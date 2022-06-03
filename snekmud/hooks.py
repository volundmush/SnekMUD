import snekmud
import logging
from aiomisc import receiver, entrypoint, get_context
from mudforge.utils import import_from_module


async def pre_start(entrypoint=None, services=None):
    context = get_context()
    snekmud.CONFIG = await context["config"]
    snekmud.SHARED = await context["shared"]
    snekmud.SERVICES = await context["services"]
    snekmud.CLASSES = await context["classes"]

    logging.info("SnekMUD loading...")
    snekmud.GAME = snekmud.SERVICES["game"]
    snekmud.CONNECTIONS = await context["connections"]

    command_counter = 0
    for category, entries in snekmud.CONFIG.get("commands", dict()).items():
        snekmud.COMMANDS[category] = [import_from_module(c) for c in entries]
        command_counter += len(entries)

    logging.info(f"Found {command_counter} commands in {len(snekmud.COMMANDS)} categories.")

    for category, path in snekmud.CONFIG.get("command_handlers", dict()).items():
        snekmud.COMMAND_HANDLERS[category] = import_from_module(path)

    logging.info(f"Found {len(snekmud.COMMAND_HANDLERS)} command handlers.")

    accounts = await snekmud.GAME.accounts.load()
    logging.info(f"Found and loaded {accounts} User Accounts.")
    characters = await snekmud.GAME.characters.load()
    logging.info(f"Found and loaded {characters} player characters.")

    no_accounts = await snekmud.GAME.prepare_characters()
    if no_accounts:
        logging.warning(f"Found {len(no_accounts)} with missing Accounts, which were not loaded: {', '.join(no_accounts)}")


async def post_start(entrypoint=None, services=None):
    pass


async def pre_stop(ep: entrypoint):
    pass


async def post_stop(ep: entrypoint):
    pass
