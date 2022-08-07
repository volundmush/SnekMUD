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

OPERATION_CLASS_PATHS = ["snekmud.operations.location", "snekmud.operations.misc", "snekmud.operations.search",
                         "snekmud.operations.display"]

CMDHANDLERS = defaultdict(dict)
CMDHANDLERS["Connection"]["Account"] = "snekmud.commands.conn_account.ConnectionAccountCmdHandler"
CMDHANDLERS["Connection"]["Login"] = "snekmud.commands.conn_login.ConnectionLoginCmdHandler"
CMDHANDLERS["Connection"]["Session"] = "snekmud.commands.conn_session.ConnectionSessionCmdHandler"
CMDHANDLERS["Session"]["Puppet"] = "snekmud.commands.sess_puppet.SessionPuppetCmdHandler"
CMDHANDLERS["Entity"]["Play"] = "snekmud.commands.ent_play.EntityPlayCmdHandler"

CMD_MATCH = re.compile(r"^(?P<cmd>(?P<prefix>[\|@\+\$-]+)?(?P<name>\w+))(?P<fullargs>(?P<switches>(?:\/\w+){0,})(?: +(?P<args>(?P<lsargs>[^=]+)?(?:=(?P<rsargs>.+)?)?)?)?)?",
                       flags=re.IGNORECASE | re.MULTILINE)

COMMAND_PATHS = ["snekmud.commands.conn_account", "snekmud.commands.conn_login", "snekmud.commands.conn_universal",
                 "snekmud.commands.conn_session", "snekmud.commands.ent_play", "snekmud.commands.sess_puppet"]