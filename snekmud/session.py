from typing import List, Optional, Dict, Any, Union
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum


class PlaySession:

    def __init__(self):
        self.connections: Optional[WeakValueDictionary[str, ref["Connection"]]] = WeakValueDictionary()
        self.account: Optional[ref["Account"]] = None
        self.character: Optional[ref["Mobile"]] = None
        self.puppet: Optional[ref["Mobile"]] = None

    async def msg(self, line: Optional[Union[str, Text]]=None, text: Optional[Union[str, Text]]=None,
                  source: Optional[Any]=None, relayed_by: Optional[List[Any]]=None, system_msg: bool=True,
                  channel=None):
        if not line and not text:
            return
        if relayed_by:
            relayed_by.append(self)
        else:
            relayed_by = [self, ]
        for k, v in self.connections.items():
            await v.msg(line=line, text=text, source=source, relayed_by=relayed_by, system_msg=system_msg,
                        channel=channel)