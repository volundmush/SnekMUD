from typing import List, Optional, Dict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from .misc import Sex, Size


class Mobile:

    def __init__(self):
        self.vnum: int = -1
        self.is_player: bool = False
        self.location: Optional[ref["Room"]] = None
        self.voided_location: Optional[ref["Room"]] = None
        self.active: bool = False

        self.name: Text = Text("Nameless Mobile")
        self.short_desc: Optional[Text] = None
        self.long_desc: Optional[Text] = None
        self.desc: Optional[Text] = None
        self.title: Optional[Text] = None

        self.size: Size = Size.UNDEFINED
        self.sex: Sex = Sex.OTHER
        self.gender: Sex = Sex.OTHER

        self.session: Optional[ref["PlaySession"]] = None