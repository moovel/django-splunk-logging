# Django-Splunk-Logging

## About
Django-Splunk-Logging implements a singleton data format and pipes your events into splunk enterprise by utilizing the HTTP Event Collector.

### SplunkEvent Example
```
def update_name_api(request):
    user = request.user
    user.name = request.GET['name']
    user.save()
    from django_splunk_logging import SplunkEvent
    SplunkEvent(key="User_event",
                request=request,
                name="name_change",
                obj=user,
                user=user)
    return "Success!"
```

This will send an event into splunk with the sourcetype 'User_event':
```
{
    auth:  true,
    user:  303,
    event:  name_change,
    eventData: {
      name:"NEW NAME",
      email:"USER@MAIL.COM"
      **other user model data**
   },
    request: {
      GET: {
        api_key:  xxxxxxxxxxxxxxxxxxxxxx 
     },
     POST: {
         name: "NEW NAME"
     },
      META: {
        CLIENT:  iPhone,
        HTTP_HOST:  website.com,
        HTTP_REFERER:  null,
        HTTP_USER_AGENT:  iPhone; iOS 9.2.1; Scale/2.00,
        HTTP_X_FORWARDED_FOR:  70.196.185.31 
     } 
      host:  website.com,
      method:  POST,
      path:  /auth/profile/?api_key=xxxxxxxxxxxxxxxxxxxxxx 
   } 
}
```

### Logging Example
Also contained is a logging handler that you can set up in your django settings to insert logging messages that are raised throughout your application.
```
def api_function(request):
    if request.GET.get('special', None):
        logging.info("Special function is firing!")
        ...
```
This will out throw an event into splunk with the sourcetype 'server_log':
```
{
    auth:  true
    event:  INFO 
    eventData: {
      line:  539 
      message:  "Special function is firing!"
      method:  api_function 
      module:  the_api_module 
      path:  /path/to/the_api_module.py
   } 
    request: {
      GET: { 
      special: true,
      api_key: xxxxxxxxxxxxxxxxxxxxx
     } 
      META: {
      ... 
     } 
      Version:  1.0.14 
      host:  website.com 
      method:  GET 
      path:  /api/function/?api_key=xxxxxxxxxxxxxxxxxxxxx 
   } 
    user:  303 
}
```

### Exception example
This handler also works with raising an exception:
```
class InvalidParameter(Exception):
    http_response_code = 400
    def __init__(self, message=None, **kwargs):
        super(InvalidParameter, self).__init__(message)

def location(request):
    if not request.GET.get('lat', None) and request.GET.get('lng', None):
        raise InvalidParameter("Must supply lat and lng")
```

Will send data to splunk as well:
```
{
    auth:  false 
    event:  ERROR 
    eventData: {
      line:  322 
      message:  Must supply lat and lng
      method:  location
      module:  location_api
      path:  /path/to/location_api.py
      response_code:  400 
      traceback:  Traceback (most recent call last):
          File "/home/ubuntu/beta/production/ridescout/api/decorators.py", line 150, in wrapper
            api_results = f(*args, **kwargs)
          File "/home/ubuntu/beta/production/ridescout/sdk/api.py", line 322, in sync
            platform))
        InvalidParameterError: No app org.trimet.mt.mobiletickets for android
   } 
    request: {
      GET: {
        api_key:  xxxxxxxxxxxxxxxxx 
        lat:  0.0 
     } 
      META: { [-] 
        CLIENT:  android 
        HTTP_HOST:  website.com 
        HTTP_REFERER:  null 
        HTTP_USER_AGENT:  okhttp/2.5.0 
        HTTP_X_FORWARDED_FOR:  24.163.101.232 
     } 
      Version:  1.0.14 
      host:  website.com 
      method:  GET 
      path:  /location/?lat=0.0&api_key=xxxxxxxxxxxxxxxxx 
   } 
    user:  null 
}
```

## Installation
Run `pip install django-splunk-logging`

Add `splunk` to `INSTALLED_APPS` in your django settings
```
INSTALLED_APPS = (
...
'django_splunk_logging',
)
```

In your django settings:
```
...
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(levelname)s  %(name)s  %(asctime)s %(filename)s:%(lineno)s] %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'splunk':{
            'class':'django_splunk_logging.SplunkHandler'
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers':{
        '': {
            'handlers': ['console','splunk'],
            'level':'INFO',
        },
        'django':{
            'handlers': ['console','splunk',],
            'propagate':False,
        },
        'py.warnings':{
            'handlers':['null'],
            'propagate':False,
        },
        'requests.packages.urllib3':{
            'handlers':['null'],
            'propagate':False,
        }
    }
}

##
# Django-Splunk-Logging
##
# Enable or disable Splunk Logs
SPLUNK_LOGS = True
# HTTP Event Collector Token
SPLUNK_TOKEN = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx"
# Splunk Event Collector has enabled HTTPS
SPLUNK_HTTPS = False
# Splunk Server Address
SPLUNK_ADDRESS = "XX.XXX.XX.XXX"
# Event Collector Port (default: 8088)
SPLUNK_EVENT_COLLECTOR_PORT = "8088"
# Enable threading on event sending
SPLUNK_THREAD_EVENTS = True
```

Optionally, you can specify `VERSION` in settings to add to the splunk data