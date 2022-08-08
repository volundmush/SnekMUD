"""
Contains commands which ought to be available to all Connections while they're authenticated.
"""

import os
import sys
import re
import snekmud
import time
import traceback
import asyncio

from .base import Command, ConnectionCommandHandler
from snekmud.exceptions import CommandError
from snekmud.db.accounts.models import Account

from mudforge.startup import copyover
import mudforge

class _UniversalCmd(Command):
    main_category = "connection"
    sub_categories = ["universal"]

class CmdCopyover(_UniversalCmd):
    name = "@copyover"
    aliases = ["@reload", "@hotboot", "@restart"]
    @classmethod
    async def access(cls, **kwargs) -> bool:
        if (acc := kwargs.get("account")):
            return acc.is_superuser
        return False

    async def execute(self):
        for c in mudforge.NET_CONNECTIONS.values():
            c.send_line("The universe unravels into chaos as a copyover commences.")
        await asyncio.sleep(0.2)
        copyover()


class CmdPy(_UniversalCmd):
    """
    execute a snippet of python code
    Usage:
      @py [cmd]
      @py/edit
      @py/time <cmd>
      @py/clientraw <cmd>
      @py/noecho
    Switches:
      time - output an approximate execution time for <cmd>
      edit - open a code editor for multi-line code experimentation
      clientraw - turn off all client-specific escaping. Note that this may
        lead to different output depending on prototocol (such as angular brackets
        being parsed as HTML in the webclient but not in telnet clients)
      noecho - in Python console mode, turn off the input echo (e.g. if your client
        does this for you already)
    Without argument, open a Python console in-game. This is a full console,
    accepting multi-line Python code for testing and debugging. Type `exit()` to
    return to the game. If Evennia is reloaded, the console will be closed.
    Enter a line of instruction after the 'py' command to execute it
    immediately.  Separate multiple commands by ';' or open the code editor
    using the /edit switch (all lines added in editor will be executed
    immediately when closing or using the execute command in the editor).
    A few variables are made available for convenience in order to offer access
    to the system (you can import more at execution time).
    Available variables in py environment:
      self, me                   : caller
      here                       : caller.location
      evennia                    : the evennia API
      inherits_from(obj, parent) : check object inheritance
    You can explore The evennia API from inside the game by calling
    the `__doc__` property on entities:
        py evennia.__doc__
        py evennia.managers.__doc__
    |rNote: In the wrong hands this command is a severe security risk.  It
    should only be accessible by trusted server admins/superusers.|n
    """
    name = "@py"
    aliases = ["@!"]
    help_category = "System"

    @classmethod
    async def access(cls, **kwargs) -> bool:
        if (acc := kwargs.get("account")):
            return acc.is_superuser
        return False

    async def execute(self):
        """hook function"""

        pycode = self.args

        available_vars = dict(snekmud.PY_DICT)
        available_vars.update(self.kwargs)
        available_vars.update({"self": self.connection, "me": self.connection})

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            # reroute standard output to game client console
            sys.stdout = self.connection
            sys.stderr = self.connection

            print(f">>> {pycode}")

            try:
                pycode_compiled = compile(pycode, "", "eval")
            except Exception:
                pycode_compiled = compile(pycode, "", "exec")

            measure_time = True

            duration = ""
            if measure_time:
                t0 = time.time()
                ret = eval(pycode_compiled, {}, available_vars)
                t1 = time.time()
                duration = " (runtime ~ %.4f ms)" % ((t1 - t0) * 1000)
            else:
                ret = eval(pycode_compiled, {}, available_vars)
            print(ret)
            if duration:
                print(duration)

        except Exception:
            errlist = traceback.format_exc().split("\n")
            if len(errlist) > 4:
                errlist = errlist[4:]
            ret = "\n".join("%s" % line for line in errlist if line)
            print(ret)
        finally:
            # return to old stdout
            sys.stdout = old_stdout
            sys.stderr = old_stderr