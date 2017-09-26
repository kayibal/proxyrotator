import pytest
import time

from proxyrotator.proxy import _Proxy


def test_disrespect_idle_time():
    a = _Proxy('A', fail_on_idle_disrespect=True)
    b = _Proxy('b', fail_on_idle_disrespect=False)
    with a:
        with b:
            time.sleep(0.1)
    with b:
        pass
    with pytest.raises(KeyError):
        with a:
            pass

def test_less_than_response_time():
    fast = _Proxy('fast', min_idle_time=0)
    with fast:
        pass
    slow = _Proxy('slow', min_idle_time=0)
    with slow:
        time.sleep(0.1)
    assert fast < slow

def test_equals():
    a = _Proxy('a')
    b = _Proxy('a')
    assert a == b

def test_less_than_idle_time():
    dead = _Proxy('dead', min_idle_time=0.1)
    dead.deactivate()

    long_idle = _Proxy('long_idle', min_idle_time=0.0001*60)
    longer_idle = _Proxy('longer_idle', min_idle_time=0.0001*60)
    with longer_idle:
        # but responds a little faster
        # if both exceed min_idle_time they are compared
        # against avg response time
        time.sleep(0.05)
    with long_idle:
        time.sleep(0.1)

    too_recently_used = _Proxy('short_idle', min_idle_time=1)
    with too_recently_used:
        pass

    assert long_idle < too_recently_used
    assert longer_idle < long_idle
    assert dead < too_recently_used
    assert dead < too_recently_used



