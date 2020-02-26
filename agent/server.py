import traceback
from xmlrpc.server import SimpleXMLRPCServer
from datetime import datetime

from .resolver import RPCResolver


class RPCServer:

    def __init__(self, host = "", port = 55555, log_path = "", f_print_logs = False):
        self.host = host
        self.port = port
        self.log_path = log_path
        self.f_print_logs = f_print_logs

    def start(self):
        server = SimpleXMLRPCServer(
            (self.host, self.port),
            logRequests = False,
            use_builtin_types = True,
            allow_none = True,
            encoding = "utf-8"
        )
        print(f"Agent listening on port {self.port}...")
        server.register_instance(RPCDispatcher(self.log_path,
                                               f_print_logs = self.f_print_logs))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Stopped!")
            exit(0)


class RPCDispatcher(RPCResolver):

    def __init__(self, log_path, f_print_logs = False):
        self.file = None
        if log_path:
            self.file = open(log_path, "a", encoding = "utf-8")
        self.f_print_logs = f_print_logs
        self.log(0, "dispatch", "started")

    def log(self, id_, method, msg):
        if self.file or self.f_print_logs:
            msg = f"{datetime.now()}: RPCServer (id={id_}) method=<{method}>: {msg}\n"
            try:
                if self.file:
                    self.file.write(msg)
                if self.f_print_logs:
                    print(msg)
            except Exception as exc:
                print(exc)

    def _dispatch(self, method, params):
        args, kwargs, id_ = params
        ret = {"method_called": method}
        self.log(id_, method, f"calling with args={args},kwargs={kwargs}")
        try:
            obj = self
            for part in method.split("."):
                obj = getattr(obj, part)
            ret["method_resolved"] = obj.__qualname__
            ret["returns"] = obj(*args, **kwargs)
            self.log(id_, method, f"success")
        except:
            ret["traceback"] = traceback.format_exc()
            self.log(id_, method, f"error")
        return ret
