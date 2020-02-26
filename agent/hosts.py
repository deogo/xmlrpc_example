from typing import Dict
import threading

from .client import RPCClient, RPCClient_T
from .resolver import RPCResolver


class MHosts:
    """Hosts

    Attrs:
        :all: call same method from all hosts
        :allt: call same method from all hosts async
        :cur: call method from current host(=thread name)
        :curt: call method from current host async(=thread name)

    Also, each host name passed creates two attributes:

        :<name>: call method from that specific host
        :<name>t: call methods async

    Returns:
        result if called from specific host\n
        dict 'host=result' if called from all hosts

    """
    _hosts = {}

    class _MHost:
        """Host"""

        def __init__(self, name: str, ip: str, port: int, log_out_dir: str, f_print_logs: bool):
            self.name = name
            self.ip = ip
            self.port = port
            self.rpc = RPCClient(self.ip, self.port,
                                 remote_host_name = name,
                                 log_out_dir = log_out_dir,
                                 f_print_logs = f_print_logs)
            self.rpct = RPCClient_T(self.ip, self.port,
                                    remote_host_name = name,
                                    log_out_dir = log_out_dir,
                                    f_print_logs = f_print_logs)

    def __init__(self, hosts: Dict[str, dict], log_out_dir: str = None, f_print_logs: bool = False):
        assert not self._hosts, f"{mhosts} class cannot be instantiated more than once"
        assert hosts
        for name, prms in hosts.items():
            obj = MHosts._MHost(
                name, prms["ip"], prms["agent_port"], log_out_dir, f_print_logs)
            assert obj.rpc.is_alive(), f"{obj.name} does not seem to be alive"
            setattr(self, name, obj.rpc)
            setattr(self, name + "t", obj.rpct)
            self._hosts[name] = obj
        self.all = MHosts._ProxyAll(self._hosts, False)
        self.allt = MHosts._ProxyAll(self._hosts, True)
        self.cur = MHosts._ProxyCurrent(self._hosts, False)
        self.curt = MHosts._ProxyCurrent(self._hosts, True)

    def __len__(self):
        return len(self._hosts)

    def __iter__(self):
        for tpl in self._hosts.items():
            yield tpl

    def __getitem__(self, name):
        return self._hosts[name]

    class _MultiCall:
        """Calls same method on all hosts

        Returns dict host_name : result"""

        def __init__(self, method, hosts: dict, threaded: bool):
            self.threaded = threaded
            if threaded:
                self.rpc_methods = dict({
                    name: getattr(host.rpct, method) for name, host in hosts.items()})
            else:
                self.rpc_methods = dict({
                    name: getattr(host.rpc, method) for name, host in hosts.items()})

        def __getattr__(self, name):
            for method in self.rpc_methods.values():  # either RPCMethodCall or RPCMethodCall_T
                getattr(method, name)
            return self

        def __call__(self, *args, **kwargs):
            if self.threaded:
                return dict(map(lambda t: (t[0], t[1].join()),
                                [(host_name, m(*args, **kwargs)) for host_name, m
                                    in self.rpc_methods.items()]))
            return dict([(host_name, m(*args, **kwargs)) for host_name, m
                         in self.rpc_methods.items()])

    class _ProxyAll(RPCResolver):
        """Allows to run same method for all hosts

        Returns:
            dict 'host_name : result'\n
            raises RPCCallError on any call fail
        """

        def __init__(self, hosts, threaded: bool):
            self._hosts = hosts
            self._threaded = threaded

        def __getattribute__(self, name):
            if name.startswith("_"):
                return object.__getattribute__(self, name)
            return MHosts._MultiCall(name, self._hosts, self._threaded)

    class _ProxyCurrent(RPCResolver):
        """Run method on current server

        Current server determined by current thread name

        Using this proxy from thread for which
        there is no RPCClient created will cause KeyError exception"""

        def __init__(self, hosts: dict, threaded: bool):
            self._hosts = hosts
            self._threaded = threaded

        def __getattribute__(self, name):
            if name.startswith("_"):
                return object.__getattribute__(self, name)
            t_name = threading.current_thread().name
            if self._threaded:
                return getattr(self._hosts[t_name].rpct, name)
            return getattr(self._hosts[t_name].rpc, name)
