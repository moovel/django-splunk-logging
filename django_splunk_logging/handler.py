import logging
import inspect
from .event import SplunkEvent
from .utils import _get_frame_from_record, _get_request

class SplunkHandler(logging.Handler):

    def emit(self, record):
        if record.exc_info:
            # if the record is a raised exception
            # we want to get the frame that is in the API function
            # IE not any wrappers
            frame = _get_frame_from_record(record)
            request = frame.f_locals.get("request", None)

            record_data = {
                'method': frame.f_code.co_name,
                'line': frame.f_lineno,
                'module': inspect.getmodule(frame).__name__,
                'path': frame.f_code.co_filename,
                'message': record.getMessage(),
                'status_code': getattr(record.exc_info[0],
                                       'http_response_code',
                                       500),
                'traceback': record.exc_text
            }

        else:
            # if the record is a regular log
            request = _get_request()

            record_data = {
                'method': record.funcName,
                'line': record.lineno,
                'module': record.module,
                'message': record.getMessage(),
                'path': record.pathname,
            }

        user_id = None
        if request:
            if request.user.is_authenticated():
                user_id = request.user.id

        SplunkEvent(key="server_log",
                    name=record.levelname,
                    request=request,
                    obj=record_data,
                    user=user_id)
