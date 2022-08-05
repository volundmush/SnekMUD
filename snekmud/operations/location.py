from snekmud.components import Inventory, InInventory, InRoom, Equipment, Equipped
from snekmud.equip import EquipSlot

from snekmud.typing import Entity
from snekmud import WORLD, COMPONENTS, OPERATIONS
from snekmud.utils import get_or_emplace
import typing
from collections.abc import Iterable
from mudforge.utils import make_iter


class AddToInventory:
    """
    Operation to simply add items to an inventory. This bypasses all checks. It assumes that
    both ent and dest are valid Entities.
    """
    comp = "InInventory"
    rev_comp = "Inventory"

    def __init__(self, ent: typing.Union[Entity, Iterable[Entity]], dest: Entity, move_type: str = "move", **kwargs):
        self.ent = make_iter(ent)
        self.dest = dest
        self.move_type = move_type
        self.kwargs = kwargs

    async def execute(self):
        c = get_or_emplace(self.dest, COMPONENTS[self.rev_comp])
        c.inventory.extend(self.ent)
        for e in self.ent:
            WORLD.add_component(e, COMPONENTS[self.comp](holder=self.dest))
            await self.at_receive_entity(e)
        await self.at_receive_entities()

    async def at_receive_entity(self, ent: Entity):
        pass

    async def at_receive_entities(self):
        pass


class RemoveFromInventory:
    rev_comp = "InInventory"
    comp = "Inventory"

    def __init__(self, ent: Entity, move_type: str = "move", **kwargs):
        self.ent = ent
        self.move_type = move_type
        self.kwargs = kwargs

    async def execute(self):
        if (i := WORLD.get_component(self.ent, COMPONENTS[self.rev_comp])):
            inv = COMPONENTS[self.comp]
            c = get_or_emplace(i.holder, inv)
            c.inventory.remove(self.ent)
            if not c.inventory:
                WORLD.remove_component(i.holder, inv)
            WORLD.remove_component(self.ent, COMPONENTS[self.comp])

    async def at_remove_item(self):
        pass


class EquipToEntity:
    comp = "Equipment"
    rev_comp = "Equipped"

    def __init__(self, ent: Entity, dest: Entity, slot: typing.Type[EquipSlot], **kwargs):
        self.ent = ent
        self.dest = dest
        self.slot = slot
        self.kwargs = kwargs

    async def execute(self):
        e = get_or_emplace(self.dest, COMPONENTS[self.comp])
        sl = self.slot(self.ent)
        e.equipment[self.slot.key] = sl
        WORLD.add_component(self.ent, COMPONENTS[self.rev_comp](holder=self.dest, slot=self.slot.key))
        await self.at_equip_entity(e, sl)

    async def at_equip_entity(self, eqp, slot_instance):
        pass


class UnequipFromEntity:
    comp = "Equipment"
    rev_comp = "Equipped"

    def __init__(self, ent: Entity):
        equipped = COMPONENTS[self.rev_comp]
        if (i := WORLD.get_component(ent, equipped)):
            e = WORLD.get_component(i.holder)
            e.equipment.pop(i.slot, None)
            if not e.equipment:
                WORLD.remove_component(i.holder, COMPONENTS[self.comp])
            WORLD.remove_component(ent, equipped)


class AddToRoom(AddToInventory):
    comp = "InRoom"


class RemoveFromRoom(RemoveFromInventory):
    rev_comp = "InRoom"


class DumpInventory:
    comp = "Inventory"
    rev_comp = "InInventory"

    def __init__(self, ent: Entity):
        self.ent = ent
        self.inv_comp = COMPONENTS[self.comp]
        self.rev = COMPONENTS[self.rev_comp]

    async def execute(self) -> list[Entity]:
        i = get_or_emplace(self.ent, self.inv_comp)
        WORLD.remove_component(self.ent, self.inv_comp)
        for e in i.inventory:
            WORLD.remove_component(e, self.rev_comp)
        return i.inventory


class DumpRoom(DumpInventory):
    rev_comp = "InRoom"


class DumpEquipment:
    comp = "Equipment"
    rev_comp = "Equipped"

    def __init__(self, ent: Entity):
        self.ent = ent
        self.eq = COMPONENTS[self.comp]
        self.rev = COMPONENTS[self.rev_comp]

    async def execute(self) -> list[Entity]:
        i = get_or_emplace(self.ent, self.eq)
        for k, v in i.equipment.items():
            WORLD.remove_component(v, self.rev)
        WORLD.remove(self.ent, self.eq)
        return list(i.equipment.values())


