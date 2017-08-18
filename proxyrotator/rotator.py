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
        log = logging.getLogger(__name__)
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
                # TODO too broad dead url might deactivate ok proxy
                if r is None or 400 <= r.status_code <= 500:
                    prxy.deactivate()
            #TODO evaluate exception class
            except requests.exceptions.RequestException as e:
                log.warning(str(e))
                prxy.deactivate()
        # dont put proxy back if it was deactivated
        if prxy.active:
            self._lock.acquire()
            try:
                heapq.heappush(self.proxies, prxy)
            finally:
                self._lock.release()
            res = r
        return res