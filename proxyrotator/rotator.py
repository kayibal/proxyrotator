import logging
import threading
import datetime as dt
import heapq
import requests

from .proxy import _Proxy

class ProxyRotator():
    _lock = threading.Lock()

    def __init__(self, proxies,
                 min_idle_time: float = 300.0,
                 fail_on_idle_disrespect: bool = True):
        self.proxies = [_Proxy(p, min_idle_time, fail_on_idle_disrespect)
                        for p in proxies]
        heapq.heapify(self.proxies)
        self._last_heapify = dt.datetime.now()
        self.refresh_interval = min_idle_time * 1e3

    @property
    def _heapify_time(self):
        return (self._last_heapify - dt.datetime.now()).total_seconds() * 1e6

    def get(self, *args, **kwargs):
        log = logging.getLogger(__name__)
        res = None
        self._lock.acquire()
        if self._heapify_time < self.refresh_interval:
            heapq.heapify(self.proxies)
        try:
            prxy = heapq.heappop(self.proxies)
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