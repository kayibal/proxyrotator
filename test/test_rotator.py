import pytest
import requests
import time
from random import normalvariate

from proxyrotator import ProxyRotator
from proxyrotator.proxy import _Proxy


def proxies(mean_idle_time=0.05, size=100):
    return [_Proxy('no_{}'.format(i),
                   min_idle_time=normalvariate(mean_idle_time, mean_idle_time/2))
            for i in range(size)]

def test_proxy_rotator(monkeypatch):
    proxies = ['no_{0:02d}'.format(i) for i in range(100)]
    slow_proxies = set(proxies[:20])
    ok_proxies = set(proxies[20:50])
    fast_proxies = set(proxies[50:70])
    error_proxies = set(proxies[70:])

    def mocked_get(*args, proxies=None, **kwargs):
        proxy_adr = proxies['http']
        no = int(proxy_adr[-2:])
        res = requests.Response()
        res.status_code = 200
        if proxy_adr in slow_proxies:
            time.sleep(0.1)
            return res
        elif proxy_adr in ok_proxies:
            time.sleep(0.05)
            return res
        elif proxy_adr in fast_proxies:
            time.sleep(0.001)
            return res
        elif proxy_adr in error_proxies:
            if no < 80:
                res.status_code = 429
                return res
            elif no < 90:
                raise requests.exceptions.ConnectTimeout()

    monkeypatch.setattr(requests, 'get', mocked_get)

    rot = ProxyRotator(proxies)

    for i in range(100):
        print(i)
        res = rot.get('http://some_url/test.html')