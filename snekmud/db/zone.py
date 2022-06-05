from pathlib import Path
import orjson
import logging
from typing import List, Set, Dict
from collections import defaultdict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
import snekmud

@dataclass_json
@dataclass(slots=True)
class ResetCommand:
    command: str = ""
    if_flag: bool = False
    arg1: int = 0
    arg2: int = 0
    arg3: int = 0
    arg4: int = 0
    arg5: int = 0
    line: int = -1
    sarg1: str = ""
    sarg2: str = ""


class ZoneFlag(IntFlag):
    CLOSED = 0
    NOIMMORT = 1
    QUEST = 2
    DBALLS = 3


@dataclass_json
@dataclass(slots=True)
class Zone:
    vnum: int = -1
    name: str = "New Zone"
    lifespan: int = 30
    start_vnum: int = -1
    end_vnum: int = -1
    reset_mode: int = 2
    reset_commands: List[ResetCommand] = field(default_factory=list)
    zone_flags: Set[ZoneFlag] = field(default_factory=set)
    builders: List[str] = field(default_factory=list)
    min_level: int = 0
    max_level: int = 99999999999


class ZoneDriver:

    __slots__ = ["data", "rooms", "mobiles", "objects", "triggers", "shops", "guilds", "__weakref__", "age",
                 "entity_instances", "path", "zone"]

    def __init__(self, path: Path, zone):
        self.zone = zone
        self.path = path
        self.data = zone
        self.age: int = 0
        self.rooms: WeakValueDictionary[int, ref["RoomDriver"]] = WeakValueDictionary()
        self.mobiles: WeakValueDictionary[int, ref["CharacterPrototypeDriver"]] = WeakValueDictionary()
        self.objects: WeakValueDictionary[int, ref["ItemPrototypeDriver"]] = WeakValueDictionary()
        self.triggers: WeakValueDictionary[int, ref["Trigger"]] = WeakValueDictionary()
        self.shops: WeakValueDictionary[int, ref["ShopDriver"]] = WeakValueDictionary()
        self.guilds: WeakValueDictionary[int, ref["GuildDriver"]] = WeakValueDictionary()

        self.entity_instances: WeakSet["EntityInstanceDriver"] = WeakSet()

    async def load_thing(self, filename: str, method, use_class):
        j_file = self.path / filename
        if j_file.exists() and j_file.is_file():
            with j_file.open(mode="r") as f:
                entities = use_class.schema().loads(f.read(), many=True)
            await method(entities)

    async def load_data(self):
        room_class = snekmud.CLASSES["room"]
        entity_class = snekmud.CLASSES["entity"]
        #await self.load_thing("triggers.json", self.load_triggers)
        await self.load_thing("rooms.json", self.load_rooms, room_class)
        logging.info(f"Loaded {len(self.rooms)} rooms.")
        await self.load_thing("objects.json", self.load_objects, entity_class)
        logging.info(f"Loaded {len(self.objects)} objects.")
        await self.load_thing("mobiles.json", self.load_mobiles, entity_class)
        logging.info(f"Loaded {len(self.mobiles)} mobiles.")

    async def load_triggers(self, entities):
        pass

    async def load_rooms(self, entities):
        room_driver = snekmud.CLASSES["room_driver"]

        for e in entities:
            room = room_driver(e, self)
            snekmud.ROOMS[e.vnum] = room
            self.rooms[e.vnum] = room

    async def load_objects(self, entities):
        obj_driver = snekmud.PROTOTYPE_CLASSES["item"]

        for e in entities:
            obj = obj_driver(e, zone=self)
            snekmud.OBJECT_PROTOTYPES[e.entity_key] = obj
            self.objects[e.entity_key] = obj

    async def load_mobiles(self, entities):
        mob_driver = snekmud.PROTOTYPE_CLASSES["character"]

        for e in entities:
            obj = mob_driver(e, zone=self)
            snekmud.MOBILE_PROTOTYPES[e.entity_key] = obj
            self.mobiles[e.entity_key] = obj

    async def save_to_file(self, data, filename):
        out_items = list(data.values())
        if not out_items:
            return
        item = out_items[0]
        print(f"TEST DUMP OF: {item.entity.entity_key}: {item.entity}")
        print(item.entity.to_json())
        j_file = self.path / filename
        print(f"Attempting to save: {j_file.absolute()}")
        out_data = item.entity.__class__.schema().dumps(out_items, many=True)
        with j_file.open(mode="w") as f:
            f.write(out_data)

    async def save_all(self):
        if not self.path.exists():
            self.path.mkdir(parents=True, exist_ok=True)

        for d, n in [(self.triggers, "triggers.json"),
                     (self.mobiles, "mobiles.json"), (self.rooms, "rooms.json"),
                     (self.objects, "objects.json")]:
            await self.save_to_file(d, n)

    async def setup(self):
        pass
