import snekmud
import logging
import orjson
from pathlib import Path
from aiomisc import receiver, entrypoint, get_context
from mudforge.utils import import_from_module
from mudforge.ansi.circle import CircleToRich


async def pre_start(entrypoint=None, services=None):
    context = get_context()
    snekmud.CONFIG = await context["config"]
    snekmud.SHARED = await context["shared"]
    snekmud.SERVICES = await context["services"]
    snekmud.CLASSES = await context["classes"]

    logging.info("SnekMUD loading...")
    snekmud.GAME = snekmud.SERVICES["game"]
    snekmud.CONNECTIONS = await context["connections"]
    empty = dict()
    snekmud.INSTANCE_CLASSES = {k: import_from_module(v) for k, v in snekmud.CONFIG.get("instances", empty).items()}
    snekmud.PROTOTYPE_CLASSES = {k: import_from_module(v) for k, v in snekmud.CONFIG.get("prototypes", empty).items()}

    for category, path in snekmud.CONFIG.get("command_handlers", dict()).items():
        snekmud.COMMAND_HANDLERS[category] = import_from_module(path)

    logging.info(f"Found {len(snekmud.COMMAND_HANDLERS)} command handlers.")

    command_counter = 0
    for category, entries in snekmud.CONFIG.get("commands", dict()).items():
        imported = [import_from_module(c) for c in entries]
        total_commands = list()
        for c in imported:
            if isinstance(c, list):
                total_commands.extend(c)
            else:
                total_commands.append(c)
        snekmud.COMMANDS[category] = total_commands
        command_counter += len(total_commands)

    logging.info(f"Found {command_counter} commands in {len(snekmud.COMMANDS)} categories.")

    module_class = snekmud.CLASSES["module"]

    mod_folder = Path.cwd() / "modules"
    if mod_folder.exists() and mod_folder.is_dir():
        for d in mod_folder.iterdir():
            if not d.is_dir():
                continue
            m = module_class(d)
            snekmud.MODULES[m.name] = m

    if "system" not in snekmud.MODULES:
        raise Exception("The system module is missing from <profile>/modules/ ! Game cannot launch.")

    for k, v in snekmud.MODULES.items():
        await v.load_data()

    snekmud.PLAYER_PROTOTYPE = snekmud.MODULES["system"].prototypes["player_character"]

    zone_class = snekmud.CLASSES["zone"]
    zone_driver_class = snekmud.CLASSES["zone_driver"]
    zone_folder = Path.cwd() / "zones"
    if zone_folder.exists() and zone_folder.is_dir():
        zone_folders = zone_folder.iterdir()
        for d in zone_folder.iterdir():
            if not d.is_dir() or not d.name.isdigit():
                continue
            z_info = d / "zone.json"
            if not z_info.exists() and z_info.is_file():
                raise Exception(f"Zone system received invalid zone: {z_info.absolute()}")
            with z_info.open(mode="r") as f:
                zone = zone_class.from_json(f.read())
                z = zone_driver_class(d, zone)
                snekmud.ZONES[z.zone.vnum] = z

    zone_count = len(snekmud.ZONES)

    for k, v in snekmud.ZONES.items():
        zone_count -= 1
        logging.info(f"Loading Zone {k}: {v.zone.name} ({zone_count} more remain)")
        await v.load_data()

    await snekmud.GAME.prepare_zones()
    await snekmud.GAME.prepare_rooms()

    accounts = await snekmud.GAME.accounts.load()
    logging.info(f"Found and loaded {accounts} User Accounts.")
    characters = await snekmud.GAME.characters.load()
    logging.info(f"Found and loaded {characters} player characters.")

    no_accounts = await snekmud.GAME.prepare_characters()
    if no_accounts:
        logging.warning(f"Found {len(no_accounts)} with missing Accounts, which were not loaded: {', '.join(no_accounts)}")

    text_dir = Path.cwd() / "text"
    if not text_dir.exists() and text_dir.is_dir():
        raise Exception("No text directory in the profile_template! Where did it go?")
    for t in text_dir.iterdir():
        if not t.is_file():
            continue
        with t.open(mode="r") as f:
            logging.info(f"Reading text/{t.name} into resources...")
            snekmud.GAME.text_files[t.name] = CircleToRich(f.read())

async def post_start(entrypoint=None, services=None):
    pass


async def pre_stop(ep: entrypoint):
    pass


async def post_stop(ep: entrypoint):
    pass
