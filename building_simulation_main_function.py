# -*- coding: utf-8 -*-
"""
Created on Thu Jul 20 13:55:24 2017

@author: ghlt
"""

import pandas as pd
import argparse, os, time
import building_simulation as bs
from datetime import datetime, timedelta
import boto3
import json
import decimal


# parse for possible arguments
def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-path", default = "dummy")
    parser.add_argument("-input", default = "dummy")
    args = parser.parse_args()
    return args


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


# get target room temperature from local file or from dynamodb
def get_target_temperature(strMode, objTable, strKey, strColumn, intOldTemp):
    if strMode == "local_file":
        strFile = r"roomtemperature.csv"
        dfTarget = pd.read_csv(strFile, sep=";")
        return dfTarget["target_temperature"].iloc[0]
    if strMode == "dynamodb":
        try:
            dictResponse = objTable.get_item(Key={'userId': strKey})
            return int(dictResponse['Item'][strColumn])
        except:
            return intOldTemp


if __name__ == "__main__":
    #_____________________________Get Arguments________________________________
    args = get_arguments()
    if args.path != "dummy":
        os.chdir(args.path)
    if args.input != "dummy":
        strInputFile = args.input
    else:
        strInputFile = "InputData.csv"
    
    # read weather data from csv-file
    dfInput = pd.read_csv(strInputFile, sep=";")
    intMaxIndex = len(dfInput)
    
    #_____________________________Set Parameter________________________________
    # use local csv-file as source of target room temperature
    strMode = "local_file"
    # use dynamodb as source of target room temperature (e.g. with Alexa)
    #strMode = "dynamodb"
    
    dtTimestamp = datetime(2017,1,1) # start timestamp
    fltTimeStep = 0.083         # 5 Minute Steps for calculation
    fltSleepTime = 1            # Sleeptime in seconds (for looping)
    fltIndoorTemp = 18          # 19 degrees celsius at beginning
    fltIsolation = 0.8          # 80% isolation
    fltRoomVolume = 160         # 160 cubic meters room
    fltCapacity = 19            # 19 kW boiler
    fltPVEfficiency = 0.14      # 14% efficient photovoltaics-device
    fltPVSize = 50              # 50 square meters photovoltaics-device
    fltWaterTemp = 25           # 25 degrees water temperature at the beginning
    fltColdWaterTemp = 10       # 10 degrees celsius fresh water temperature
    fltStorageVolume = 200      # 200 liters warm water storage
    fltTargetWaterTemp = 50     # 50 degrees
    
    fltEnergyConsumption = 0    # Start energy consumption counter
    fltTargetRoomTemp = 18      # Start Target Room Temperature
    
    #_____________________Connect to DynamoDB or local file____________________
    if strMode == "dynamodb":
        dfTableInfos = pd.read_csv("DynamoDB_table_infos.csv", sep=";", index_col=0)
        dynamodb = boto3.resource("dynamodb", region_name=dfTableInfos["region"].loc["target_room_temp"])
        objTableTRT = dynamodb.Table(dfTableInfos["table"].loc["target_room_temp"])
    else:
        dfTableInfos = pd.DataFrame([[0,0]], columns=["key","column"])
        dfTableInfos.index = ["target_room_temp"]
        objTableTRT = None
    
    #______________________________Start Loop__________________________________
    h = -1
    while True:
        h += 1
        # return to first row if end of dataframe is reached
        if h >= intMaxIndex:
            h = 0
        
        # get current target room temperature every 5th loop
        if h % 5 == 0:
            fltTargetRoomTemp = get_target_temperature(strMode, 
                                                       objTableTRT,
                                                       dfTableInfos["key"].loc["target_room_temp"],
                                                       dfTableInfos["column"].loc["target_room_temp"],
                                                       fltTargetRoomTemp)
        
        # timestamp only used for printing
        dtTimestamp += timedelta(hours = fltTimeStep)
        
        # get input data from dataframe
        fltOutdoorTemp = dfInput["outdoor_temperature"].iloc[h]
        fltSolarRadiation = dfInput["solar_radiation"].iloc[h]
        intWaterUsage = dfInput["use_water"].iloc[h]
        
        # calculate cooling of water by room temperature
        fltWaterTemp += bs.water_storage_cooling(fltWaterTemp, 
                                                 fltColdWaterTemp, 
                                                 fltStorageVolume, 
                                                 fltTimeStep)
        # calculate cooling of the room by outdoor temperature
        fltIndoorTemp += bs.room_cooling(fltOutdoorTemp, 
                                         fltIndoorTemp, 
                                         fltTimeStep, 
                                         fltIsolation)
        # calculate needed energy for heating and new temperature of the room
        fltECH, fltIndoorTemp = bs.room_heating(fltIndoorTemp, 
                                                fltTargetRoomTemp, 
                                                fltTimeStep, 
                                                fltRoomVolume, 
                                                fltCapacity)
        # calculate cooling of water storage by usage of warm water
        fltWaterTemp += bs.water_cooling_by_usage(fltWaterTemp, 
                                                  fltColdWaterTemp, 
                                                  intWaterUsage, 
                                                  fltTimeStep)
        # calculate needed heating energy and temperature of water storage
        fltECW, fltWaterTemp = bs.water_heating(fltWaterTemp, 
                                                fltTargetWaterTemp, 
                                                fltTimeStep, 
                                                fltStorageVolume, 
                                                fltCapacity)
        # calculate solar energy by solar radiation
        fltSE = bs.get_solar_energy(fltSolarRadiation, 
                                    fltPVEfficiency, 
                                    fltPVSize, 
                                    fltTimeStep)
        
        # calculate energy of current loop and set it to zero if more energy
        # was produced than consumed
        fltCEC = fltECH + fltECW - fltSE
        if fltCEC < 0:
            fltCEC = 0
        
        # accumulate energy consumption
        fltEnergyConsumption += fltCEC
        
        # print results of current loop
        print("==============================================================")
        print("Datetime: " + dtTimestamp.strftime("%Y-%m-%d %H:%M"))
        print("Outdoor-Temp: " + format(fltOutdoorTemp, '.2f') + " °C")
        print("Solar-Radiation: " + format(fltSolarRadiation, '.2f') + " kW / m²")
        print("Water-Usage: " + str(intWaterUsage))
        print()
        print("Room-Temp: " + format(fltIndoorTemp, '.2f') + " °C")
        print("Water-Temp: " + format(fltWaterTemp, '.2f') + " °C")
        print()
        print("Heat-Energy: " + format(fltECH, '.3f') + " kWh")
        print("Water-Energy: " + format(fltECW, '.3f') + " kWh")
        print("Solar-Energy: " + format(fltSE, '.3f') + " kWh")
        print()
        print("Energy-Consumption: " + format(fltEnergyConsumption, '.3f') + " kWh")
        
        
        # wait for next loop
        time.sleep(fltSleepTime)