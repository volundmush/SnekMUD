import typing
from snekmud import MODIFIERS_ID, MODIFIERS_NAMES
from mudforge.utils import partial_match, lazy_property
from snekmud.exceptions import DatabaseError
from snekmud import OPERATIONS, WORLD, COMPONENTS
from snekmud.utils import get_or_emplace


class Modifier:
    modifier_id = -1

    def __init__(self, owner):
        self.owner = owner

    @classmethod
    def get_name(cls):
        if hasattr(cls, "name"):
            return cls.name
        return cls.__name__

    def __str__(self):
        return getattr(self, "name", self.__class__.__name__)

    def __int__(self):
        return self.modifier_id

    def __repr__(self):
        return f"<{self.__class__.__name__}: {int(self)}>"

    def stat_multiplier(self, ent, stat_name) -> float:
        return 0.0

    def stat_bonus(self, ent, stat_name) -> int:
        return 0


class _ModHandler:
    comp_name = None

    def __init__(self, ent):
        self.ent = ent

    @lazy_property
    def comp(self):
        return get_or_emplace(self.ent, COMPONENTS[self.comp_name])

    def find(self, flag):
        if (found := self.comp.find(flag)):
            return found
        elif isinstance(flag, str):
            if (fname := partial_match(flag, MODIFIERS_NAMES[self.comp.category()].keys())):
                return MODIFIERS_NAMES[self.comp.category()][fname]
        return None

    def all(self):
        return self.comp.all()

    def ids(self):
        return [x.modifier_id for x in self.all()]

    def names(self):
        return [x.name for x in self.all()]


class SingleModifier(_ModHandler):
    """
    Class used as a base for handling single Modifier types, like Race, Sensei, ItemType, RoomSector.
    """
    default = None

    @lazy_property
    def comp(self):
        return get_or_emplace(self.ent, COMPONENTS[self.comp_name], modifier=self.default)

    def __init__(self, ent):
        super().__init__(ent)
        if self.default:
            comp = self.comp
            if not comp.modifier:
                comp.modifier = self.default(ent)

    def get(self) -> typing.Optional["Modifier"]:
        return self.comp.modifier

    def set(self, flag: typing.Union[int, str, typing.Type["Modifier"]], strict: bool = False):
        """
        Used to set a flag to owner. It will replace existing one.

        Args:
            flag (int or str): ID or name (case insensitive) of flag.
            strict (bool): raise error if flag doesn't exist.

        Raises:
            DatabaseError if flag does not exist.
        """
        if (found := self.find(flag)):
            self.comp.modifier = found(self.ent)
        elif strict:
            raise DatabaseError(f"{self.comp.category()} {flag} not found!")

    def clear(self):
        self.comp.modifier = None


class MultiModifier(_ModHandler):
    """
    Class used as a base for handling PlayerFlags, RoomFlags, MobFlags, and similar.

    It is meant to be instantiated via @lazy_property on an ObjectDB typeclass.

    These are objects loaded into advent.MODIFIERS_NAMES and MODIFIERS_ID.
    """

    def has(self, flag: typing.Union[int, str, typing.Type["Modifier"]]) -> bool:
        """
        Called to determine if owner has this flag.

        Args:
            flag (int or str): ID or name (case insensitive) of flag.

        Returns:
            answer (bool): Whether owner has flag.
        """
        if (found := self.find(flag)):
            return found.modifier_id in self.ids()
        return False

    def add(self, flag: typing.Union[int, str, typing.Type["Modifier"]], strict=False):
        """
        Used to add a flag to owner.

        Args:
            flag (int or str): ID or name (case insensitive) of flag.
            strict (bool): raise error if flag doesn't exist.

        Raises:
            DatabaseError if flag does not exist.
        """
        if (found := self.find(flag)):
            m = found(self.ent)
            self.comp.modifiers[str(m)] = m
        elif strict:
            raise DatabaseError(f"{self.comp.category()} {flag} not found!")

    def remove(self, flag: typing.Union[int, str], strict=False):
        """
        Removes a flag if owner has it.

        Args:
            flag (int or str): ID or name (case insensitive) of flag.
            strict (bool): raise error if flag doesn't exist.

        Raises:
            DatabaseError if flag does not exist.
        """
        if (found := self.find(flag)):
            self.comp.modifiers.pop(found.get_name(), None)
        elif strict:
            raise DatabaseError(f"{self.comp.category()} {flag} not found!")