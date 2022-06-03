import time
from typing import List, Optional, Dict, Any, Union
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum


class Session:

    def __init__(self):
        self.connections: Optional[WeakValueDictionary[str, ref["Connection"]]] = WeakValueDictionary()
        self.account: Optional[ref["Account"]] = None
        self.character: Optional[ref["Mobile"]] = None
        self.puppet: Optional[ref["Mobile"]] = None
        self.created = time.time()
        self.last_user_input = time.time()

    def get_idle_time(self):
        return self.last_user_input - self.created

    def get_conn_time(self):
        return time.time() - self.created

    async def msg(self, line: Optional[Union[str, Text]]=None, text: Optional[Union[str, Text]]=None,
                  source: Optional[Any]=None, relayed_by: Optional[List[Any]]=None, system_msg: bool=True,
                  channel=None, gmcp=None, highlighter: str = "null", **kwargs):
        if not line and not text and not gmcp:
            return
        if relayed_by:
            relayed_by.append(self)
        else:
            relayed_by = [self, ]
        for k, v in self.connections.items():
            await v.msg(line=line, text=text, source=source, relayed_by=relayed_by, system_msg=system_msg,
                        channel=channel, gmcp=gmcp, highlighter=highlighter, **kwargs)

    async def update(self, tick: int):
        """
        Called every tick.
        """
