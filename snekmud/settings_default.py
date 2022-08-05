from mudforge.settings_default import *
import re

NAME = "SnekMUD"

SERVICES["game"] = "snekmud.game.GameService"

HOOKS["pre_start"].append("snekmud.hooks.pre_start")
HOOKS["early_launch"].append("snekmud.hooks.early_launch")

COMPONENTS = [
    "snekmud.components"
]

CLASSES["game_connection"] = "snekmud.connection.GameConnection"
CLASSES["default_module"] = "snekmud.modules.Module"
CLASSES["AccountHandler"] = "snekmud.handlers.AccountHandler"
CLASSES["GameSessionHandler"] = "snekmud.handlers.GameSessionHandler"
CLASSES["PlayerCharacterHandler"] = "snekmud.handlers.PlayerCharacterHandler"

EQUIP_CLASS_PATHS = list()

MODIFIERS = list()

OPERATION_CLASS_PATHS = ["snekmud.operations.location"]

CMDHANDLERS = defaultdict(dict)
CMDHANDLERS["Connection"]["Account"] = "snekmud.parsers.conn.account.AccountMenu"
CMDHANDLERS["Connection"]["Login"] = "snekmud.parsers.conn_login.LoginParser"

CMD_MATCH = re.compile(r"^(?P<cmd>(?P<prefix>[\|@\+\$-]+)?(?P<name>\w+))(?P<fullargs>(?P<switches>(?:\/\w+){0,})(?: +(?P<args>(?P<lsargs>[^=|.]+)?(?:=(?P<rsargs>.+)?)?)?)?)?",
                       flags=re.IGNORECASE | re.MULTILINE)

COMMAND_PATHS = []