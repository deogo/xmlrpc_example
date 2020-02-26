from agent.hosts import MHosts
import threading

"""See agent.resolver for available methods"""
# Simulate having few hosts
hosts_ = {
    "host1": {"ip": "127.0.0.1", "agent_port": 55555},
    "host2": {"ip": "127.0.0.1", "agent_port": 55556},
    "host3": {"ip": "127.0.0.1", "agent_port": 55557},
}


mhosts = MHosts(hosts_,
                log_out_dir=None,  # directory to create client logs in
                f_print_logs=False)  # if True - print logs to stdout
# run method on specific host
print("host1 foo_no_args\n\t",
      mhosts.host1.examples.foo_no_args())

# run async method on specific host (by adding <t> to host name)
thread = mhosts.host2t.examples.foo_args_kwargs(1, 2, 3, a = 4, b = 5, c = 6)
# wait finish and get result
print("host2 async foo_args_kwargs\n\t", thread.join())

# foo raising exc
try:
    mhosts.host3.examples.foo_raising_exc()
except Exception as exc:
    print("host3 foo_raising_exc\n\t", exc)

# Run specific method on all hosts one after another

print("all foo_returns_datetime\n\t",
      "\n\t".join(
          f"{k}={v}" for k, v in
          mhosts.all.examples.foo_returns_datetime().items())
      )

# Run specific method on all hosts in parallel

print("all foo_returns_datetime(async)\n\t",
      "\n\t".join(
          f"{k}={v}" for k, v in
          mhosts.allt.examples.foo_returns_datetime().items())
      )

# running method on host corresponging to the current thread name
threading.current_thread().name = "host2"
print("current thread(=host2) run foo_returns_datetime\n\t",
      mhosts.cur.examples.foo_returns_datetime())
# same async
print("same async\n\t",
      mhosts.curt.examples.foo_returns_datetime().join())

input("press for windows examples (requires <pip install pywin32>)")
# run notepad on each host minimized
ret = mhosts.all.os.exec("notepad.exe", wait_finish = False, wnd_minimize = True)
input("started notepad on each host minimized\n\t"
      + "\n\t".join(
          f"{k}={v}" for k, v in
          ret.items())
      )
ret = mhosts.all.os.kill_procs("notepad.exe")
input("killed notepad.exe\n\t"
      + "\n\t".join(
          f"{k}={v}" for k, v in
          ret.items())
      )

# getting dir
print("cur host DIR\n\t",
      mhosts.cur.os.exec("dir", cwd = "C:\\"))
