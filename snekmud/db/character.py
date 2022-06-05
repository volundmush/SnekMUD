from typing import Optional, Union, Any, Dict, Set, List
from weakref import ref, WeakValueDictionary
from rich.text import Text
from mudforge.ansi.circle import CircleToRich

import snekmud
from snekmud.commands.base import HasCommandHandler

from rich.table import Table
from rich.box import ASCII2
from snekmud.db.room import ExitDir, MoveType, RoomFlag
from snekmud.db.entity import EntityInstanceDriver, EntityPrototypeDriver
from snekmud.db.misc import Sex


class CharacterPrototypeDriver(EntityPrototypeDriver):
    pass


class CharacterInstanceDriver(EntityInstanceDriver, HasCommandHandler):

    __slots__ = ["instance_id", "session", "cmd_handler", "race", "sensei", "race_spoof"]

    def __init__(self, entity, instance_id: str, prototype: EntityPrototypeDriver, persistent: bool = False):
        super().__init__(entity, instance_id, prototype, persistent=persistent)
        self.session: Optional[ref["Session"]] = None
        self.cmd_handler: Optional["BaseCharacterCommandHandler"] = None
        self.location: Optional[ref["RoomDriver"]] = None
        self.carrying: List[ref["ItemInstanceDriver"]] = list()
        self.equipment: Dict[int, ref["ItemInstanceDriver"]] = WeakValueDictionary()
        self.wait_cmd_ticks: int = 0
        self.race = None
        self.race_spoof = None
        self.sensei = None
        self.builder_vision: bool = False

    def is_player(self):
        return bool(self.entity.character_data.player)

    async def process_command_entry(self, cmd):
        if not self.cmd_handler:
            return
        cmd.character = self
        self.cmd_handler.pending_command_queue.append(cmd)

    async def msg(self, line: Optional[Union[str, Text]]=None, text: Optional[Union[str, Text]]=None,
                  source: Optional[Any]=None, system_msg: bool=True, channel=None, gmcp=None,
                  highlighter: str = "null", **kwargs):
        if not self.session:
            return
        if not line and not text and not gmcp:
            return
        await self.session.msg(line=line, text=text, source=source, relayed_by=[self, ], system_msg=system_msg,
                                channel=channel, gmcp=None, highlighter=highlighter, **kwargs)

    async def render_room(self, room: "RoomDriver" = None):
        if room is None:
            room = self.location
        if not room:
            return Text("There is nothing to see!")
        flags = room.room.room_flags
        out = list()
        sep = "O----------------------------------------------------------------------O"
        out.append(sep)
        out.append(Text("Location: ") + CircleToRich(room.room.name))
        planet_flags = [r for r in flags if r.is_legacy_planet()]
        if planet_flags:
            out.append(f"Planet: {str(planet_flags[0].name.capitalize())}")
        out.append(f"Gravity: {room.get_gravity_fancy()}")
        if self.builder_vision:
            flag_names = ' '.join(r.name for r in flags)
            flag_display = f"[ {flag_names} ]"
            out.append(f"Flags: {flag_display} Sector: [ {room.room.sector_type.name} ] Vnum: [{room.room.vnum:>8}]")
        out.append(sep)
        out.append(CircleToRich(room.room.description))
        out.append(sep)

        inhab_copy = set(room.characters)
        if self in inhab_copy:
            inhab_copy.remove(self)

        if inhab_copy or room.objects:
            contents_table = Table(title="Contents", safe_box=True, box=ASCII2)
            contents_table.add_column("Inhabitants")
            contents_table.add_column("Things")

            inhab = Text("\n").join([CircleToRich(i.entity.name) for i in inhab_copy])
            objects = Text("\n").join([CircleToRich(o.entity.name) for o in room.objects])
            contents_table.add_row(inhab, objects)
            out.append(contents_table)

        if room.exits:
            out.append("Exits: ")
            out.append(", ".join([d.abbr() for d in room.exits.keys()]))
        return out

    async def can_move_to(self, destination: Union[None, "RoomDriver"] = None) -> (bool, str):
        if not destination:
            return False, "Destination does not exist."
        return True, ''

    async def move_to(self, destination: Union[None, "RoomDriver"] = None, via_exit: Optional["ExitDriver"] = None,
                      direction: ExitDir = ExitDir.UNKNOWN, pay_costs: bool = True,
                      move_type: MoveType = MoveType.UNKNOWN, look_after_move: bool = True,
                      announce_location: bool = True, announce_destination: bool = True):

        location = self.location
        if location and location == destination:
            if look_after_move and location:
                rendered = await self.render_room(location)
                await self.msg(line=rendered, system_msg=True)
            return

        if location is None:
            announce_location = False

        if destination is None:
            announce_destination = False
            if announce_location:
                pass  # TODO: make the announce at location
            await self.do_move(destination)
            return

        if announce_location:
            pass
        await self.do_move(destination)
        if announce_destination:
            pass
        if look_after_move:
            rendered = await self.render_room(destination)
            await self.msg(line=rendered, system_msg=True)

    async def do_move(self, destination: Union[None, "RoomDriver"] = None):
        location = self.location
        self.location = destination
        if location:
            await location.character_leave(self)
        if destination:
            await destination.character_enter(self)

    async def get_login_room(self) -> (Union["RoomDriver", None], str):
        # First, check for a saved logout location.
        if (logout_id := self.entity.locations.get("logout", None)):
            if (found := snekmud.ROOMS.get(logout_id, None)):
                return found, ''

        # If that fails, try their home location.

        if (home_id := self.entity.locations.get("home", None)):
            if (found := snekmud.ROOMS.get(logout_id, None)):
                return found, "You find yourself back at home, as your previous location no longer exists."

        # Okay that still didn't work? Then we can only fall back to the global starting room.
        if (global_start := snekmud.CONFIG["rooms"]["global_start"]):
            if (found := snekmud.ROOMS.get(global_start, None)):
                return found, "You find yourself in this place, as none other existed to place you."

        # Okay, something really goofed.
        return None, "Cannot find a safe login room. Contact staff."

    async def update(self, current_tick: int):
        if self.cmd_handler:
            await self.cmd_handler.update(current_tick)

    def you_will_know_my_name(self):
        if not self.is_player():
            return True
        if not self.session and self.session.get_slevel() > 0:
            return True
        return False

    def i_will_know_your_name(self):
        if not self.is_player():
            return True
        if self.session and self.session.get_slevel() > 0:
            return True
        return False

    def can_see(self, other: "CharacterInstanceDriver"):
        return True

    def get_race_name(self, ignore_spoof=False):
        if ignore_spoof:
            return self.race.name
        if self.race_spoof:
            return self.race_spoof.name
        return self.race.name

    def get_name_of(self, other: "CharacterInstanceDriver"):
        if self == other:
            return other.entity.name

        if not self.can_see(other):
            return "Someone"

        if self.i_will_know_your_name() or other.you_will_know_my_name():
            return other.entity.name

        if other.is_player():
            if (dub := self.entity.character_data.player.dubs.get(other.entity.character_data.character_id, None)):
                return dub
        return other.get_race_name()

    def get_short_of(self, other: "CharacterInstanceDriver"):
        pass

    def get_sex(self):
        return Sex(self.entity.character_data.sex)