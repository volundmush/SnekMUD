import sys
from pathlib import Path
from snekmud.db.players.models import PlayerCharacter
from snekmud.typing import Entity
from mudforge.utils import generate_name
from snekmud import components as cm
from snekmud.utils import read_data_file
from snekmud.serialize import deserialize_entity
from snekmud import WORLD, PLAYER_ID
import logging


class Prototype:

    def __init__(self, module, name, data):
        self.module = module
        self.name = name
        self.entities = dict()
        self.data = data


class Module:

    def __init__(self, name: str, path: Path, save_path: Path):
        self.name = sys.intern(name)
        self.maps: dict[str, Entity] = dict()
        self.prototypes: dict[str, Prototype] = dict()
        self.entities: dict[str, Entity] = dict()
        self.path = path
        self.save_path = save_path

    def __str__(self):
        return self.name

    async def load_init(self):
        pass

    async def load_maps(self):
        m_dir = self.path / "maps"
        if not m_dir.exists():
            return

        if not m_dir.is_dir():
            return

        for d in [d for d in m_dir.iterdir() if d.is_file()]:
            key, ext = d.name.split(".", 1)
            data = read_data_file(d)
            if not data:
                continue
            map_ent = WORLD.create_entity()
            WORLD.add_component(map_ent, cm.Name(key))
            self.maps[key] = map_ent
            continue

            grid = cm.GridMap()
            for d in data:
                if "Coordinates" not in data:
                    continue
                coordinates = data.pop("Coordinates")
                room_ent = deserialize_entity(data)
                grid.rooms.add(cm.PointHolder(coordinates, room_ent))

    async def load_prototypes(self):
        p_dir = self.path / "prototypes"
        if not p_dir.exists():
            return

        if not p_dir.is_dir():
            return

        for d in [d for d in p_dir.iterdir() if d.is_file()]:
            key, ext = d.name.split(".", 1)
            data = read_data_file(d)
            if not data:
                continue
            data["Prototype"] = {"module_name": self.name, "prototype": key}
            self.prototypes[key] = Prototype(self, key, data)

    async def load_entities_initial(self):
        e_dir = self.path / "prototypes"
        if not e_dir.exists():
            return

        if not e_dir.is_dir():
            return

        for d in [d for d in e_dir.iterdir() if d.is_file()]:
            key, ext = d.name.split(".", 1)
            data = read_data_file(d)
            if not data:
                continue
            e_ent = deserialize_entity(data)
            self.index_entity(e_ent)

    def index_entity(self, ent: Entity):
        if not (e_id := WORLD.try_component(ent, cm.EntityID)):
            return
        self.prototypes[e_id.prototype].entities[e_id.ent_id] = ent
        self.entities[e_id.ent_id] = ent

    async def load_entities_finalize(self):
        pass

    def assign_id(self, ent: Entity, proto: str, index: bool = True):
        p = self.prototypes[proto]
        new_id = generate_name(proto, p.entities.keys())
        WORLD.add_component(ent, cm.EntityID(module_name=self.name, prototype=proto, ent_id=new_id))
        if index:
            self.entities[new_id] = ent
            p.entities[new_id] = ent
        return new_id
