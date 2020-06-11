#!/usr/bin/env python

"""PublishLayersAsMIL.py: shares a list of layers as a map image layer to portal."""

import arcpy, json
from urllib.request import urlopen
from urllib.parse import urlencode
import xml.dom.minidom as DOM

__author__ = "Shilpi Jain"
__copyright__ = "Esri"
__credits__ = ["Shilpi Jain"]
__license__ = ""
__version__ = ""
__maintainer__ = ""
__email__ = "sjain at esri.com"
__status__ = "Production"


# Function to enable extensions
def enable_extensions(sddraftPath, soe):
    # Read the sddraft xml.
    doc = DOM.parse(sddraftPath)

    # Find all elements named TypeName. This is where the server object extension
    # (SOE) names are defined.
    typeNames = doc.getElementsByTagName('TypeName')
    for typeName in typeNames:
        # Get the TypeName we want to enable.
        if typeName.firstChild.data == soe:
            extension = typeName.parentNode
            for extElement in extension.childNodes:
                # Enable Feature Access.
                if extElement.tagName == 'Enabled':
                    extElement.firstChild.data = 'true'

    # Write to sddraft.
    f = open(sddraftPath, 'w')
    doc.writexml(f)
    f.close()


# Function to configure properties of an extension
# soe = extension for which properties have to be added
def enable_configproperties(sddraftPath, soe, property_set):
    # Read the sddraft xml.
    doc = DOM.parse(sddraftPath)

    # Find all elements named TypeName. This is where the server object extension
    # (SOE) names are defined.
    typeNames = doc.getElementsByTagName('TypeName')
    for typeName in typeNames:
        # Get the TypeName we want to enable.
        if typeName.firstChild.data == soe:
            extension = typeName.parentNode
            # prp = extension.childNodes.getElementsByTagNameNS('PropertyArray')
            for extElement in extension.childNodes:
                if extElement.tagName == 'Definition':
                    for definition in extElement.childNodes:
                        if definition.tagName == 'ConfigurationProperties':
                            for config_prop in definition.childNodes:
                                if config_prop.tagName == 'PropertyArray':
                                    for prop in property_set:
                                        prop_set = doc.createElement("PropertySetProperty")
                                        attr = doc.createAttribute("xsi:type")
                                        attr.value = "typens:PropertySetProperty"
                                        prop_set.setAttributeNode(attr)

                                        prop_key = doc.createElement("Key")
                                        txt = doc.createTextNode(prop["key"])
                                        prop_key.appendChild(txt)
                                        prop_set.appendChild(prop_key)

                                        prop_value = doc.createElement("Value")
                                        attr = doc.createAttribute("xsi:type")
                                        attr.value = "xs:string"
                                        prop_value.setAttributeNode(attr)
                                        txt = doc.createTextNode(prop["value"])
                                        prop_value.appendChild(txt)
                                        prop_set.appendChild(prop_value)

                                        config_prop.appendChild(prop_set)

    # Write to sddraft
    f = open(sddraftPath, 'w')
    doc.writexml(f)
    f.close()


if __name__ == "__main__":
    # region prepare
    # list the paths for the input aprx, output sddraft and sd files in variables
    aprxPath = r"C:\path2APRX\states\states.aprx"
    serviceName = 'USStates_UC2020'
    sddraftPath = r"C:\path2APRX\PublishingSamples\Output\%s.sddraft" % (serviceName)
    sdPath = r"C:\path2APRX\PublishingSamples\Output\%s.sd" % (serviceName)

    # list the AGO or enterprise url and credentials here
    portalURL = r'https://sjain.esri.com/portal'
    fed_server = r'https://sjain.esri.com/server'
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
    # lyrs=[]
    # lyrs.append(m.listLayers('States')[0])
    # endregion

    # region publish
    ''' The first step to automate the publishing of a map, layer, or list of layers to a hosted web layer using ArcPy, in new object-oriented approach.
       
       Use "getWebLayerSharingDraft" method to create a MapImageSharingDraft object (reference: http://pro.arcgis.com/en/pro-app/arcpy/sharing/mapimagesharingdraft-class.htm)
       Syntax = getWebLayerSharingDraft (server_type, service_type, service_name, {map or layers}, {...})
       
       Then to a Service Definition Draft (.sddraft) file with "exportToSDDraft" method.
       Syntax = exportToSDDraft (out_sddraft)
    '''
    # Create MapImageSharingDraft and set service properties
    sharing_draft = m.getWebLayerSharingDraft("FEDERATED_SERVER", "MAP_IMAGE", serviceName) # Creates a MapImageSharingdraft class object
    sharing_draft.federatedServerUrl = fed_server
    sharing_draft.portalFolder = 'sj'
    sharing_draft.copyDataToServer = False  # Need to register db first if set to False
    sharing_draft.summary = "My Summary"
    sharing_draft.tags = "My Tags"
    sharing_draft.description = "My Description"
    sharing_draft.credits = "My Credits"
    sharing_draft.useLimitations = "My Use Limitations"
    sharing_draft.exportToSDDraft(sddraftPath) # Need to crack open the sddraft to enable FS
    print("Exported SDDraft")

    '''Once sddraft is created, it can be modified to set various properties 
       We are going to turn on feature access and set timezone to UTC
    '''
    # Set timezone
    property_set = [{
        "key": "dateFieldsRespectsDayLightSavingTime",
        "value": "true"
    },
        {
            "key": "dateFieldsTimezoneID",
            "value": "UTC"
        }]
    # To set time zone on hosted feature service, soe = "FeatureServer"
    enable_configproperties(sddraftPath, soe="MapServer", property_set=property_set)

    # Enable extensions on map server
    enable_extensions(sddraftPath, "FeatureServer")
    # enable_extensions(sddraftPath, "VersionManagementServer")
    # enable_extensions(sddraftPath, "LRServer")

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
    arcpy.UploadServiceDefinition_server(sdPath, fed_server)
    print("Uploaded and Shared SD")
    # endregion
    print("END")
    # end
