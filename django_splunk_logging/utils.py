import sys

def _get_frame_from_record(record):
    """
    takes a exception log record and looks at the traceback object.
    Traverses the traceback and finds the inner most call
    that takes in a request object as an arguement

    This allows more accurate logging for wrapped api's
    """
    tb = record.exc_info[2]
    tb_with_request = tb
    while tb.tb_next:
        tb_next = tb.tb_next
        if tb_next.tb_frame.f_locals.get('request', None):
            tb_with_request = tb_next
        tb = tb_next
    return tb_with_request.tb_frame


def _get_request():
    """
    Traverses stack to find a request object
    """
    request = None
    try:
        for i in range(8, 0, -1):
            if 'request' in sys._getframe(i).f_locals.keys():
                request = sys._getframe(i).f_locals['request']
                break
    except:
        pass
    return request