#!/usr/bin/env python3
from pathlib import Path
import asyncio
import os
import sys
import logging
import orjson
import snekmud
from mudforge.utils import generate_name, import_from_module
from snekmud.db.account import CRYPT
from ruamel.yaml import YAML
from snekmud.game import AccountManager, CharacterManager
from rich.traceback import install
#install(show_locals=True)


class GameImporter:

    def __init__(self, folder, era=0, skip=False, admin_names = None):
        if admin_names is None:
            admin_names = list()
        self.folder = Path(folder)
        self.skip = skip
        self.era = era
        self.users = dict()
        self.characters = dict()
        self.char_map = dict()
        self.account_map = dict()
        self.admin_names = admin_names
        self.account_manager = AccountManager(self)
        self.character_manager = CharacterManager(self)

    async def import_accounts(self, account_path):
        for p in Path(account_path).rglob("*.json"):
            if p.is_file() and p.exists():
                await self.import_account(p)

    async def import_account(self, path: Path):
        print(f"Importing Account From File: {path}")
        account_id = generate_name("acc", snekmud.ACCOUNTS.keys(), gen_length=8)
        acc_class = snekmud.CLASSES["account"]
        acc_driver = snekmud.CLASSES["account_driver"]
        with path.open(mode="rb") as f:
            data = orjson.loads(f.read())
            data["account_id"] = account_id
            acc = acc_driver(acc_class.from_dict(data))
            snekmud.ACCOUNTS[acc.account.account_id] = acc
        print(f"Imported Account: {acc.account.name} - {account_id}")
        self.account_map[acc.account.name.lower()] = account_id

    async def import_zones(self, zone_path):
        zone_dir = Path.cwd() / "zones"
        zone_dir.mkdir(parents=True, exist_ok=True)
        for p in Path(zone_path).iterdir():
            if p.is_dir() and p.name.isdigit():
                await self.import_zone(p, zone_dir)

    async def import_zone(self, path: Path, zone_dir):
        async def import_helper(path: Path, filename: str, vnum: int, zone, method):
            j_file = path / filename
            if j_file.exists():
                await method(j_file, vnum, zone)

        zone_class = snekmud.CLASSES["zone"]
        zone_driver = snekmud.CLASSES["zone_driver"]
        z_file = path / "zone.json"
        print(f"Importing Zone from Path: {path}")
        with z_file.open(mode="rb") as f:
            vnum = int(path.name)
            zone_data = orjson.loads(f.read())
            zone_data["vnum"] = vnum
            zone = zone_driver(zone_dir / str(vnum), zone_class.from_dict(zone_data))
            snekmud.ZONES[vnum] = zone

        for fn, meth in [("triggers.json", self.import_triggers), ("rooms.json", self.import_rooms),
                      ("objects.json", self.import_objects), ("mobiles.json", self.import_mobiles),
                      ("shops.json", self.import_shops), ("guilds.json", self.import_guilds)]:
            await import_helper(path, fn, vnum, zone, meth)

    async def import_triggers(self, path: Path, vnum: int, zone):
        pass

    async def import_rooms(self, path: Path, vn: int, zone):
        room_class = snekmud.CLASSES["room"]
        room_driver = snekmud.CLASSES["room_driver"]

        with path.open(mode="rb") as f:
            data = orjson.loads(f.read())
            for k, v in data.items():
                await asyncio.sleep(0)
                vnum = int(k)
                v["vnum"] = vnum
                if "exits" in v:
                    exits = v["exits"]
                    v["exits"] = {int(k): v for k, v in exits.items()}
                room = room_driver(room_class.from_dict(v), zone)
                snekmud.ROOMS[vnum] = room
                zone.rooms[vnum] = room
        print(f"ZONE {vn}: Imported {len(zone.rooms)} rooms.")

    async def import_objects(self, path: Path, vn: int, zone):
        obj_class = snekmud.CLASSES["entity"]
        obj_driver = snekmud.PROTOTYPE_CLASSES["item"]

        with path.open(mode="rb") as f:
            data = orjson.loads(f.read())
            for k, v in data.items():
                await asyncio.sleep(0)
                vnum = v["entity_key"]
                v["item_data"]["values"] = {int(k): v for k, v in v["item_data"]["values"].items()}
                obj = obj_driver(obj_class.from_dict(v), zone=zone)
                snekmud.OBJECT_PROTOTYPES[vnum] = obj
                zone.objects[vnum] = obj

        print(f"ZONE {vn}: Imported {len(zone.objects)} objects.")

    async def import_mobiles(self, path: Path, vn: int, zone):
        mob_class = snekmud.CLASSES["entity"]
        mob_driver = snekmud.PROTOTYPE_CLASSES["character"]

        with path.open(mode="rb") as f:
            data = orjson.loads(f.read())
            for k, v in data.items():
                await asyncio.sleep(0)
                vnum = v["entity_key"]
                if v["character_data"]["sensei"] == 255:
                    v["character_data"]["sensei"] = -1
                mob = mob_driver(mob_class.from_dict(v), zone=zone)
                zone.mobiles[vnum] = mob
                snekmud.MOBILE_PROTOTYPES[vnum] = mob
        print(f"ZONE {vn}: Imported {len(zone.mobiles)} mobiles.")

    async def import_shops(self, path: Path, vn: int, zone):
        pass

    async def import_guilds(self, path: Path, vn: int, zone):
        pass

    async def import_characters(self, character_path):
        for p in Path(character_path).rglob("*.json"):
            if p.is_file() and p.exists():
                await self.import_character(p)

    async def import_character(self, path: Path):
        print(f"Importing Character From File: {path}")
        character_id = generate_name("char", snekmud.CHARACTERS.keys(), gen_length=8)
        mob_class = snekmud.CLASSES["entity"]
        mob_driver = snekmud.INSTANCE_CLASSES["character"]
        with path.open(mode="rb") as f:
            data = orjson.loads(f.read())
            data["character_id"] = character_id
            account_name = data.pop("account_id")
            data["account_id"] = self.account_map.get(account_name)
            mob = mob_driver(mob_class.from_dict(data), character_id, prototype=None, persistent=True)
            snekmud.CHARACTERS[character_id] = mob
        print(f"Imported Character: {mob.entity.name} - {character_id}")

    async def run(self):
        if not self.folder.exists() and self.folder.is_dir():
            raise ValueError("Input lib folder does not exist.")
        await self.import_accounts(self.folder / "accounts")
        await self.import_zones(self.folder / "zones")
        await self.import_characters(self.folder / "characters")
        for k, v in snekmud.ZONES.items():
            print(f"Saving Zone: {k} - {v.zone.name}")
            await v.save_all()
        await self.account_manager.save_all()
        await self.character_manager.save_all()


if __name__ == "__main__":
    if not sys.argv:
        raise Exception("Must be called with a pathname!")

    y = YAML(typ="safe")

    try:
        with open(f"mudforge.yaml", "r") as f:
            snekmud.CONFIG = y.load(f)
        with open("shared.yaml", "r") as f:
            snekmud.SHARED = y.load(f)
    except Exception:
        raise Exception("Could not import config!")
    empty = dict()

    snekmud.CLASSES = {k: import_from_module(v) for k, v in snekmud.CONFIG.get("classes", empty).items()}
    snekmud.SERVICES = {k: import_from_module(v)(shared=snekmud.SHARED, config=snekmud.CONFIG) for k, v in
                snekmud.CONFIG.get("services", empty).items()}
    snekmud.INSTANCE_CLASSES = {k: import_from_module(v) for k, v in snekmud.CONFIG.get("instances", empty).items()}
    snekmud.PROTOTYPE_CLASSES = {k: import_from_module(v) for k, v in snekmud.CONFIG.get("prototypes", empty).items()}

    g_importer = GameImporter(sys.argv[1], admin_names=sys.argv[2:])

    asyncio.run(g_importer.run())
    print("Conversion Complete!")