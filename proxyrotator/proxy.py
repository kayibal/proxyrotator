import datetime as dt
import time
from functools import total_ordering

import logging


@total_ordering
class _Proxy():
    """Internal Proxy object.

    This class keeps track of Proxies and defines a
    total ordering between them based on their statistics
    and last time used.

    In case fail_on_idle_disrespect is set and the proxy pool
    is not able to respect all proxies minimum idle times due to
    too little number of proxies available to serve the current
    income in requests. A KeyError is raised. If not set only a
    warning will be raised and the min_idle_time will de ignored
    in case there is no alternative proxy left left.
    """

    idle_disrispect_msg = "Min idle time of {} disrispected. " \
                          "This might lead to failures. Try increasing" \
                          "number of proxies."
    def __init__(self, proxy_ip: str,
                 min_idle_time: float=300.0,
                 fail_on_idle_disrespect: bool=True):
        """Initialize Proxy

        :param proxy_ip: str
            the proxies ip adress
        :param min_idle_time: float
            minimum time this proxy should be idle in seconds
        :param fail_on_idle_disrespect: bool
            if set to true the proxy will raise an
            exception if used too early.
        """
        self.proxy = proxy_ip
        self.min_idle_time = min_idle_time * 1e6
        self.fail_on_idle_disrespect = fail_on_idle_disrespect
        self.times_used = 0
        self.last_used = dt.datetime.today() - dt.timedelta(days=1)
        self.response_times = []
        self.active = True

    def __eq__(self, other):
        if self.proxy == other.proxy:
            return True

        return False

    @property
    def idle_time(self):
        if self.times_used < 1:
            return dt.timedelta.max
        return dt.datetime.now() - self.last_used

    @property
    def _idle_microseconds(self):
        return self.idle_time.total_seconds() * 1e6

    @property
    def _idle_time_norm(self):
        return self.min_idle_time / self._idle_microseconds

    @property
    def avg_response_time(self):
        if len(self.response_times) == 0:
            return 0
        return sum(self.response_times) / len(self.response_times)

    def deactivate(self):
        self.active = False

    def __lt__(self, other):
        if self.active:
            if self._idle_microseconds > self.min_idle_time \
                    and other._idle_microseconds > other.min_idle_time:
                return self.avg_response_time < other.avg_response_time
            return self._idle_time_norm < other._idle_time_norm
        else:
            return True

    def __enter__(self):
        log = logging.getLogger(__name__)
        self._start = time.time()
        if self.min_idle_time > self._idle_microseconds:
            msg = self.idle_disrispect_msg.format(str(self))
            if self.fail_on_idle_disrespect:
                raise KeyError(msg)
            else:
                log.warning(msg)
                log.warning('Ignoring min_idle_time...')
        return self.proxy

    def __exit__(self, *args):
        self.last_used = dt.datetime.now()
        self.response_times.append(time.time() - self._start)
        self.times_used += 1

    def __repr__(self):
        return "[{} {}|{}min ~{}s]".format(self.proxy, self.idle_time,
                                           self.min_idle_time/1e6, self.avg_response_time)