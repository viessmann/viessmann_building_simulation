# -*- coding: utf-8 -*-
"""
Created on Wed May 31 16:10:39 2017

@author: ghlt
"""

def room_cooling(fltOutdoorTemperature, fltCurrentRoomTemperature, fltTimeStep, 
                 fltIsolation):
    """
    fltOutdoorTemperature - Average Outdoor temperature in °C
    fltCurrentRoomTemperature - Average Roomtemperature in °C
    fltTimeStep - Timestep in hours
    fltIsolation - Isolation of building as rate per hour [0 to 1]
    """
    
    fltDiff = fltOutdoorTemperature - fltCurrentRoomTemperature
    fltDiffTemperature = fltDiff * (1 - fltIsolation) * fltTimeStep
    
    if abs(fltDiffTemperature) > abs(fltDiff):
        fltDiffTemperature = fltDiff
    
    return fltDiffTemperature


def room_heating(fltCurrentRoomTemperature, fltTargetRoomTemperature, 
                 fltTimeStep, fltRoomVolume, fltCapacity):
    """
    fltCurrentRoomTemperature - Average room temperature in °C
    fltTargetRoomTemperature - Target room temperature in °C
    fltTimestep - Timestep in hours
    fltRoomVolume - Volume of room in m³
    fltCapacity - Capacity of boiler in kW [from 11 to 35]
    """
    
    fltDiff = fltTargetRoomTemperature - fltCurrentRoomTemperature
    if fltDiff < 0:
        fltDiff = 0
    
    fltSpecificHeatCapacity = 1.005 # kJ / (kg * K)
    fltAirDense = 1.2041 # kg / m³
    fltRadiatorEfficiency = 0.02
    fltCapacityKiloJoule = fltCapacity * 3600 * fltTimeStep * fltRadiatorEfficiency
    fltAirMass = fltRoomVolume * fltAirDense
    fltAddTemperature = fltCapacityKiloJoule / (fltAirMass * fltSpecificHeatCapacity)
    
    if fltAddTemperature > fltDiff:
        fltConsumption = (fltDiff / fltAddTemperature) * fltCapacity * fltTimeStep
        fltNewRoomTemperature = fltCurrentRoomTemperature + fltDiff
    else:
        fltConsumption = fltCapacity * fltTimeStep
        fltNewRoomTemperature = fltCurrentRoomTemperature + fltAddTemperature
    
    return fltConsumption, fltNewRoomTemperature


def get_solar_energy(fltSolarRadiation, fltPVEfficiency, fltPVSize, fltTimeStep):
    """
    fltSolarRadiation - Radiation in kW / m² [max: 1, avg: 0.075]
    fltPVEfficiency - Efficiency of the photovoltaik-device [from 0.1 to 0.18]
    fltPVSize - Size of the photovoltaik-device in m² [avg: 50]
    fltTimestep - Timestep in hours
    """
    
    fltSolarEnergy = fltSolarRadiation * fltPVEfficiency * fltPVSize * fltTimeStep
    return fltSolarEnergy


def water_cooling_by_usage(fltWaterTemperature, fltColdWaterTemperature, 
                           intUsage, fltTimeStep):
    """
    fltWaterTemperature - Temperature of water in storage in °C
    fltColdWaterTemperature - Temperature of incoming water in °C
    intUsage - 1 if warmwater is used, 0 else
    fltTimestep - Timestep in hours
    """
    
    intEmptyingRate = 3 # this means the storage can emptied 3 times a hour completely
    
    if intUsage == 1:
        fltDiff = fltColdWaterTemperature - fltWaterTemperature
        fltDiffTemperature = fltDiff * intEmptyingRate * fltTimeStep
        if fltDiffTemperature > fltDiff:
            fltDiffTemperature = fltDiff
    else:
        fltDiffTemperature = 0
    
    return fltDiffTemperature


def water_storage_cooling(fltWaterTemperature, fltCurrentRoomTemperature, 
                          fltStorageVolume, fltTimeStep):
    """
    fltWaterTemperature - Temperature of water in storage in °C
    fltCurrentRoomTemperature - Roomtemperature in °C
    fltStorageVolume - Volume of water storage in l
    fltTimeStep - Timestep in hours
    """
    
    fltDiff = fltCurrentRoomTemperature - fltWaterTemperature
    fltCoolingRatio = (1 / (3 * fltStorageVolume)) * 200 # a 200l storage will
                                                         # cool down in 3 hours
    fltDiffTemperature = fltDiff * fltCoolingRatio * fltTimeStep
    
    if abs(fltDiffTemperature) > abs(fltDiff):
        fltDiffTemperature = fltDiff
    
    return fltDiffTemperature


def water_heating(fltCurrentWaterTemperature, fltTargetWaterTemperature, 
                  fltTimeStep, fltStorageVolume, fltCapacity):
    """
    fltCurrentWaterTemperature - Current water temperature in °C
    fltTargetWaterTemperature - Target water temperature in °C
    fltTimestep - Timestep in hours
    fltStorageVolume - Volume of storage in l
    fltCapacity - Capacity of boiler in kW [from 11 to 35]
    """
    
    fltDiff = fltTargetWaterTemperature - fltCurrentWaterTemperature
    if fltDiff < 0:
        fltDiff = 0
    
    fltSpecificHeatCapacity = 4.182 # kJ / (kg * K)
    fltWaterDense = 1000 # kg / m³
    fltCapacityKiloJoule = fltCapacity * 3600 * fltTimeStep
    fltWaterMass = (fltStorageVolume / 1000) * fltWaterDense
    fltAddTemperature = fltCapacityKiloJoule / (fltWaterMass * fltSpecificHeatCapacity)
    
    if fltAddTemperature > fltDiff:
        fltConsumption = (fltDiff / fltAddTemperature) * fltCapacity * fltTimeStep
        fltNewWaterTemperature = fltTargetWaterTemperature
    else:
        fltConsumption = fltCapacity * fltTimeStep
        fltNewWaterTemperature = fltCurrentWaterTemperature + fltAddTemperature
    
    return fltConsumption, fltNewWaterTemperature