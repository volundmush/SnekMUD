from typing import List, Optional, Dict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum


class PlaySession:

    def __init__(self):
        self.connections: Optional[WeakValueDictionary[str, ref["Connection"]]] = WeakValueDictionary()
        self.account: Optional[ref["Account"]] = None
        self.character: Optional[ref["Mobile"]] = None
        self.puppet: Optional[ref["Mobile"]] = None