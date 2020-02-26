import inspect
from typing import Union, Dict
import subprocess
from datetime import datetime
import time


def all_static(cls):
    """class decorator, makes all methods static, including nested"""
    for name, m in inspect.getmembers(cls, inspect.isfunction):
        if name.startswith("_"):
            continue
        setattr(cls, name, staticmethod(m))
    for name, m in inspect.getmembers(cls, inspect.isclass):
        if name.startswith("_"):
            continue
        setattr(cls, name, all_static(m))
    return cls


@all_static
class RPCResolver:
    """Static RPC methods resolver

    After being inherited by RPCClient method can be called from client
    and resolved on server-side
    """

    class examples:

        def foo_no_args():
            return "foo_no_args"

        def foo_args_kwargs(*args, **kwargs):
            return f"got args={args},kwargs={kwargs}"

        def foo_raising_exc():
            raise Exception("Something bad happend")

        def foo_returns_datetime():
            time.sleep(1)
            return datetime.now()

    def is_alive():
        """indicates if RPC server accessible"""
        return True

    class os:

        def exec(args: Union[str, list], *, wait_finish: bool = True,
                 ignore_errors: bool = False, wnd_minimize: bool = False, cwd: str = None,
                 env: dict = None, as_text: bool = True) -> dict:
            """Execute process

            Args:
                :args: str as whole command line or list of args
                :wait_finish: if False process starts only, method returns PID of started proc, if True waits process to finish, returns, PID,stdout,and return code
                :ignore_errors: if False and return_code!=0 - raises an Exception, otherwise not
                :wnd_minimize: run process minimized, has effect for Windows only
                :cwd: changes current working dir for running process
                :env: environmental variables, see subprocess.Popen docs for details
                :as_text: if True process stdout returned as utf-8 text, otherwise it's a bytes

            Returns:
                dict{pid,output,return_code}
            """
            import win32con
            mArgs = {
                "creationflags": subprocess.CREATE_NEW_CONSOLE,
                "bufsize": -1,
                "cwd": cwd,
                "env": env,
                "shell": True,
            }
            if as_text:
                mArgs.update({
                    "text": True,
                    "encoding": "utf-8",
                    "errors": "ignore"
                })
            if wait_finish:
                mArgs.update({
                    "stdin": subprocess.PIPE,
                    "stdout": subprocess.PIPE,
                    "stderr": subprocess.PIPE,
                })
            if wnd_minimize:
                mArgs["shell"] = False  # minimization does not work when shell=True
                mArgs["startupinfo"] = subprocess.STARTUPINFO(
                    dwFlags = subprocess.STARTF_USESHOWWINDOW,
                    wShowWindow = win32con.SW_MINIMIZE
                )

            oProc = subprocess.Popen(args, **mArgs)
            pid = oProc.pid
            return_code = None
            output = None
            if wait_finish:
                sOut, sErr = oProc.communicate()
                return_code = oProc.returncode
                if return_code != 0 and not ignore_errors:
                    sErrDesc = "Error executing command:\r\n"
                    sErrDesc += args + '\r\n'
                    if sOut:
                        sErrDesc += "Output:\r\n" + str(sOut) + '\r\n'
                    if sErr:
                        sErrDesc += "Errors:\r\n" + str(sErr) + '\r\n'
                    raise Exception(sErrDesc)
                output = str(sOut)
            return dict({
                "pid": pid,
                "output": output,
                "return_code": return_code,
            })

        def kill_procs(procs: Union[list, str, int], exclude_pid: int = 0):
            """Kills processes on Windows

            Args:
                :procs: process name, pid, or list of those
                :exclude_pid: pid to exclude when killing procs

            """
            import win32api
            from win32com import client
            from pythoncom import (CoInitializeEx, CoUninitialize,
                                   COINIT_MULTITHREADED)

            if not isinstance(procs, list):
                procs = [procs]
            my_pid = win32api.GetCurrentProcessId()
            CoInitializeEx(COINIT_MULTITHREADED)
            try:
                wmg = client.GetObject(
                    r"winmgmts:{impersonationLevel=impersonate}!\\.\root\cimv2")
                objLoc = client.Dispatch("wbemscripting.swbemlocator")
                objLoc.Security_.privileges.addasstring("sedebugprivilege", True)
                query = r"SELECT * FROM Win32_Process WHERE"
                for i, procName in enumerate(procs):
                    assert isinstance(procName, (int, str)), f"{procName}"
                    query += r" {}{} = '{}'".format("" if i == 0 else "OR ",
                                                    "Name" if isinstance(
                                                        procName, str) else "ProcessID",
                                                    procName)
                for proc in wmg.ExecQuery(query):
                    if proc.ProcessID in [my_pid, exclude_pid]:
                        continue
                    proc.Terminate
                    del proc

                del objLoc
                del wmg
            finally:
                CoUninitialize()

    class svn:

        def update():
            pass

        def revert():
            pass

        def cleanup():
            pass

    class git:

        def fetch():
            pass

        def pull():
            pass

        def push():
            pass

    class vm:

        def find_machine(vm_name):
            pass

        def find_machine_re(pattern):
            pass

        def make_diff_vm(vm_name):
            pass

        def conf_debug_pipe(vm_name):
            pass

        def rename(vm_name, new_name):
            pass

        def switch_cable(vm_name, state):
            pass

        def connect_udp_tunnel(vm_name, dest, dport, sport):
            pass

        def start(vm_name):
            pass

        def set_property(vm_name, prop, value, type_):
            pass

        def get_property(vm_name, prop):
            pass

        def wait_shutdown(vm_name):
            pass

        def power_off(vm_name):
            pass

        def wait_stopped(vm_name):
            pass

        def wait_ready(vm_name):
            pass

        def destroy(vm_name):
            pass

        def exec(vm_name, executable, args = [], success_codes = [0], wait = True):
            pass


