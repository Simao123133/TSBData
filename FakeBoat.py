#!/usr/bin/local python3

import csv
import json
import time
import paho.mqtt.client as mqtt

broker_address="tsb1.vps.tecnico.ulisboa.pt" 

client = mqtt.Client("P1") #create new instance
client.username_pw_set('TSB', password='tecnicosb2020')
print("connecting to broker")
client.connect(broker_address, 1883, 60) #connect to broker

data = {"Timestamp":0, 
		"Speed":0, 
		"dist":0, 
		"left_angle":0, 
		"right_angle":0, 
		"pitch":0, 
		"roll":0, 
		"yaw":0, 
		"velX":0,
		"velY":0, 
		"velZ":0, 
		"AbsTime":0}
	

with open('Dados_Xsens_2021-09-10_12-35-58.csv') as csv_file:
	csv_reader = csv.DictReader(csv_file, delimiter=',')
	line_count = 0
	for row in csv_reader:
		if line_count == 0:
			data["Timestamp"] = row["Timestamp"]
		#if line_count % 40:
		# 	line_count += 1
		# 	continue
		if line_count > 1:
			time.sleep(float(row["Timestamp"]) - float(data["Timestamp"]))
		if line_count == 0:
			print(f'Column names are {", ".join(row)}')
			line_count += 1
		else:
			data["Timestamp"] = row["Timestamp"]
			data["Speed"] = row["Speed"]
			data["dist"] = row["dist"]
			data["left_angle"] = row["left_angle"]
			data["right_angle"] = row["right_angle"]
			data["pitch"] = row["pitch"]
			data["roll"] = row["roll"]
			data["yaw"] = row["yaw"]
			data["velX"] = row["velX"]
			data["velY"] = row["velY"]
			data["velZ"] = row["velZ"]
			data["AbsTime"] = row["AbsTime"]
			line_count += 1
			json_data = json.dumps(data)
			client.publish("TSB/SR03/AHRS", json_data)
	print(f'Processed {line_count} lines.')