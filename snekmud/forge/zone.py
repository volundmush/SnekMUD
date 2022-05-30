from typing import List
from weakref import WeakValueDictionary, ref
from rich.text import Text
from enum import IntFlag


class ResetCommand:

    __slots__ = ["command", "if_flag", "args", "line", "sargs", "__weakref__"]

    def __init__(self):
        self.command: str = ""
        self.if_flag: bool = False
        self.args: List[int] = list()
        self.line: int = -1
        self.sargs: List[str] = list()


class ZoneFlag(IntFlag):
    pass


class Zone:

    __slots__ = ["vnum", "name", "lifespan", "age", "bottom_vnum", "top_vnum", "reset_mode",
                 "reset_commands", "flags", "rooms", "mobiles", "things", "triggers", "shops",
                 "guilds"]

    def __init__(self):
        self.vnum = -1
        self.name = Text("New Zone")
        self.lifespan = 30
        self.age = -1
        self.bottom_vnum = -1
        self.top_vnum = -1
        self.reset_mode = 2
        self.reset_commands: List[ResetCommand] = list()
        self.flags: int = 0
        self.rooms: WeakValueDictionary[int, ref["Room"]] = WeakValueDictionary()
        self.mobiles: WeakValueDictionary[int, ref["Mobile"]] = WeakValueDictionary()
        self.things: WeakValueDictionary[int, ref["Thing"]] = WeakValueDictionary()
        self.triggers: WeakValueDictionary[int, ref["Trigger"]] = WeakValueDictionary()
        self.shops: WeakValueDictionary[int, ref["Shop"]] = WeakValueDictionary()
        self.guilds: WeakValueDictionary[int, ref["Guild"]] = WeakValueDictionary()

