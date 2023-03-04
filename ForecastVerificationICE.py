"""
Name: Test_Fcst_Verification                                                          
Created on: 02/19/23                                                             
Created By: Kayla Tinker
"""
# To run: "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" 
# C:\Python27\ArcGIS10.6\'scriptname'


import os
import arcpy
import datetime
import zipfile
import shutil

### Track changes here for testing
output_file = "U:/FcstVerification_TextFile.txt"

arcpy.env.workspace = r"U:\My Documents\ArcGIS\Default1.gdb"
arcpy.env.overwriteOutput = 1

### Only run on Sunday, Tuesday, or Thursday when we have already out from 
### the day before an analysis to use as 'ground truth'. 
### Because our forecasts are valid on Saturday, Monday and Wednesday
now = datetime.datetime.now()
weekday = now.weekday()
test_variable = ""


#if weekday == 6 or weekday == 1 or weekday == 3:
### For testing purposes
if weekday < 7:
    test_variable = "Today is a Sunday, Tuesday, or Thursday"
    ###
    ### Pull in analysis from day prior
    ###
    analysis_input = "I:\SIPAS\ARCHIVE\Ice_Archive_Zipped"
    ### Yesterday's date & 6 days ago date 
    today = datetime.datetime.today()
    
    yesterday = today - datetime.timedelta(days=1)
    yesterday_string = yesterday.strftime("%y%m%d")
    ct_string = "ct_" + yesterday_string
    
    sixDaysAgo = today - datetime.timedelta(days=6)
    sixDaysAgo_string = sixDaysAgo.strftime("%y%m%d")
    forecast_string = "forecast_" + sixDaysAgo_string
    forecastshp_string = "iceForcastTEMP_" + sixDaysAgo_string
    
    
    ### Working with the zip file 
    
    ### 1. Filter out CT == 00 (Ice free) in Analysis
    with zipfile.ZipFile(os.path.join(analysis_input, (ct_string + ".zip")),'r') as myzip:
        # Create a dummy folder to extract, that will be deleted...hmm it is empty?
        temp_folder = "U:\\temporary"
        #os.mkdir(temp_folder)
        myzip.extractall(temp_folder)
        outFeatureClass_Analysis_Dissolve = "Verification_Analysis_Filter"      
        definition_query = "CT <> '00'"
        arcpy.MakeFeatureLayer_management(os.path.join(temp_folder, (ct_string + ".shp")), "Shapefile_lyr")
        arcpy.SelectLayerByAttribute_management("Shapefile_lyr", "NEW_SELECTION", definition_query)
        arcpy.CopyFeatures_management("Shapefile_lyr", outFeatureClass_Analysis_Dissolve)
        
    ### 2. Filter out Type == ice free(Ice free) in forecast
    with zipfile.ZipFile(os.path.join(analysis_input, (forecast_string + ".zip")),'r') as myzip:
        myzip.extractall(temp_folder)
        outFeatureClass_Forecast_Dissolve = "Verification_Forecast_Filter"      
        definition_query = "Type <> 'Ice Free'"
        arcpy.MakeFeatureLayer_management(os.path.join(temp_folder, (forecastshp_string + ".shp")), "Shapefile1_lyr")
        arcpy.SelectLayerByAttribute_management("Shapefile1_lyr", "NEW_SELECTION", definition_query)
        arcpy.CopyFeatures_management("Shapefile1_lyr", outFeatureClass_Forecast_Dissolve)
    
    #shutil.rmtree(temp_folder)
    ### 3. Intersect - Find where the analysis + forecast overlap i.e. where did we get it right
    outFeatureClass_Overlap = "Verification_Overlap"
    arcpy.Intersect_analysis([outFeatureClass_Analysis_Dissolve, outFeatureClass_Forecast_Dissolve], outFeatureClass_Overlap)
    
    ### 4. Sum shape area of #1 & #2 and write to text file
    outTable_AnalysisAreaSum = "Analysis_Area_Sum"
    outTable_ForecastAreaSum = "Forecast_Area_Sum"
    outTable_OverlapAreaSum = "Overlap_Area_Sum"
    
    arcpy.analysis.Statistics(outFeatureClass_Analysis_Dissolve, outTable_AnalysisAreaSum, [["Shape_Area", "SUM"]]) 
    arcpy.analysis.Statistics(outFeatureClass_Forecast_Dissolve, outTable_ForecastAreaSum, [["Shape_Area", "SUM"]]) 
    arcpy.analysis.Statistics(outFeatureClass_Overlap, outTable_OverlapAreaSum, [["Shape_Area", "SUM"]]) 
    
    sum_table_analysis = arcpy.da.TableToNumPyArray(outTable_AnalysisAreaSum, "SUM_Shape_Area")
    sum_table_forecast = arcpy.da.TableToNumPyArray(outTable_ForecastAreaSum, "SUM_Shape_Area")
    sum_table_overlap = arcpy.da.TableToNumPyArray(outTable_OverlapAreaSum, "SUM_Shape_Area")
        
    # Trying to figure out units
    # arcpy.stats.CalculateAreas(outFeatureClass_Analysis_Dissolve, outTable_AnalysisAreaSum)
     
    ### Write to text file for testing
    with open(output_file, "w") as f:
        f.write(test_variable + os.linesep)
        f.write(yesterday_string + os.linesep)
        f.write("units are square meters and do not match with the projection used in AGOL" + os.linesep)
        f.write("Total Area of the analysis: " + str(sum_table_analysis[0][0]) + os.linesep)
        f.write("Total Area of the Forecast: " + str(sum_table_forecast[0][0]) + os.linesep)
        f.write("Overlapped area is: " + str(sum_table_overlap[0][0]))
        f.write("Over Forecasted by:" + str(sum_table_forecast[0][0] - sum_table_overlap[0][0]))


else:
    test_variable = "Today is NOT a Sunday, Tuesday, or Thursday"
    with open(output_file, "w") as f:
        f.write(test_variable)
