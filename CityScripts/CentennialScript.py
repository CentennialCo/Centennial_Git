#-------------------------------------------------------------------------------
# Name:  City of Centennial Parcel Data Update
# Purpose:  Energov Parcels
#
# Author:      Max Marno
# North Line GIS LLC.
# Created:     20/12/2017
#-------------------------------------------------------------------------------
import os
import sys
import arcpy
import string
import calendar, datetime, traceback
from arcpy import env
from mailer import Mailer
from mailer import Message
'''
WORKSPACE AND ENVIRONMENT SETUP:
'''
#THIS WILL DETERMINE WHERE THE OUTPUT LOG IS WRITTEN
backupTime = time.strftime("%Y_%m_%d_%H%M")

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))
file_path = get_script_path()
# REPLACE 'file_path' WITH DESIRED DIRECTORY FOR OUTPUT LOG IF DIFFERENT FROM SCRIPT LOCATION
os.chdir(file_path)
arcpy.env.overwriteOutput = True
GDBpath = "X:\\GIS\\EnerGov\\SourceData.gdb"
#GDBpath = "D:\\Projects\\Centennial\\CentennialModel\\Source_Data\\Centennial.gdb"
arcpy.env.scratchWorkspace = GDBpath
arcpy.env.workspace = GDBpath
# FINAL PARCEL OUTPUT NAME:
FinalOutputName = "ParcelFinal"
BackupParcel = "X:\\GIS\\EnerGov\\Backup.gdb\\Backup_" + str(backupTime)
################################################################################
try:
    '''
    LOG START TIME
    '''
    d = datetime.datetime.now()
    os.chdir("X:\\GIS\\EnerGov")
    log = open("PythonOutputLogFile.txt","a")
    log.write("----------------------------" + "\n")
    log.write("----------------------------" + "\n")
    log.write("Log: " + str(d) + "\n")
    log.write("\n")
    # Start process...
    starttime = datetime.datetime.now()
    log.write("Begin process:\n")
    log.write("     Process started at "+ str(starttime) + "\n")
    log.write("\n")
    print "Started at " + str(d)
    '''
    INPUT:
    '''
    parcel = os.path.join(GDBpath, "Parcel")
    water = os.path.join(GDBpath, "Water")
    stormwater = os.path.join(GDBpath, "Stormwater")
    school = os.path.join(GDBpath, "School")
    rtd = os.path.join(GDBpath, "RTD")
    recreation = os.path.join(GDBpath, "Recreation")
    improvement = os.path.join(GDBpath, "Improvement")
    fire = os.path.join(GDBpath, "Fire")
    #e470 = os.path.join(GDBpath, "E470")
    zoning = os.path.join(GDBpath, "Zoning")
    subdivisions = os.path.join(GDBpath, "Subdivisions")
    landusecurrent = os.path.join(GDBpath, "LandUse_Current")
    landusefuture = os.path.join(GDBpath, "Future_Land_Use_Unapproved")
    sanitation = os.path.join(GDBpath, "Sanitation")
    councildistricts = os.path.join(GDBpath, "Council_Districts")
    aia = os.path.join(GDBpath, "AIA")
    metrodistrict = os.path.join(GDBpath, "Metro_District")
    hoas = os.path.join(GDBpath, "HOAs")
    ardcorridor = os.path.join(GDBpath, "ArapahoeRdCorridor")
    rtif = os.path.join(GDBpath, "RTIF")
    acirea = os.path.join(GDBpath, "acirea")
    acxcel = os.path.join(GDBpath, "acxcel")
    ccbwqa = os.path.join(GDBpath, "ccbwqa")
    semswaURL = "https://maps.semswa.org/arcgis/rest/services/DrainageFP/SMSA_Drainage_Floodplain2/FeatureServer/2/query"
    # NO INPUT NEEDED BEYOND HERE
    '''
    LOAD SEMSWA FLOOD SERVICE
    '''
    ################################################################################
    baseURL= semswaURL
    where = '1=1'
    fields ='objectid, src_layer, zone_subty, fld_zone'
    token = ''
    #The above variables construct the query
    query = "?where={}&outFields={}&returnGeometry=true&f=json&token={}".format(where, fields, token)
    # See http://services1.arcgis.com/help/index.html?fsQuery.html for more info on FS-Query
    fsURL = baseURL + query
    fs = arcpy.FeatureSet()
    fs.load(fsURL)
    arcpy.CopyFeatures_management(fs, "SEMSWA")
    semswa = os.path.join(GDBpath, "SEMSWA")
    ################################################################################
    '''
    DEFINE FUNCTIONS:
    '''
    ################################################################################
    # SPATIAL JOINS:
    def SpJn(targfeats, joinfeats, outputname, joinfieldname, targetfieldname):
        fieldmappings = arcpy.FieldMappings()
        # Add all fields from inputs.
        fieldmappings.addTable(targfeats)
        fieldmappings.addTable(joinfeats)
        # PARCEL FIELDS (ONES TO KEEP)
        Kfields = [f.name for f in arcpy.ListFields(targfeats)]
        #keepers = ["want_this_field", "this_too", "and_this"] # etc.
        # REMOVE ALL FIELDS IN WATER TABLE FROM FIELD MAPPINGS OBJECT
        for field in fieldmappings.fields:
            if field.name not in Kfields:
                fieldmappings.removeFieldMap(fieldmappings.findFieldMapIndex(field.name))
        # NEW FIELD MAP THAT IS THE DESIRED FIELD FROM JOIN TABLE
        fmap = arcpy.FieldMap()
        # PARAMS FOR INPUT FIELD ARE TABLE(FC), AND FIELD NAME
        fmap.addInputField(joinfeats, joinfieldname)
        # RENAME TO MATCH EXISTING FIELD
        fmap_name = fmap.outputField
        fmap_name.name = targetfieldname
        fmap.outputField = fmap_name
        # REPLACE EXISTING FIELD MAP, WITH NEW ONE FROM SPATIAL JOIN FEATURES
        fieldmappings.replaceFieldMap(fieldmappings.findFieldMapIndex(targetfieldname), fmap)
        arcpy.SpatialJoin_analysis(target_features=targfeats, join_features=joinfeats, out_feature_class=outputname, field_mapping=fieldmappings, match_option="HAVE_THEIR_CENTER_IN")
        # DELETE JOIN_COUNT AND TARGET FIELDS
        # FIRST 'TARGET' FIELDS
        tfields = [f.name for f in arcpy.ListFields(outputname)]
        tfields = [x for x in tfields if "TARGET" in x]
        if len(tfields)>0:
            arcpy.DeleteField_management(outputname, tfields)
        # NOW JOIN_COUNT FIELDS
        jcfields = [f.name for f in arcpy.ListFields(outputname)]
        jcfields = [x for x in jcfields if "Join_Count" in x]
        if len(jcfields)>0:
            arcpy.DeleteField_management(outputname, jcfields)
        # NOW OBJECT ID FIELDS
        ofields = [f.name for f in arcpy.ListFields(outputname)]
        ofields = [x for x in ofields if "OBJECTID_1" in x]
        if len(ofields)>0:
            arcpy.DeleteField_management(outputname, ofields)

        print outputname + " Spatial Join Complete"

    # ADD NECESSARY FIELDS IF MISSING
    def addfield(intable, inname, intype):
        checkfields = arcpy.ListFields(intable)
        DISTFIELD=0
        for field in checkfields:
            if field.name == inname:
                DISTFIELD+=1
        if DISTFIELD <1:
            arcpy.AddField_management(intable, inname, intype)
        print inname +" Add Field Complete"

    # DELETE FIELDS AUTOMATICALLY ADDED IN SPATIAL JOINS
    def deljoinfields (inputtable):
        # FIRST 'TARGET' FIELDS
        field_list = [f.name for f in arcpy.ListFields(inputtable)]
        field_list = [x for x in field_list if "TARGET" in x]
        arcpy.DeleteField_management(inputtable, field_list)
        # NOW JOIN_COUNT FIELDS
        field_list = [f.name for f in arcpy.ListFields(inputtable)]
        field_list = [x for x in field_list if "Join_Count" in x]
        arcpy.DeleteField_management(inputtable, field_list)

    # USE SELECT BY LOCATION AND FIELD CACLULATOR TO POPULATE FIELDS:
    def calcselect(inputtable, selfeatures, calcfield, calcvalue, overlap):
        # ! CALCVALUE MUST BE WRAPPED IN SINGLE QUOTES, IE  '"Yes"'   !!!!
        arcpy.MakeFeatureLayer_management(inputtable, "temp_lyr")
        arcpy.management.SelectLayerByLocation("temp_lyr", overlap, selfeatures, None, "NEW_SELECTION", "NOT_INVERT")
        arcpy.CalculateField_management("temp_lyr", calcfield, calcvalue, "PYTHON_9.3", None)
        arcpy.SelectLayerByAttribute_management("temp_lyr", "CLEAR_SELECTION")
        arcpy.CopyFeatures_management("temp_lyr", "temp_fc")
        arcpy.CopyFeatures_management("temp_fc", inputtable)
        arcpy.DeleteFeatures_management("temp_fc")
        print selfeatures + " Calculated @ " + str(d)
    ################################################################################
    '''
    PRE PROCESSING: ADD FIELDS
    '''
    addfield(parcel, "CurrentLandUse", "TEXT")
    addfield(parcel, "FutureLandUse", "TEXT")
    addfield(parcel, "AIA", "TEXT")
    addfield(parcel, "ArapahoeRdCorridor", "TEXT")
    addfield(parcel, "RTIF", "TEXT")
    addfield(parcel, "CCBWQA", "TEXT")
    addfield(parcel, "SEMSWA", "TEXT")
    """<Added Fields For Arapahoe Parcels"""
    addfield(parcel, "POWER", "TEXT")
    #addfield(parcel, "E470", "TEXT")
    addfield(parcel, "FIRE", "TEXT")
    addfield(parcel, "IMPROVEMENT", "TEXT")
    addfield(parcel, "METRO", "TEXT")
    addfield(parcel, "POWER", "TEXT")
    addfield(parcel, "RECREATION", "TEXT")
    addfield(parcel, "RTD", "TEXT")
    addfield(parcel, "SANITATION", "TEXT")
    addfield(parcel, "SCHOOL", "TEXT")
    addfield(parcel, "STORMWATER", "TEXT")
    addfield(parcel, "WATER", "TEXT")
    addfield(parcel, "WATER_AND_SANITATION", "TEXT")
    addfield(parcel, "HOA_Name", "TEXT")
    addfield(parcel, "HOA_ID", "TEXT")
    addfield(parcel, "ZONECLASS", "TEXT")
    addfield(parcel, "ZONEDESC", "TEXT")
    addfield(parcel, "Subdivision", "TEXT")
    addfield(parcel, "Cent_Council_District", "TEXT")
    addfield(parcel, "LANDUSEDES", "TEXT")
    addfield(parcel, "FutureLandUse", "TEXT")
    """End Add Area >"""

    '''
    SELECT BY LOCATION AND CALCULATE FIELDS
    '''
    calcselect(parcel, aia, "AIA", '"Yes"', "HAVE_THEIR_CENTER_IN")
    #calcselect(parcel, e470, "E470", '"Yes"', "HAVE_THEIR_CENTER_IN")
    calcselect(parcel, ardcorridor, "ArapahoeRdCorridor", '"Yes"', "HAVE_THEIR_CENTER_IN")
    calcselect(parcel, rtif, "RTIF", '"Yes"', "HAVE_THEIR_CENTER_IN")
    calcselect(parcel, acirea, "Power", '"IREA"', "HAVE_THEIR_CENTER_IN")
    calcselect(parcel, acxcel, "Power", '"XCEL"', "HAVE_THEIR_CENTER_IN")
    calcselect(parcel, ccbwqa, "CCBWQA", '"Yes"', "INTERSECT")
    calcselect(parcel, semswa, "SEMSWA", '"Yes"', "INTERSECT")
    '''
    SPATIAL JOINS
    '''

    # THESE MUST BE KEPT IN ORDER - RUNNING OUT OF SEQUENCE WILL BREAK THE SCRIPT!
    # JOIN WATER TO PARCEL
    SpJn(parcel, water, 'parcel_water', 'NAME', 'WATER')
    # JOIN STORMWATER TO PARCEL
    SpJn('parcel_water', stormwater, 'parcel_stormwater', 'Name', 'STORMWATER')
    arcpy.Delete_management('parcel_water')
    # JOIN SCHOOL TO PARCEL
    SpJn('parcel_stormwater', school, 'parcel_school', 'DIST_NAME', 'SCHOOL')
    arcpy.Delete_management('parcel_stormwater')
    # JOIN RTD TO PARCEL
    SpJn('parcel_school', rtd, 'parcel_rtd', 'RTDBNDTYPE', 'RTD')
    arcpy.Delete_management('parcel_school')
    # JOIN RECREATION TO PARCEL
    SpJn('parcel_rtd', recreation, 'parcel_recreation', 'DIST_NAME', 'RECREATION')
    arcpy.Delete_management('parcel_rtd')
    # JOIN IMPROVEMENT TO PARCEL
    SpJn('parcel_recreation', improvement, 'parcel_improvement', 'DISTRICTNA', 'IMPROVEMENT')
    arcpy.Delete_management('parcel_recreation')
    # JOIN FIRE TO PARCEL
    SpJn('parcel_improvement', fire, 'parcel_fire', 'NAME', 'FIRE')
    arcpy.Delete_management('parcel_improvement')
    # JOIN ZONECLASS TO PARCEL
    SpJn('parcel_fire', zoning, 'parcel_zoneclass', 'ZONECLASS', 'ZONECLASS')
    arcpy.Delete_management('parcel_fire')
    # JOIN ZONEDESC TO PARCEL
    SpJn('parcel_zoneclass', zoning, 'parcel_zonedesc', 'ZONEDESC', 'ZONEDESC')
    arcpy.Delete_management('parcel_zoneclass')
    # JOIN SUBDIVISIONS TO PARCEL
    SpJn('parcel_zonedesc', subdivisions, 'parcel_subdivisions', 'SUBDIVISIO', 'Subdivision')
    arcpy.Delete_management('parcel_zonedesc')
    # JOIN SANNITATION TO PARCEL
    SpJn('parcel_subdivisions', sanitation, 'parcel_sanitation', 'NAME', 'SANITATION')
    arcpy.Delete_management('parcel_subdivisions')
    # JOIN COUNCIL DISTRICTS TO PARCEL
    SpJn('parcel_sanitation', councildistricts, 'parcel_councildistricts', 'NAME', 'Cent_Council_District')
    arcpy.Delete_management('parcel_sanitation')
    # JOIN METRO DISTRICT TO PARCEL
    SpJn('parcel_councildistricts', metrodistrict, 'parcel_metrodistrict', 'District_N', 'METRO')
    arcpy.Delete_management('parcel_councildistricts')
    # JOIN HOA ID TO PARCEL
    SpJn('parcel_metrodistrict', hoas, 'parcel_hoaid', 'hoa_id', 'HOA_ID')
    arcpy.Delete_management('parcel_metrodistrict')
    # JOIN HOA NAME TO PARCEL
    SpJn('parcel_hoaid', hoas, 'parcel_hoaname', 'HOA_Name', 'HOA_Name')
    arcpy.Delete_management('parcel_hoaid')
    """# JOIN CITY COUNCIL TO PARCEL
    SpJn('parcel_hoaname', councildistricts, 'parcel_councildistricts', 'District', 'Cent_Council_District')
    arcpy.Delete_management('parcel_hoaname')"""
    # JOIN CURRENT LAND USE TO PARCEL
    SpJn('parcel_hoaname', landusecurrent, 'parcel_currentlanduse', 'Land_Use_T', 'LANDUSEDES')
    arcpy.Delete_management('parcel_hoaname')
    # JOIN FUTURE LAND USE TO PARCEL
    SpJn('parcel_currentlanduse', landusefuture, 'parcel_futurelanduse', 'FLU', 'FutureLandUse')
    arcpy.Delete_management('parcel_currentlanduse')


    # FINAL OUTPUT
    arcpy.CopyFeatures_management("parcel_futurelanduse", FinalOutputName)
    arcpy.Delete_management("parcel_futurelanduse")
    print "Final Output Created"
        # BACKUP THE PREVIOUS PARCELS AND DELETE AND APPEND TO SDE PARCELS
    EnerGovParcels = "Database Connections//EnerGov_GIS.sde//EnerGov_GIS.DBO.EnerGovP//Energov_Parcels_NL"
    arcpy.CopyFeatures_management(EnerGovParcels, BackupParcel)
    if int(arcpy.GetCount_management(EnerGovParcels)[0]) > 0:
        arcpy.DeleteRows_management(EnerGovParcels)
        print "TaxParcel Rows Deleted"
    print "Append Starting if zero rows are in LGIM Parcels"
    if int(arcpy.GetCount_management(EnerGovParcels)[0]) == 0:
        arcpy.Append_management(inputs="X:/GIS/EnerGov/SourceData.gdb/ParcelFinal", target="Database Connections/Energov_GIS.sde/EnerGov_GIS.DBO.EnerGovP/EnerGov_GIS.DBO.ParcelFinal", schema_type="TEST", field_mapping="", subtype="")
        print "Parcels Appeneded"

    '''
    LOG COMPLETION TIME
    '''
    endtime = datetime.datetime.now()
    # Process Completed
    log.write("     Completed successfully in "+ str(endtime - starttime) + "\n")
    log.write("\n")

    ##################################################################################
    #Send E-Mail after complete
    from mailer import Mailer
    from mailer import Message

    message = Message(From="mjones@centennialco.gov",
                      To='mjones@centennialco.gov,koyama@centennialco.gov,dstertz@centennialco.gov')
    message.Subject = "Energov Parcels Updated @ " +str(d)
    message.Html = """<p>The script ran and data has been updated!<br><br>
       The script took <b> """+ str(endtime - starttime)+"""</b> to run<br><br>
       Here is the <a href="file://X:/GIS/EnerGov/PythonOutputLogFile.txt">Link to the Log File</a> for tracking.</p>"""
    sender = Mailer('COC-EXCH01.coc.local')
    sender.send(message)
    ##################################################################################
    # Close Log
    log.close()
except:
    starttime = datetime.datetime.now()
    endtime = datetime.datetime.now()
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    # Concatenate information together concerning
    # the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
    # Return python error messages for use in
    # script tool or Python Window
    arcpy.AddError(pymsg)
    arcpy.AddError(msgs)
    # LOG AND CLOSE
    log.write("" + pymsg + "\n")
    log.write("Failed @" +str(d))
    log.close()
    message = Message(From="mjones@centennialco.gov",
                      To='mjones@centennialco.gov,koyama@centennialco.gov,dstertz@centennialco.gov')
    message.Subject = "Energov Parcels FAILED @ " +str(d)
    message.Html = """<p>The script done broke something!<br><br>
       The script took <b> """+ str(endtime - starttime)+"""</b> to run<br><br>
       Here is the <a href="file://X:/GIS/EnerGov/PythonOutputLogFile.txt">Link to the Log File</a> for tracking why it done messed up.</p>"""
    sender = Mailer('COC-EXCH01.coc.local')
    sender.send(message)
