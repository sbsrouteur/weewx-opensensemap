# weewx-opensensemap 
weewx extension that sends data to OpenSenseMap
Copyright 2011- sbsRouteur
Distributed under the terms of the MIT License

Installation instructions:

1) download

wget -O weewx-opensensemap.zip https://github.com/xxxxxg/archive/master.zip

2) run the installer:

wee_extension --install weewx-wbug.ziop

3) modify weewx.conf:

'''
[StdRESTful]
    [[OpenSenseMap]]
      SensorId=INSERT_SENSORBOX_ID_HERE,
      AuthKey=INSERT_AUTH_KEY_HERE,
      UsUnit=False,
      [[Sensors]]
          [[outTemp]]
            SensorId=ENTER_OUT_TEMP_SENSOR_ID                            
          },
          [[outHumidity]]
            SensorId=ENTER_OUT_Humidity_SENSOR_ID                            
          
'''
4) restart weewx

sudo /etc/init.d/weewx stop
sudo /etc/init.d/weewx start