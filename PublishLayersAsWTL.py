#!/usr/bin/env python

"""PublishLayersAsWTL.py: shares a list of layers as a web tiled layer to AGO."""

import arcpy, json
from urllib.request import urlopen
from urllib.parse import urlencode

__author__ = "Shilpi Jain"
__copyright__ = "Copyright 2018, Esri"
__credits__ = ["Shilpi Jain"]
__license__ = ""
__version__ = ""
__maintainer__ = ""
__email__ = "sjain at esri.com"
__status__ = "Production"

# list the paths for the input aprx, output sddraft and sd files in variables
aprxPath = r"C:\path2APRX\states\states.aprx"
serviceName = 'MajorCitites_UC2019'
sddraftPath = r"C:\path2APRX\PublishingSamples\Output\%s.sddraft" % (serviceName)
sdPath = r"C:\path2APRX\PublishingSamples\Output\%s.sd" % (serviceName)
observedTileFile = r'Output\observed_' + serviceName + '_tiles.png'

# list the AGO or enterprise url and credentials here
portalURL = r'https://www.arcgis.com'
cred_detail = []
with open("secure/AGO_pass.txt") as f:
        for line in f:
            cred_detail.append(line.splitlines())
username = cred_detail[0][0]
password = cred_detail[1][0]

# Sign into AGO and set as active portal
arcpy.SignInToPortal(portalURL, username, password)

# Maintain a reference of an ArcGISProject object pointing to your project
aprx = arcpy.mp.ArcGISProject(aprxPath)

# Maintain a reference of a Map object pointing to your desired map
m = aprx.listMaps('Cities')[0]

# create a list of layers which contains the 2nd and 3rd layers of the map
lyrs=[]
lyrs.append(m.listLayers('Major Cities')[0])

''' the first step to automate the publishing of a map, layer, or list of layers to a hosted web layer using ArcPy, in new object-oriented approach.
   
   Use "getWebLayerSharingDraft" method to create a TileSharingDraft object (reference: http://pro.arcgis.com/en/pro-app/arcpy/sharing/tilesharingdraft-class.htm)
   Syntax = getWebLayerSharingDraft (server_type, service_type, service_name, {map or layers}, {...})
   
   Then to a Service Definition Draft (.sddraft) file with "exportToSDDraft" method.
   Syntax = exportToSDDraft (out_sddraft)
'''
# Create TileSharingDraft and set service properties
sharing_draft = m.getWebLayerSharingDraft("HOSTING_SERVER", "TILE", serviceName, lyrs)
sharing_draft.portalUrl = portalURL
sharing_draft.summary = "My Summary"
sharing_draft.tags = "My Tags"
sharing_draft.description = "My Description"
sharing_draft.credits = "My Credits"
sharing_draft.useLimitations = "My Use Limitations"
sharing_draft.exportToSDDraft(sddraftPath)
print("Exported SDDraft")

''' The Service Definition Draft can then be converted to a fully consolidated Service Definition (.sd) file using the Stage Service tool.
    Staging compiles all the necessary information needed to successfully publish the GIS resource.
    Syntax = StageService_server (in_service_definition_draft, out_service_definition, staging_version)
'''
arcpy.StageService_server(sddraftPath, sdPath)
print("Created SD")

'''  Finally, the Service Definition file can be uploaded and published as a GIS service to a specified online organization using the Upload Service Definition tool.
    This step takes the Service Definition file, copies it onto the server, extracts required information, and publishes the GIS resource.
    Syntax = UploadServiceDefinition_server (in_sd_file, in_server, {in_service_name}, {in_cluster}, {in_folder_type},
                                                                        {in_folder}, {in_startupType}, {in_override}, {in_my_contents}, {in_public}, {in_organization}, {in_groups})
'''
arcpy.UploadServiceDefinition_server(sdPath, 'My Hosted Services', in_override = "OVERRIDE_DEFINITION", in_public = "PUBLIC", in_organization = "SHARE_ORGANIZATION")
print("Uploaded and Shared SD")

# Creates and updates tiles in an existing web tile layer cache. 
input_service = r'https://tiles.arcgis.com/tiles/<orgID>/arcgis/rest/services/' + serviceName + r'/MapServer'
arcpy.ManageMapServerCacheTiles_server(input_service, [295828763.79577702], "RECREATE_ALL_TILES")
print("Created Tiles")

''' Getting the token
'''
token_url = 'https://www.arcgis.com/sharing/generateToken'
referer = "http://services.arcgis.com"
query_dict1 = {  'username':   username,
                 'password':   password,
                 'expiration': str(1440),
                 'client':     'referer',
                 'referer': referer}
query_string = urlencode(query_dict1)
tokenStr = json.loads(urlopen(token_url + "?f=json", str.encode(query_string)).read().decode('utf-8'))['token']

'''  Validation - Save the tile image to local disk
'''
print("Validating")
tile_url = "https://tiles.arcgis.com/tiles/<orgID>/arcgis/rest/services/%s/MapServer/tile/1/0/0?cacheKey=92d45a007db841cd&token=" % (serviceName)
f = open(observedTileFile,'wb')
data = urlopen(tile_url + tokenStr).read()
f.write(data)
f.close()
print("END")
# end
