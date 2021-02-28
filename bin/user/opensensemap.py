# Copyright 2021- sbsRouteur

"""
This is a weewx extension that uploads data to OpenSenseMap.
https://opensensemap.org
Minimal Configuration:
[StdRESTful]
    [[OpenSenseMap]]
        SensorBoxID = OpenSenseMap_ID
        AuthKey = OpenSenseMap_AuthSecret
        USUnits = False
        [[Sensors]]
          [[outTemp]]
            SensorId = SENSOR_ID
            Unit = °C 
          ....
"""

try:
    # Python 3
    import queue
except ImportError:
    # Python 2
    import Queue as queue
import json
import calendar
import re
import sys
import time
import six
from six.moves import urllib
try:
    # Python 3
    from urllib.parse import urlencode
except ImportError:
    # Python 2
    from urllib import urlencode


import weewx
import weewx.restx
import weewx.units
from weeutil.weeutil import startOfDayUTC
from weeutil.weeutil import to_bool

VERSION = "0.3"

if weewx.__version__ < "3":
    raise weewx.UnsupportedFeature("weewx 3 is required, found %s" %
                                   weewx.__version__)

try:
    # Test for new-style weewx logging by trying to import weeutil.logger
    import weeutil.logger
    import logging
    log = logging.getLogger(__name__)

    def logdbg(msg):
        log.debug(msg)

    def loginf(msg):
        log.info(msg)

    def logerr(msg):
        log.error(msg)
    
except ImportError:
    # Old-style weewx logging
    import syslog

    def logmsg(level, msg):
        syslog.syslog(level, 'OpenSenseMap: %s' % msg)

    def logdbg(msg):
        logmsg(syslog.LOG_DEBUG, msg)

    def loginf(msg):
        logmsg(syslog.LOG_INFO, msg)

    def logerr(msg):
        logmsg(syslog.LOG_ERR, msg)

class OpenSenseMap(weewx.restx.StdRESTful):
    def __init__(self, engine, config_dict):
        """This service recognizes standard restful options plus the following:
        SensorBoxId: OpenSenseMap Box identifier
        AuthKey : Box Auth Secret Key
        password: OpenSenseMap password
        Sensor : Dictionnary of Sensors
          Key : WeewxValueName
          SensorID : SensorID for API  
        """
        
        super(OpenSenseMap, self).__init__(engine, config_dict)
        
        site_dict = weewx.restx.get_site_dict(config_dict, 'OpenSenseMap', 'SensorId',
                                              'AuthKey','UsUnits')
        
        if site_dict is None:
            return
        Sensors=config_dict['StdRESTful']['OpenSenseMap']['Sensors']
        if Sensors is None:
            raise ("Missing sensors collection option")
        site_dict['manager_dict'] = weewx.manager.get_manager_dict(
            config_dict['DataBindings'], config_dict['Databases'], 'wx_binding')

        self.archive_queue = queue.Queue()
        self.archive_thread = OpenSenseMapThread(self.archive_queue,Sensors, **site_dict)
        self.archive_thread.start()
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        self.LogginID = site_dict['SensorId'][0:2]+"xxxxxxxx"+site_dict['SensorId'][-4:]
        loginf("OpenSenseMap v%s: Data for station %s will be posted"% (VERSION,self.LogginID))
        print("OpenSenseMap v%s: Data for station %s will be posted"% (VERSION,self.LogginID))

    def new_archive_record(self, event):
        self.archive_queue.put(event.record)

class OpenSenseMapThread(weewx.restx.RESTThread):

    _SERVER_URL = 'https://ingress.opensensemap.org'
    """_DATA_MAP = {'tempf':          ('outTemp',     '%.1f'), # F
                 'humidity':       ('outHumidity', '%.0f'), # percent
                 'winddir':        ('windDir',     '%.0f'), # degree [0-360]
                 'windspeedmph':   ('windSpeed',   '%.1f'), # mph
                 'windgustmph':    ('windGust',    '%.1f'), # mph
                 'baromin':        ('barometer',   '%.3f'), # inHg
                 'rainin':         ('hourRain',    '%.2f'), # in
                 'dailyRainin':    ('dayRain',     '%.2f'), # in
                 'monthlyrainin':  ('monthRain',   '%.2f'), # in
                 'tempfhi':        ('outTempMax',  '%.1f'), # F (for the day)
                 'tempflo':        ('outTempMin',  '%.1f'), # F (for the day)
                 'Yearlyrainin':   ('yearRain',    '%.2f'), # in
                 'dewptf':         ('dewpoint',    '%.1f'), # F
                 'solarradiation': ('radiation',   '%.1f'), # MJ/m^2
                 'UV':             ('UV',          '%.0f'), # index
                 'soiltempf':      ('soilTemp1',   '%.1f'), # F
                 'soiltempf2':     ('soilTemp2',   '%.1f'), # F
                 'soiltempf3':     ('soilTemp3',   '%.1f'), # F
                 'soiltempf4':     ('soilTemp4',   '%.1f'), # F
                 'soilmoisture':   ('soilMoist1',  '%.1f'), # %
                 'soilmoisture2':  ('soilMoist2',  '%.1f'), # %
                 'soilmoisture3':  ('soilMoist3',  '%.1f'), # %
                 'soilmoisture4':  ('soilMoist4',  '%.1f'), # %
                 'leafwetness':    ('leafWet1',    '%.1f'), # %
                 'leafwetness':    ('leafWet1',    '%.1f'), # %
                 'tempf2':         ('extraTemp1',  '%.1f'), # F
                 'tempf3':         ('extraTemp2',  '%.1f'), # F
                 'tempf4':         ('extraTemp3',  '%.1f'), # F
                 'humidity2':      ('extraHumid1', '%.0f'), # %
                 'humidity3':      ('extraHumid2', '%.0f'), # %
                 }
"""
    def __init__(self, q, Sensors,
                 SensorId, AuthKey, UsUnits,
                 manager_dict,
                 server_url=_SERVER_URL, skip_upload=False,
                 post_interval=None, max_backlog=sys.maxsize, stale=None,
                 log_success=True, log_failure=True,
                 timeout=60, max_tries=3, retry_wait=5):
        super(OpenSenseMapThread, self).__init__(q,
                                               protocol_name='OpenSenseMap',
                                               manager_dict=manager_dict,
                                               post_interval=post_interval,
                                               max_backlog=max_backlog,
                                               stale=stale,
                                               log_success=log_success,
                                               log_failure=log_failure,
                                               max_tries=max_tries,
                                               timeout=timeout,
                                               retry_wait=retry_wait,
                                               skip_upload=skip_upload)
        self.SensorId = SensorId
        self.AuthKey = AuthKey
        self.server_url = server_url
        self.Sensors = Sensors
        self.UseUSUnits = to_bool(UsUnits)


    def get_record(self, record, dbm):
        rec = super(OpenSenseMapThread, self).get_record(record, dbm)
        # put everything into the right units

        if not self.UseUSUnits :
          rec = weewx.units.to_METRIC(rec)

        return rec

    def check_response(self, response):

        for line in response:
            if not line.decode().startswith('"Measurements saved in box"'):
                raise weewx.restx.FailedPost("Server response: %s" % line.decode())
            else:
              return

    def format_url(self, record):
        logdbg("record: %s" % record)
        url = self.server_url + '/boxes/'+ self.SensorId + '/data'
        
        if weewx.debug >= 2:
            loginf('url: %s' % re.sub(r"s\/.*\/", "s/XXXXXXXXXXXXXX/", url))
        return url

    def get_post_body(self, record):  # @UnusedVariable
        """Return any POST payload.
        
        The returned value should be a 2-way tuple. First element is the Python
        object to be included as the payload. Second element is the MIME type it 
        is in (such as "application/json").
        
        Return a simple 'None' if there is no POST payload. This is the default.
        """
        Values={}
        f = weewx.units.Formatter()
        for SensorName in self.Sensors:
          Sensor=self.Sensors[SensorName]
          if SensorName in record and not record[SensorName] is None:
            ug = weewx.units._getUnitGroup(SensorName)
            if self.UseUSUnits:
              un=weewx.units.USUnits[ug]
            else:
              un=weewx.units.MetricUnits[ug]
            if 'Unit' in Sensor:
              RecordValue=weewx.units.convert((record[SensorName],un),Sensor['Unit'])[0]
            else:
              RecordValue=record[SensorName]
            
            if 'Format' in Sensor:
              FormattedValue=Sensor['Format']%(RecordValue)
            else:
              FormattedValue=f.get_format_string(un)%(RecordValue)

            Values[Sensor['SensorId']]=FormattedValue
        RetVal = json.dumps(Values, ensure_ascii=False)
        print('OpenSenseMap : Body Encoded as **%s**'% (RetVal))  
        return RetVal, 'application/json'
        
    def handle_exception(self, e, count):
        """Check exception from HTTP post.  This simply logs the exception."""
        loginf("%s: Failed upload attempt %d: %s" % (self.protocol_name, count, e))

    def get_request(self, url):
        """Get a request object. This can be overridden to add any special headers."""
        _request = urllib.request.Request(url)
        _request.add_header("User-Agent", "weewx/%s" % weewx.__version__)
        _request.add_header("Authorization", self.AuthKey)
        return _request



# Do direct testing of this extension like this:
#   PYTHONPATH=WEEWX_BINDIR python WEEWX_BINDIR/user/OpenSenseMap.py
if __name__ == "__main__":
    import optparse
    import weewx.manager

    weewx.debug = 2

    try:
        # WeeWX V4 logging
        weeutil.logger.setup('OpenSenseMap', {})
    except NameError:
        # WeeWX V3 logging
        syslog.openlog('OpenSenseMap', syslog.LOG_PID | syslog.LOG_CONS)
        syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_DEBUG))

    usage = """%prog --id=StationID --AuthKey=AuthKey [--version] [--help]"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', dest='version', action='store_true',
                      help='display driver version')
    parser.add_option('--id', metavar='OpenSenseMap_ID', help='Your SensorBox ID')
    parser.add_option('--AuthKey', metavar='OpenSenseMap_AuthSecret', help='Auth Key to upload')
    #parser.add_option('--pw', dest='pw', metavar='PASSWORD', help='your password')
    (options, args) = parser.parse_args()

    manager_dict = {
        'manager': 'weewx.manager.DaySummaryManager',
        'table_name': 'archive',
        'schema': None,
        'database_dict': {
            'SQLITE_ROOT': '/home/weewx/archive',
            'database_name': 'weewx.sdb',
            'driver': 'weedb.sqlite'
        }
    }

    if options.version:
        print("meteotemplate uploader version %s" % VERSION)
        exit(0)

    if options.id == None:
      print("Wrong params run : "+ usage )
      exit(0)
    else:
      print("uploading to station %s" % options.id)

    Sensors={'windSpeed':{'SensorId':'603b5c4d2c4a41001b8db744','Unit':"km_per_hour",'Format':'%.2f'},}
    q = queue.Queue()
    t = OpenSenseMapThread(q,Sensors,options.id,options.AuthKey,False,  manager_dict)
    t.start()
    q.put({'dateTime': int(time.time() + 0.5),
           'usUnits': weewx.US,
           'outTemp': 51.26,
           'inTemp': 75.8,
           'outHumidity': 72,
           'windSpeed': 8,
           'windDir':331})
    q.put(None)
    t.join(20)
