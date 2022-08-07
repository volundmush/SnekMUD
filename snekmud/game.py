from mudforge.services.game import GameService as OldGame
import logging
import snekmud
from pathlib import Path
from snekmud.typing import Entity
from snekmud.utils import read_yaml_file
from mudforge import CLASSES
from mudforge.utils import import_from_module
from snekmud import COMPONENTS, WORLD


class GameService(OldGame):
    mod_path = Path("modules")
    save_root = Path("save")

    async def at_post_module_initial_load(self):
        pass

    async def on_start(self):
        logging.info(f"Loading game database from {self.mod_path}")
        default_module = CLASSES["default_module"]

        for p in [p for p in self.mod_path.iterdir() if p.is_dir()]:
            module_class = default_module
            meta_path = p / "meta.yaml"
            if meta_path.exists() and meta_path.is_file():
                meta_data = read_yaml_file(meta_path)
                if meta_data and (m_class_path := meta_data.get("class", None)):
                    module_class = import_from_module(m_class_path)
            m = module_class(p.name, p, self.save_root / p.name)
            snekmud.MODULES[m.name] = m

        logging.info(f"Discovered {len(snekmud.MODULES)} modules!")

        for k, v in snekmud.MODULES.items():
            await v.load_init()

        for k, v in snekmud.MODULES.items():
            await v.load_maps()

        for k, v in snekmud.MODULES.items():
            await v.load_prototypes()

        await self.at_post_module_initial_load()

        logging.info("Performing initial entity load from database.")
        for k, v in snekmud.MODULES.items():
            await v.load_entities_initial()
        logging.info("Finished initial entity load.")

        logging.info("Finalizing load of entities...")
        for k, v in snekmud.MODULES.items():
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