from typing import Optional, Union, Any, Dict
from weakref import WeakValueDictionary, ref
from rich.text import Text
from snekmud.misc import Sex, Size
from snekmud.commands.base import HasCommandHandler
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

@dataclass_json
@dataclass(slots=True)
class Mobile:
    vnum: int = -1
    character_id: Optional[str] = None
    account_id: Optional[str] = None
    location: Optional[int] = None
    home: Optional[int] = None
    saved_locations: Dict[str, int] = field(default_factory=dict)
    name: Text = field(default=Text("Nameless Mobile"), metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))

class _MobileDriver:

    __slots__ = ["__weakref__", "mobile"]

    def __str__(self):
        return str(self.mobile.name)

class MobilePrototypeDriver(_MobileDriver):

    __slots__ = ["instances"]

    def __init__(self, mobile):
        self.mobile = mobile
        self.instances = dict()

class MobileInstanceDriver(_MobileDriver, HasCommandHandler):

    __slots__ = ["instance_id", "session", "cmd_handler"]

    def __init__(self, mobile, instance_id: str):
        self.mobile = mobile
        self.instance_id = instance_id
        self.session: Optional[ref["Session"]] = None
        self.cmd_handler: Optional["BaseMobileCommandHandler"] = None
        self.location: Optional[ref["Room"]] = None

    def __str__(self):
        return str(self.mobile)

    def is_player(self):
        return self.mobile.character_id is not None

    async def msg(self, line: Optional[Union[str, Text]]=None, text: Optional[Union[str, Text]]=None,
                  source: Optional[Any]=None, system_msg: bool=True, channel=None, gmcp=None,
                  highlighter: str = "null", **kwargs):
        if not self.play_session:
            return
        if not line and not text and not gmcp:
            return
        await self.session(line=line, text=text, source=source, relayed_by=[self, ], system_msg=system_msg,
                                channel=channel, gmcp=None, highlighter=highlighter, **kwargs)