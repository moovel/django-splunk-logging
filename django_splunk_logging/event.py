import datetime
import time
import logging
import json
from uuid import UUID
import os

from django.conf import settings
import requests
from threading import Thread
from .utils import _get_request


class SplunkEvent(object):
    _key = None
    _timestamp = None
    _request = None
    _user = None
    _auth = None
    _start = None
    _obj = None
    _name = None
    _auth_key = "Splunk {0}".format(settings.SPLUNK_TOKEN)

    def __init__(self, *args, **kwargs):
        self._key = kwargs.pop('key', "Generic")
        self._timestamp = str(time.time())
        self._request = kwargs.pop('request', _get_request())
        self._user = kwargs.pop('user', None)
        self._name = kwargs.pop('name', None)
        self._obj = kwargs.pop('obj', None)

        if self._request is not None:
            try:
                self._auth = self._request.user.is_authenticated()
                self._user = self._request.user.id
            except:
                self._auth = False

        ran_shortcut = self.package_obj(self._obj)
        if ran_shortcut:
            if settings.SPLUNK_THREAD_EVENTS:
                Thread(target=self.send_to_splunk).start()
            else:
                self.send_to_splunk()

    def package_obj(self, obj):
        """
        Shortcut method if an object is passed to the init method.

        Generally used for objects that have a to_json() method.
        """
        if obj is None:
            return False
        if isinstance(obj, list):
            ## if it is a list of objects, handle it in self.format()
            return True

        if 'to_json' in dir(obj):
            for k, v in obj.to_json().iteritems():
                setattr(self, k, v)

        elif isinstance(obj, dict):
            for key, value in obj.iteritems():
                if type(value) is datetime.datetime:
                    setattr(self, key, value.strftime('%m/%d/%Y %H:%M:%S'))
                elif type(value) is UUID:
                    setattr(self, key, str(value))
                else:
                    setattr(self, key, value)
        else:
            for oa in [x for x in obj.__dict__ if not x.startswith('_')]:
                if type(getattr(obj, oa)) is datetime.datetime:
                    setattr(self,
                            oa,
                            getattr(obj, oa).strftime('%m/%d/%Y %H:%M:%S'))
                elif type(getattr(obj, oa)) is UUID:
                    setattr(self, oa, str(getattr(obj, oa)))
                else:
                    setattr(self, oa, getattr(obj, oa))
        return True

    def send_to_splunk(self):
        if not settings.SPLUNK_LOGS:
            return
        url = settings.SPLUNK_ADDRESS + ":" + \
            settings.SPLUNK_EVENT_COLLECTOR_PORT + \
            '/services/collector/event'

        if settings.SPLUNK_HTTPS:
            url = "https://" + url
        else:
            url = "http://" + url

        headers = {'Authorization': self._auth_key}
        r = requests.post(url,
                          headers=headers,
                          data=json.dumps(self.format()),
                          verify=False)
        if r.status_code > 200:
            # logging.error(
            #     'error sending splunk event to http collector: {0}'.format(
            #         r.json()))
            # attempt to avoid recursion with the logging handler
            print 'error sending splunk event to http collector: {0}'.format(
                r.text)

    def format_request(self):
        """ Format the request to JSON. """
        if not self._request:
            return {}
        else:
            data = {
                'path': self._request.get_full_path(),
                'host': self._request.get_host(),
                'GET': self._request.GET,
                'method': self._request.method,
                'META': {
                    'HTTP_HOST': self._request.META.get('HTTP_HOST', None),
                    'HTTP_REFERER': self._request.META.get('HTTP_REFERER', None),
                    'HTTP_USER_AGENT': self._request.META.get('HTTP_USER_AGENT', None),
                    'HTTP_X_FORWARDED_FOR': self._request.META.get('HTTP_X_FORWARDED_FOR', None),
                    'CLIENT': 'OTHER',
                },
            }
            if 'is_ios' and 'is_android' in self._request.__dict__:
                if self._request.is_ios:
                    data['META']['CLIENT'] = 'ios'
                elif self._request.is_android:
                    data['META']['CLIENT'] = 'android'
                else:
                    data['META']['CLIENT'] = 'android'

            if hasattr(settings, "VERSION"):
                data['version'] = settings.VERSION
            try:
                if self._request.method == "DELETE":
                    data['DELETE'] = self._request.DELETE
                elif self._request.method == "PUT":
                    data['PUT'] = self._request.PUT
                elif self._request.method == "POST":
                    data['POST'] = self._request.POST
            except Exception as e:
                pass
            return data

    def format(self):
        """ Format the SplunkEvent to JSON. """
        if isinstance(self._obj, list):
            # list of objects
            event_obj = []
            for o in self._obj:
                item = {}
                if 'to_json' in dir(o):
                    item = o.to_json()
                elif isinstance(o, dict):
                    item = o
                else:
                    for oa in [x for x in o.__dict__ if not x.startswith('_')]:
                        if type(getattr(o, oa)) is datetime.datetime:
                            item[oa] = getattr(o, oa).strftime(
                                '%m/%d/%Y %H:%M:%S')
                        elif type(getattr(o, oa)) is UUID:
                            item[oa] = str(getattr(o, oa))
                        else:
                            item[oa] = getattr(o, oa)
                event_obj.append(item)

        else:
            event_obj = {}
            for x in [attr for attr in self.__dict__ if not attr.startswith('_')]:
                event_obj[x] = getattr(self, x)
        data = {}
        data['time'] = self._timestamp
        data['sourcetype'] = self._key
        data['event'] = {
            'request': self.format_request(),
            'auth': self._auth,
            'user': self._user,
            'eventData': event_obj,
            'event': self._name,
        }
        return data

    def start_timer(self):
        """ Start a Timer. """
        self._start = time.time()

    def stop_timer(self):
        """ Stop the Timer and assign value to object. """
        try:
            self.execution = int(round((time.time() - self._start)*1000))
        except AttributeError:
            logging.error('you didnt start the timer!')
