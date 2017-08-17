import logging
import threading
import heapq
import requests

from .proxy import _Proxy

class ProxyRotator():
    _lock = threading.Lock()

    def __init__(self, proxies):
        self.proxies = [_Proxy(p) for p in proxies]
        heapq.heapify(self.proxies)

    def get(self, *args, **kwargs):
        log = logging.get(__name__)
        res = None
        self._lock.acquire()
        try:
            prxy = self.proxies.pop()
        finally:
            self._lock.release()
        with prxy as proxy_adr:
            kwargs.update({'proxies': {'http': proxy_adr}})
            try:
                log.info('Using proxy {}'.format(proxy_adr))

                r = requests.get(*args, **kwargs)
                if r is None or not r.ok:
                    prxy.deactivate()
            except requests.exceptions.RequestException as e:
                log.warning(str(e))
                prxy.deactivate()
        if prxy.active:
            self._lock.acquire()
            try:
                heapq.heappush(self.proxies, prxy)
            finally:
                self._lock.release()
            res = r
        return res