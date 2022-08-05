import esper
from collections import defaultdict

WORLD = esper.World()

MODULES = {}

COMPONENTS = {}

MODIFIERS_NAMES = defaultdict(dict)

MODIFIERS_ID = defaultdict(dict)

EQUIP_SLOTS = defaultdict(dict)

PLAYER_ID = dict()

OPERATIONS = dict()

CMDHANDLERS = defaultdict(dict)

COMMANDS = defaultdict(lambda: defaultdict(list))
