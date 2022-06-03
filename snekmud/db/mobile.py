from typing import Optional, Union, Any
from weakref import WeakValueDictionary, ref
from rich.text import Text
from snekmud.misc import Sex, Size
from snekmud.commands.base import HasCommandHandler


class Mobile(HasCommandHandler):

    __slots__ = ["vnum", "character_id", "location", "saved_locations", "active", "name", "short_desc", "long_desc",
                 "desc", "title", "size", "sex", "gender", "play_session",
                 "cmd_handler"]

    def __init__(self):
        self.vnum: int = -1
        self.character_id: Optional[str] = None
        self.location: Optional[ref["Room"]] = None
        self.saved_locations: WeakValueDictionary[str, ref["Room"]] = WeakValueDictionary()

        # a character that isn't active is in a suspended state. It is loaded into memory, but not participating in the
        # game simulation. It should be stored Nowhere if it isn't active. Do not process buffs/debuffs, tick down timers, etc.
        self.active: bool = False

        self.name: Text = Text("Nameless Mobile")
        self.short_desc: Optional[Text] = None
        self.long_desc: Optional[Text] = None
        self.desc: Optional[Text] = None
        self.title: Optional[Text] = None

        self.size: Size = Size.UNDEFINED
        self.sex: Sex = Sex.OTHER
        self.gender: Sex = Sex.OTHER

        self.play_session: Optional[ref["PlaySession"]] = None

        self.cmd_handler: Optional["BaseMobileCommandHandler"] = None

    def is_player(self):
        return self.character_id is not None

    async def msg(self, line: Optional[Union[str, Text]]=None, text: Optional[Union[str, Text]]=None,
                  source: Optional[Any]=None, system_msg: bool=True, channel=None):
        if not self.play_session:
            return
        if not line and not text:
            return
        await self.play_session(line=line, text=text, source=source, relayed_by=[self, ], system_msg=system_msg,
                                channel=channel)
