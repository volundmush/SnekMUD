from mudforge.services.game import GameService as OldGame
import logging
import snekmud
import mudforge
from pathlib import Path
from snekmud.typing import Entity
from snekmud.utils import read_json_file
from mudforge import CLASSES
from mudforge.utils import import_from_module, lazy_property
from snekmud import COMPONENTS, WORLD

async def broadcast(s: str):
    return
    for c in mudforge.NET_CONNECTIONS.values():
        c.send_line(s)


async def part_broad(s: str):
    return
    for c in mudforge.NET_CONNECTIONS.values():
        c.send_text(s)


class GameService(OldGame):
    mod_path = Path("modules")
    save_root = Path("save")

    async def at_post_module_initial_load(self):
        pass

    @lazy_property
    def modules(self):
        modules = list(snekmud.MODULES.values())
        modules.sort(key=lambda x: x.sort_order)
        return modules

    async def load_initial(self):
        logging.info(f"Loading game database from {self.mod_path}")
        await broadcast(f"Beginning database load...")
        default_module = CLASSES["default_module"]

        for p in [p for p in self.mod_path.iterdir() if p.is_dir()]:
            module_class = default_module
            meta_path = p / "meta.json"
            meta_data = None
            if meta_path.exists() and meta_path.is_file():
                meta_data = read_json_file(meta_path)
                if meta_data and (m_class_path := meta_data.get("class", None)):
                    module_class = import_from_module(m_class_path)
            m = module_class(p.name, p, self.save_root / p.name, meta=meta_data)
            snekmud.MODULES[m.name] = m
        count = len(snekmud.MODULES)

        logging.info(f"Discovered {count} modules!")
        await broadcast(f"Discovered {count} modules!")

    async def load_middle(self):
        for v in self.modules:
            logging.info(f"Module {v}: Loading...")
            await broadcast(f"Module {v}: Loading...")
            await v.load_init()
            await v.load_maps()
            await v.load_prototypes()

    async def load_finish(self):
        await broadcast("Spawning entities...")
        logging.info("Performing initial entity load from database.")
        for v in self.modules:
            await v.load_entities_initial()
        logging.info("Finished initial entity load.")

        logging.info("Finalizing load of entities...")
        for v in self.modules:
            await v.load_entities_finalize()
        logging.info("Finished load!")

    async def game_loop(self):
        pass

    def register_entity(self, ent: Entity, ent_id=None):
        if ent_id is None:
            ent_id = WORLD.component_for_entity(ent, COMPONENTS['EntityID'])
        m = snekmud.MODULES[ent_id.module_name]
        p = m.prototypes[ent_id.prototype]
        m.entities[ent_id.ent_id] = ent
        p.entities[ent_id.ent_id] = ent