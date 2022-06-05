from typing import List, Optional, Dict, Set, Union, Any
from collections import defaultdict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

from snekmud.db.misc import Location, Position, ObjectFlag, WearFlag, ExtraFlag, EntityType
from snekmud.db.misc import Sex, Size, HairLength, HairStyle, HairColor, ObjectType
from snekmud.db.misc import AuraColor, SkinColor, ForeheadAppendage, DistinguishingFeature
from snekmud.db.misc import Coordinates, LocationType, Location, NewLocation, EyeColor

from snekmud.db.sensei import SenseiId, SENSEI_MAP
from snekmud.db.race import RaceId, RACE_MAP
from snekmud.db.room import ExitDir, MoveType

from mudforge.ansi.circle import CircleToRich


@dataclass_json
@dataclass(slots=True)
class Skill:
    level: int = 0
    bonus: int = 0
    perfection: int = 0


@dataclass_json
@dataclass(slots=True)
class ItemData:
    type_flag: ObjectType = ObjectType.JUNK
    values: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    wear_flags: List[WearFlag] = field(default_factory=list)
    extra_flags: List[ExtraFlag] = field(default_factory=list)
    cost: int = 0
    cost_per_day: int = 0


@dataclass_json
@dataclass(slots=True)
class PhysicsData:
    size: Size = Size.UNDEFINED
    weight: int = 0
    height: int = 0


@dataclass_json
@dataclass(slots=True)
class LegacyAppearanceData:
    hair_length: HairLength = HairLength.SHORT
    hair_style: HairStyle = HairStyle.PLAIN
    hair_color: HairColor = HairColor.BLACK
    skin_color: SkinColor = SkinColor.WHITE
    eye_color: EyeColor = EyeColor.BLACK
    forehead_appendage: ForeheadAppendage = ForeheadAppendage.STUBBY
    aura_color: AuraColor = AuraColor.WHITE
    distinguishing_feature: DistinguishingFeature = DistinguishingFeature.EYE


@dataclass_json
@dataclass(slots=True)
class PlayerCharacterData:
    dubs: Dict[str, str] = field(default_factory=dict)
    character_id: Optional[str] = None
    account_id: Optional[str] = None


@dataclass_json
@dataclass(slots=True)
class CharacterData:
    title: Optional[str] = None
    sex: Sex = Sex.OTHER
    race: RaceId = RaceId.UNKNOWN
    legacy_appearance: Optional[LegacyAppearanceData] = None
    sensei: SenseiId = SenseiId.COMMONER
    time: int = 0
    position: Position = Position.STANDING
    skills: Dict[int, Skill] = field(default_factory=dict)
    player: Optional[PlayerCharacterData] = None


@dataclass_json
@dataclass(slots=True)
class Entity:
    entity_key: Union[int, str] = None
    entity_type: EntityType = EntityType.JUNK
    level: int = 0
    name: str = "New Entity"
    description: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    action_description: Optional[str] = None
    ex_description: Dict[str, str] = field(default_factory=dict)
    triggers: List[int] = field(default_factory=list)
    item_data: Optional[ItemData] = None
    character_data: Optional[CharacterData] = None
    locations: Dict[str, int] = field(default_factory=dict)
    physics: Optional[PhysicsData] = None


class _EntityDriver:

    __slots__ = ["__weakref__", "entity"]

    def __init__(self, entity: Entity):
        self.entity = entity

    def __str__(self):
        return CircleToRich(self.entity.name, strip=True)


class EntityPrototypeDriver(_EntityDriver):

    __slots__ = ["instances", "zone", "module"]

    def __init__(self, entity: Entity, zone: Optional["ZoneDriver"]=None, module: Optional["Module"] = None):
        super().__init__(entity)
        self.instances = dict()
        self.zone = zone
        self.module = module

    def to_dict(self):
        return self.entity.to_dict()

    def to_json(self):
        return self.entity.to_json()


class EntityInstanceDriver(_EntityDriver):

    __slots__ = ["instance_id", "prototype", "persistent"]

    def __init__(self, entity: Entity, instance_id: str, prototype: EntityPrototypeDriver, persistent: bool = False):
        super().__init__(entity)
        self.instance_id = instance_id
        self.prototype = prototype
        self.persistent = persistent

    def find_location(self, loc_type: LocationType, coord: Coordinates):
        return None
