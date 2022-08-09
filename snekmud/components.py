import typing
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from enum import IntEnum
import kdtree
import sys
from mudforge.utils import lazy_property
from mudrich.evennia import EvenniaToRich, strip_ansi
import snekmud
from snekmud.serialize import deserialize_entity, serialize_entity

from snekmud.typing import Entity, GridCoordinates, SpaceCoordinates


@dataclass_json
@dataclass
class _Save:

    def should_save(self) -> bool:
        return True

    def save_name(self) -> str:
        return str(self.__class__.__name__)

    def export(self):
        return self.to_dict()

    @classmethod
    def deserialize(cls, data: typing.Any, ent: Entity):
        return cls.from_dict(data)

    def at_post_deserialize(self, ent):
        pass

@dataclass_json
@dataclass
class _NoSave(_Save):

    def should_save(self) -> bool:
        return False


@dataclass_json
@dataclass
class InGame(_NoSave):
    pass


@dataclass_json
@dataclass
class PendingRemove(_NoSave):
    pass


@dataclass_json
@dataclass
class IsPersistent(_NoSave):
    pass


@dataclass_json
@dataclass
class MetaTypes(_Save):
    types: list[str] = field(default_factory=list)


@dataclass_json
@dataclass
class Prototype(_Save):
    module_name: str = ""
    prototype: str = ""


@dataclass_json
@dataclass
class EntityID(Prototype):
    ent_id: str = ""


@dataclass_json
@dataclass
class PlayerCharacter(_Save):
    player_id: int = -1


@dataclass_json
@dataclass
class NPC(_Save):
    pass


@dataclass_json
@dataclass
class AccountOwner(_Save):
    account_id: int = 0


@dataclass_json
@dataclass
class InInventory(_NoSave):
    holder: Entity = -1


@dataclass_json
@dataclass
class WearSlots(_Save):
    slots: list[str] = field(default_factory=list)


@dataclass_json
@dataclass
class Equipped(_NoSave):
    holder: Entity = -1
    category: str = None
    slot: str = None


@dataclass_json
@dataclass
class Inventory(_Save):
    inventory: list[Entity] = field(default_factory=list)

    def should_save(self) -> bool:
        return bool(self.inventory)

    def export(self):
        return [serialize_entity(e) for e in self.inventory]

    @classmethod
    def deserialize(cls, data: typing.Any, ent: Entity):
        o = cls()
        for d in data:
            e = deserialize_entity(d, register=True)
            snekmud.WORLD.add_component(e, InInventory(holder=ent))
            o.inventory.append(e)
        return o


@dataclass_json
@dataclass
class Equipment(_Save):
    equipment: dict[str, typing.Type["EquipSlot"]] = field(default_factory=dict)

    def should_save(self) -> bool:
        return bool(self.equipment)

    def export(self):
        return [(v.category, k, serialize_entity(v.item)) for k, v in self.equipment.items()]

    @classmethod
    def deserialize(cls, data: typing.Any, ent: Entity):
        o = cls()
        for category, key, item in data:
            e = deserialize_entity(item)
            snekmud.WORLD.add_component(e, Equipped(holder=ent, category=category, slot=key))
            o.equipment[key] = snekmud.EQUIP_SLOTS[category][key](e)
        return o

    def all(self):
        for x in self.equipment.values():
            yield x.item


@dataclass_json
@dataclass
class SaveInRoom(EntityID):
    coordinates: GridCoordinates = field(default_factory=lambda: [0, 0, 0])


@dataclass_json
@dataclass
class InRoom(_Save):
    holder: Entity = -1

    def should_save(self) -> bool:
        return snekmud.WORLD.entity_exists(self.holder)

    def save_name(self) -> str:
        return "SaveInRoom"

    def export(self):
        data = {}
        if (ent_data := snekmud.WORLD.try_component(self.holder, EntityID)):
            data.update(ent_data.to_dict())
        return data


class PointHolder:

    def __init__(self, coordinates: typing.Union[GridCoordinates, SpaceCoordinates], data: typing.Optional[typing.Any] = None):
        self.coordinates = coordinates
        self.data = data

    def __len__(self):
        return len(self.coordinates)

    def __getitem__(self, i):
        return self.coordinates[i]

    def __repr__(self):
        return f"Item({self.coordinates},  {self.data})"


@dataclass
class InSpace:
    space_sector: Entity = -1


@dataclass
class GridMap:
    rooms: kdtree.Node = field(default_factory=lambda: kdtree.create(dimensions=3))


@dataclass
class SpaceMap:
    contents: kdtree.Node = field(default_factory=lambda: kdtree.create(dimensions=3))


@dataclass_json
@dataclass
class _ModBase(_Save):

    @classmethod
    def category(cls):
        return cls.__name__

    @classmethod
    def find(cls, check):
        if isinstance(check, int):
            return snekmud.MODIFIERS_ID[cls.category()].get(check, None)
        elif isinstance(check, str):
            return snekmud.MODIFIERS_NAMES[cls.category()].get(check, None)


@dataclass_json
@dataclass
class _SingleModifier(_ModBase):
    modifier: "Modifier"

    def export(self):
        return self.modifier.modifier_id

    @classmethod
    def deserialize(cls, data: typing.Any, ent):
        if (found := cls.find(data)):
            return cls(modifier=found(ent))
        raise Exception(f"Cannot locate {str(cls)} {data}")

    def all(self):
        if self.modifier:
            return [self.modifier]
        return []


@dataclass_json
@dataclass
class _MultiModifiers(_ModBase):
    modifiers: dict[str, typing.Any] = field(default_factory=dict)

    def should_save(self) -> bool:
        return bool(self.modifiers)

    def export(self):
        return list(self.modifiers.keys())

    @classmethod
    def deserialize(cls, data: typing.Any, ent):
        o = cls()
        for i in data:
            if (found := cls.find(i)):
                m = found(ent)
                o.modifiers[str(m)] = m

    def all(self):
        self.modifiers.values()


class _StringBase(_Save):
    rich_cache = dict()

    def should_save(self) -> bool:
        return bool(self.plain)

    def __init__(self, s: str):
        self.color = sys.intern(s)
        if self.color not in self.rich_cache:
            self.rich_cache[self.color] = EvenniaToRich(s)

    def __str__(self):
        return self.plain


    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.color}>"

    @property
    def plain(self):
        return self.rich.plain

    @lazy_property
    def rich(self):
        return self.rich_cache[self.color]

    def __rich_console__(self, console, options):
        return self.rich.__rich_console__(console, options)

    def __rich_measure__(self, console, options):
        return self.rich.__rich_measure__(console, options)

    def render(self, console, end: str = ""):
        return self.rich.render(console, end=end)

    def export(self):
        return self.color

    @classmethod
    def deserialize(cls, data: typing.Any, ent):
        return cls(data)


class Name(_StringBase):
    pass


class Description(_StringBase):
    pass


class ShortDescription(_StringBase):
    pass


class LongDescription(_StringBase):
    pass


class ActionDescription(_StringBase):
    pass


@dataclass_json
@dataclass
class ExDescriptions(_Save):
    ex_descriptions: list[typing.Tuple[Name, Description]] = field(default_factory=list)

    def should_save(self) -> bool:
        return bool(self.ex_descriptions)

    def export(self):
        return [(key.export(), desc.export()) for (key, desc) in self.ex_descriptions]

    @classmethod
    def deserialize(cls, data: typing.Any, ent):
        o = cls()
        for k, d in data:
            o.ex_descriptions.append((Name(k), Description(d)))
        return o


class HasSession(_NoSave):

    def __init__(self, session):
        self.session = session


@dataclass_json
@dataclass
class HasCmdHandler(_NoSave):
    cmdhandler: "Parser" = None
    cmdhandler_name: str = None
    entity: Entity = None

    async def set_cmdhandler(self, cmdhandler: str, **kwargs):
        if not (p := snekmud.CMDHANDLERS["Entity"].get(cmdhandler, None)):
            self.send(line=f"ERROR: CmdHandler {cmdhandler} not found for GameSessions, contact staff")
            return
        if self.cmdhandler:
            await self.cmdhandler.close()
        self.cmdhandler = p(self, **kwargs)
        self.cmdhandler_name = cmdhandler
        await self.cmdhandler.start()

    async def process_input_text(self, data: str):
        if not self.cmdhandler:
            await self.set_cmdhandler("Play")
        await self.cmdhandler.parse(data)

    def send(self, **kwargs):
        if (sess := snekmud.WORLD.try_component(self.entity, snekmud.COMPONENTS["HasSession"])):
            if sess.session:
                sess.session.handler.send(**kwargs)

    def at_post_deserialize(self, ent):
        self.entity = ent


class Receiver(_NoSave):
    entity: Entity = None

    def at_post_deserialize(self, ent):
        self.entity = ent

    def receive(self, msg: str, from_ent: Entity, msg_type=None, **kwargs):
        self.send(msg)

    def send(self, msg):
        if (sess := snekmud.WORLD.try_component(self.entity, snekmud.COMPONENTS["HasSession"])):
            if sess.session:
                sess.session.handler.send(line=msg)