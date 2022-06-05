import orjson
from pathlib import Path
import snekmud
from snekmud.db.misc import EntityType
import logging


class Module:

    def __init__(self, path: Path, system: bool = False):
        self.path = path
        self.system = system
        self.prototypes = dict()
        self.name = str(path.name)

    async def load_data(self):
        p_file = self.path / "maps.json"
        if p_file.exists():
            await self.load_maps(p_file)

        p_file = self.path / "prototypes.json"
        if p_file.exists():
            await self.load_prototypes(p_file)

    async def load_maps(self, p: Path):
        pass

    async def load_prototypes(self, p: Path):
        entity_class = snekmud.CLASSES["entity"]
        with p.open(mode="rb") as f:
            data = orjson.loads(f.read())
            for k, v in data.items():
                e_type = EntityType(v.get("entity_type", EntityType.JUNK))
                proto_class = e_type.get_proto_class()
                v["entity_key"] = k
                ent = entity_class.from_dict(v)
                proto = proto_class(ent, module=self)
                self.prototypes[k] = proto
