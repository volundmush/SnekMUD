from mudforge.settings_default import *
import re

NAME = "SnekMUD"

SERVICES["game"] = "snekmud.game.GameService"

HOOKS["early_launch"].append("snekmud.hooks.early_launch")
HOOKS["cold_start"].append("snekmud.hooks.cold_start")
HOOKS["copyover"].append("snekmud.hooks.copyover")
HOOKS["copyover_recover_stage_2"].append("snekmud.hooks.copyover_recover_stage_2")

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

OPERATION_CLASS_PATHS = ["snekmud.operations.location", "snekmud.operations.misc", "snekmud.operations.comm",
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

METATYPE_INTEGRITY = defaultdict(list)




######################################################################
# FuncParser
#
# Strings parsed with the FuncParser can contain 'callables' on the
# form $funcname(args,kwargs), which will lead to actual Python functions
# being executed.
######################################################################
# This changes the start-symbol for the funcparser callable. Note that
# this will make a lot of documentation invalid and there may also be
# other unexpected side effects, so change with caution.
FUNCPARSER_START_CHAR = "$"
# The symbol to use to escape Func
FUNCPARSER_ESCAPE_CHAR = "\\"
# This is the global max nesting-level for nesting functions in
# the funcparser. This protects against infinite loops.
FUNCPARSER_MAX_NESTING = 20
# Activate funcparser for all outgoing strings. The current Session
# will be passed into the parser (used to be called inlinefuncs)
FUNCPARSER_PARSE_OUTGOING_MESSAGES_ENABLED = False
# Only functions defined globally (and not starting with '_') in
# these modules will be considered valid inlinefuncs. The list
# is loaded from left-to-right, same-named functions will overload
FUNCPARSER_OUTGOING_MESSAGES_MODULES = ["evennia.utils.funcparser", "server.conf.inlinefuncs"]
# Prototype values are also parsed with FuncParser. These modules
# define which $func callables are available to use in prototypes.
FUNCPARSER_PROTOTYPE_PARSING_MODULES = [
    "evennia.prototypes.protfuncs",
    "server.conf.prototypefuncs",
]

GETTER_PATHS = ["snekmud.getters"]