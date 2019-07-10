#!/usr/bin/env python

"""PublishLayersAsMIL.py: shares a list of layers as a map image layer to portal."""

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

#region prepare
# list the paths for the input aprx, output sddraft and sd files in variables
aprxPath = r"C:\path2APRX\states\states.aprx"
serviceName = 'USStates_UC2019_1'
sddraftPath = r"C:\path2APRX\PublishingSamples\Output\%s.sddraft" % (serviceName)
sdPath = r"C:\path2APRX\PublishingSamples\Output\%s.sd" % (serviceName)
observedTileFile = r'Output\observed_' + serviceName + '_exportWholeMap.png'

# list the AGO or enterprise url and credentials here
portalURL = r'https://sjain.esri.com/portal'
svrTiles = r'https://sjain.esri.com/server'
cred_detail = []
with open("secure/Enterprise_pass.txt") as f:
        for line in f:
            cred_detail.append(line.splitlines())
username = cred_detail[0][0]
password = cred_detail[1][0]

# Sign into AGO and set as active portal
arcpy.SignInToPortal(portalURL, username, password)

# Maintain a reference of an ArcGISProject object pointing to your project
aprx = arcpy.mp.ArcGISProject(aprxPath)

# Maintain a reference of a Map object pointing to your desired map
m = aprx.listMaps('States')[0]

# create a list of layers which contains the 2nd and 3rd layers of the map
#lyrs=[]
#lyrs.append(m.listLayers('States')[0])
#endregion

#region publish
''' the first step to automate the publishing of a map, layer, or list of layers to a hosted web layer using ArcPy, in new object-oriented approach.
   
   Use "getWebLayerSharingDraft" method to create a MapImageSharingDraft object (reference: http://pro.arcgis.com/en/pro-app/arcpy/sharing/mapimagesharingdraft-class.htm)
   Syntax = getWebLayerSharingDraft (server_type, service_type, service_name, {map or layers}, {...})
   
   Then to a Service Definition Draft (.sddraft) file with "exportToSDDraft" method.
   Syntax = exportToSDDraft (out_sddraft)
'''
# Create MapImageSharingDraft and set service properties
sharing_draft = m.getWebLayerSharingDraft("FEDERATED_SERVER", "MAP_IMAGE", serviceName) # Creates a MapImageSharingdraft class object
sharing_draft.federatedServerUrl = svrTiles
sharing_draft.portalFolder = 'sj'
sharing_draft.copyDataToServer = True # Need to register db first if set to False
sharing_draft.summary = "My Summary"
sharing_draft.tags = "My Tags"
sharing_draft.description = "My Description"
sharing_draft.credits = "My Credits"
sharing_draft.useLimitations = "My Use Limitations"
sharing_draft.exportToSDDraft(sddraftPath) # Need to crack open the sddraft to enable FS
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
arcpy.UploadServiceDefinition_server(sdPath, svrTiles)
print("Uploaded and Shared SD")
#endregion

#region validation
# Creates and updates tiles in an existing web tile layer cache. 
input_service = svrTiles + r'/rest/services/' + serviceName + r'/MapServer'
print("Map Image published successfully - " + input_service)

''' Getting the token
'''
token_url = portalURL + r'/sharing/rest/generateToken'
referer = svrTiles + r'/rest/services'
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
tile_url = svrTiles + r'/rest/services/' + serviceName + r"/MapServer/export?bbox=-174.0241598064554,-1.4747596064937696,-52.02447994654452,86.03698128749386&format=png&transparent=false&f=image&token="
f = open(observedTileFile,'wb')
data = urlopen(tile_url + tokenStr).read()
# print("Exported map from " + tile_url + tokenStr + " to " + observedTileFile)
f.write(data)
f.close()
#endregion
print("END")
# end
