# installer for OpenSensMap Rest uploader
# Copyright 2021- 
# Distributed under the terms of the MIT License

from weecfg.extension import ExtensionInstaller

def loader():
    return OpenSenseMapInstaller()

class OpenSenseMapInstaller(ExtensionInstaller):
    def __init__(self):
        super(OpenSenseMapInstaller, self).__init__(
            version="0.1",
            name='OpenSenseMap',
            description='Upload weather data to OpenSenseMap.',
            author="sbsrouteur",
            author_email="sbsrouteur@free.fr",
            restful_services='user.opensensemap.OpenSenseMap',
            config={
                'StdRESTful': {
                    'OpenSenseMap': {
                        'SensorId': 'INSERT_SENSORBOX_ID_HERE',
                        'AuthKey': 'INSERT_AUTH_KEY_HERE',
                        'UsUnits':'False',
                        'enable':'True',
                        'Sensors':{
                          'outTemp':{
                            'SensorId':'ENTER_OUT_TEMP_SENSOR_ID'                            
                          },
                          'outHumidity':{
                            'SensorId':'ENTER_OUT_Humidity_SENSOR_ID'                            
                          }
                        }
                        }}},
            files=[('bin/user', ['bin/user/opensensemap.py'])]
            )
