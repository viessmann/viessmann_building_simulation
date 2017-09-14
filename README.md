# Viessmann building simulation for Hack Zürich 2017
The Viessmann building simulation for Hack Zürich 2017 is written in Python3 and tested on Windows and Raspbian on Raspberry Pi 3 Model B.

## Features
The Viessmann building simulation is a highly simplified simulation of a house consisting of a room, a domestic hot water storage and a solar energy system (photo voltaic / solar thermal energy).

Simulated processes:
* Heating up the room by heating device
* Cooling down the room by the difference between room and outdoor temperature
* Heating up the water storage by heating device
* Cooling down the water storage by the difference between room and water temperature
* Cooling down the water storage by usage of customer (extracting warm water)
* Producing energy by solar radiation

## Files
| Filename | Comment |
| -------- | ------- |
| building_simulation.py | Core functions of building simulation |
| building_simulation_main_function.py | Main function with looping over input data and controlling by Alexa (DynamoDB) or local csv-file |
| DynamoDB_table_infos.csv | Parameter of dynamodb-table like access-key, currently filled with placeholders |
| InputData.csv | Input weather data of one week in equidistant 5 minute time steps |
| roomtemperature.csv | Contains target room temperature and is used as aletrnative to control by Alexa |

## Usage
1. Insert DynamoDB parameter into DynamoDB_table_infos.csv (optional)
2. Run building_simulation_main_function.py
