import os
from xmlrpc.client import ServerProxy
from uuid import uuid4
import time
from datetime import datetime
import threading

from .resolver import RPCResolver


class RPCClient(RPCResolver):

    """
    Syncronous RPC Client

    returns called method result or raise RPCCallError
    """

    def __init__(self, host, port, remote_host_name = None, log_out_dir = None, f_print_logs = False):
        self._remote_host_name = remote_host_name
        self._file = None
        self._f_print_logs = f_print_logs
        if log_out_dir:
            self._file = open(os.path.join(log_out_dir, f"RPCClient_{self._remote_host_name}.log"),
                              "w", encoding = "utf-8")
        self._host = host
        self._uri = f"http://{host}:{port}/"
        self._proxy = ServerProxy(self._uri, encoding = "utf-8", allow_none = True,
                                  use_datetime = True, use_builtin_types = True)

    def __del__(self):
        if self._file:
            self._file.close()
        with self._proxy:
            pass

    def _log(self, msg):
        if self._file or self._f_print_logs:
            try:
                msg = (f"{datetime.now()}: RPCClient "
                       f"<{self._remote_host_name or self._host}>: {msg}\n")
                if self._file:
                    self._file.write(msg)
                if self._f_print_logs:
                    print(msg)
            except Exception as exc:
                print(exc)

    def _resolve_attr(self, name):
        return RPCMethodCall(self._proxy, self, name)

    def __getattribute__(self, name: str):  # skipping usual attr resolving
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        return self._resolve_attr(name)


class RPCClient_T(RPCClient):
    """Asyncronous version of RPCClient

    Method call returns started thread

    The thread has join() method which returns result, or raise RPCCallError
    """

    def _resolve_attr(self, name):
        return RPCMethodCall_T(self._proxy, self, name)


class RPCMethodCall:
    """Used to control rpc-proxy methods call"""

    def __init__(self, proxy: ServerProxy, client: RPCClient, name: str):
        self.proxy = getattr(proxy, name)
        self.method = name
        self.client = client
        self.id_ = 0

    def __getattr__(self, name: str):
        self.proxy = getattr(self.proxy, name)
        self.method += f".{name}"
        return self

    def __str__(self):
        return f'{self.__class__.__name__}: id={self.id_} method={self.method}'

    def _call(self, *args, **kwargs):
        self.id_ = uuid4().hex
        self.client._log(f'id={self.id_}:\n\tmethod: {self.method}\n\targs={args}\n\tkwargs={kwargs}')
        tries = 10
        while tries:
            tries -= 1
            try:
                ret = self.proxy(args, kwargs, self.id_)
                break
            except ConnectionRefusedError as ex:
                self.client._log(f'id={self.id_}:\n{ex}\nurl={self.client._uri}')
                if not tries:
                    raise ex
                time.sleep(5)
                continue
        tb = ret.get("traceback")
        returns = ret.get("returns", None)
        self.client._log(f'id={self.id_}:\n\t'
                         + "\n\t".join(f"{k}: {v}" for k, v in ret.items()))
        if tb:
            raise RPCCallError(self.method, tb, self.id_, self.client._remote_host_name)
        return returns

    def __call__(self, *args, **kwargs):
        return self._call(*args, **kwargs)


class RPCMethodCall_T(RPCMethodCall):
    """Threaded version of RPCMethodCall

    Returns started thread instead result

    This thread has join() method which returns result, or raise exception
    """

    def __call__(self, *args, **kwargs):
        t = CMethodThread(self, self._call, args, kwargs)
        t.start()
        return t


class CMethodThread(threading.Thread):

    def __init__(self, rpc: RPCMethodCall_T, foo, args, kwargs):
        super().__init__(daemon = True)
        assert callable(foo), f"{foo} is not callable"
        self.foo = foo
        self.args = args
        self.kwargs = kwargs
        self.ret = None
        self.exc = None
        self.rpc = rpc

    def join(self, timeout = None):
        print(f"\tWaiting for thread {self.rpc}")
        super().join(timeout)
        if self.exc:
            raise self.exc
        return self.ret

    def run(self):
        try:
            self.ret = self.foo(*self.args, **self.kwargs)
        except Exception as exc:
            self.exc = exc


class RPCCallError(Exception):
    """Raised when RPCClient method call fails"""

    def __init__(self, method, tb, id_, host_name):
        self.tb = tb
        self.method = method
        self.id_ = id_
        self.host_name = host_name
        super().__init__()

    def __str__(self):
        tb = self.tb.replace('\n', '\n\t')
        return f"<{self.host_name}> method '{self.method}' call failed (id={self.id_}):\n\t{tb}"
