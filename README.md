# weewx-opensensemap 

weewx extension that sends data to OpenSenseMap

Copyright 2021- sbsRouteur

Distributed under the terms of the MIT License

Installation instructions:

1) download

`wget -O weewx-opensensemap.zip https://github.com/sbsrouteur/weewx-opensensemap/releases/download/V0.3/weewx-opensensemap-0.3.zip`

2) run the installer:

`wee_extension --install weewx-opensensemap.zip`

3) modify weewx.conf:

```
[StdRESTful]
    [[OpenSenseMap]]
      SensorId=INSERT_SENSORBOX_ID_HERE,
      AuthKey=INSERT_AUTH_KEY_HERE,
      UsUnits=False,
      [[[Sensors]]]
          [[[[outTemp]]]]
            SensorId=ENTER_OUT_TEMP_SENSOR_ID
            Unit=degree_C #Optional Unit override
            Format=%0.3f #Optional Format override
          [[[[outHumidity]]]]
            SensorId=ENTER_OUT_Humidity_SENSOR_ID                            

```  

1) restart weewx

```
sudo /etc/init.d/weewx stop
sudo /etc/init.d/weewx start
```
