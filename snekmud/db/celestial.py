from typing import List, Optional, Dict, Set
from collections import defaultdict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from snekmud.db.entity import EntityInstanceDriver, EntityPrototypeDriver


class CelestialBodyPrototypeDriver(EntityPrototypeDriver):
    pass


class CelestialBodyInstanceDriver(EntityInstanceDriver):
    pass
