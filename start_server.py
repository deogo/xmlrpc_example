from os import path, chdir
import threading

from agent.server import RPCServer

chdir(path.dirname(__file__))
# Simulate having few hosts
for port in [55555, 55556, 55557]:
    rpc = RPCServer(
        host = '',
        port = port,
        log_path = path.join(path.dirname(__file__), f"agent_{port}.log"),
        f_print_logs = False  # if True - server prints logs in stdout
    )

    threading.Thread(target=rpc.start).start()

