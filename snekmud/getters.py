from mudforge.utils import make_iter, is_iter
from snekmud.typing import Entity
from snekmud import COMPONENTS, WORLD, OPERATIONS, MODULES, GETTERS
from rich.text import Text


class DisplayInRoom:

    def __init__(self, viewer, room, entity, **kwargs):
        self.viewer = viewer
        self.room = room
        self.entity = entity
        self.kwargs = kwargs

    def execute(self):
        if (long := WORLD.try_component(self.entity, COMPONENTS["RoomDescription"])) and long.plain:
            return long.color
        name = GETTERS["GetDisplayName"](self.viewer, self.entity).execute()
        return f"{name} is here."


class GetEquipment:

    def __init__(self, entity, **kwargs):
        self.entity = entity
        self.kwargs = kwargs

    def execute(self):
        if (eq := WORLD.try_component(self.entity, COMPONENTS["Equipment"])):
            return list(eq.all())
        return []


class VisibleEquipment:

    def __init__(self, viewer: Entity, holder: Entity, **kwargs):
        self.viewer = viewer
        self.holder = holder
        self.kwargs = kwargs

    def execute(self):
        return GETTERS["VisibleEntities"](self.viewer, GETTERS["GetEquipment"](self.holder).execute()).execute()


class VisibleNearbyMeta:

    def __init__(self, viewer: Entity, meta_type: str = "item", **kwargs):
        self.viewer = viewer
        self.meta_type = meta_type
        self.kwargs = kwargs

    def execute(self):
        meta_get = GETTERS["GetMetaTypes"]

        def check(ent):
            if not (meta := meta_get(ent).execute()):
                return False
            return self.meta_type in meta.types

        con_get = GETTERS["VisibleContents"]
        out = list()
        if (room := GETTERS["GetRoomLocation"](self.viewer).execute()):
            room_contents = con_get(self.viewer, room).execute()
            room_contents.remove(self.viewer)
            out.extend(room_contents)
        out.extend(con_get(self.viewer, self.viewer).execute())
        out.extend(GETTERS["VisibleEquipment"](self.viewer, self.viewer).execute())
        return [o for o in out if check(o)]


class GetDisplayName:

    def __init__(self, viewer, target, rich=False, plain=False, **kwargs):
        self.viewer = viewer
        self.target = target
        self.kwargs = kwargs
        self.rich = rich
        self.plain = plain

    def execute(self):
        if (name := WORLD.try_component(self.target, COMPONENTS["Name"])):
            if self.rich:
                return name.rich
            if self.plain:
                return name.plain
            return name.color
        elif (comp := WORLD.try_component(self.target, COMPONENTS["EntityID"])):
            fmt = f"{comp.module_name}/{comp.ent_id}"
        else:
            fmt = f"Entity {self.target}"
        if self.rich:
            return Text(fmt)
        return fmt


class GetContents:
    """
    Retrieve every Entity in an Entity's Inventory.
    """

    def __init__(self, entity, **kwargs):
        self.entity = entity
        self.kwargs = kwargs

    def execute(self) -> list[Entity]:
        if (inv := WORLD.try_component(self.entity, COMPONENTS["Inventory"])):
            return [i for i in inv.inventory if WORLD.entity_exists(i)]
        return []


class VisibleEntities:
    """
    Return a list of all entities which the viewer can see.
    """

    def __init__(self, viewer, entities, **kwargs):
        self.viewer = viewer
        self.entities = entities
        self.kwargs = kwargs

    def execute(self) -> list[Entity]:
        g = GETTERS["VisibleTo"]
        return [x for x in self.entities if g(self.viewer, x, **self.kwargs).execute()]


class VisibleTo:
    """
    Check to see if viewer can see entity.
    """

    def __init__(self, viewer, entity, **kwargs):
        self.viewer = viewer
        self.entity = entity
        self.kwargs = kwargs

    def execute(self) -> bool:
        return True


class VisibleContents:
    """
    Wrapper for VisibleEntities that retrieves contents from room.
    """

    def __init__(self, viewer, entity, **kwargs):
        self.viewer = viewer
        self.entity = entity
        self.kwargs = kwargs

    def execute(self) -> list[Entity]:
        vis_to = GETTERS["VisibleEntities"]
        contents = GETTERS["GetContents"](self.entity, **self.kwargs).execute()
        return vis_to(self.viewer, contents, **self.kwargs).execute()


class EntityFromKeyAndGridCoordinates:
    comp = "GridMap"

    def __init__(self, module_name: str, entity_key: str, coordinates):
        self.module_name = module_name
        self.entity_key = entity_key
        self.coordinates = coordinates

    def execute(self):
        if not (e := GETTERS["EntityFromKey"](self.module_name, self.entity_key).execute()):
            return None
        if not (grid := WORLD.try_component(e, COMPONENTS[self.comp])):
            return None
        if not (holder := grid.rooms.search_nn((self.coordinates[0], self.coordinates[1], self.coordinates[2]))):
            return None
        c1 = holder.coordinates
        c2 = self.coordinates
        if not c1[0] == c2[0] and c1[1] == c2[1] and c1[2] == c2[2]:
            return None
        return holder.data


class EntityFromKey:

    def __init__(self, module_name: str, entity_key: str):
        self.module_name = module_name
        self.entity_key = entity_key

    def execute(self):
        if not (m := MODULES.get(self.module_name, None)):
            return None
        return m.entities.get(self.entity_key, None)


class GetRoomLocation:

    def __init__(self, ent):
        self.ent = ent

    def execute(self):
        if (in_room := WORLD.try_component(self.ent, COMPONENTS["InRoom"])):
            return in_room.holder
        return None


class Gender:

    def __init__(self, viewer, target, **kwargs):
        self.viewer = viewer
        self.target = target
        self.kwargs = kwargs

    def execute(self):
        return "neuter"


class GetAllContainedEntities:

    def __init__(self, ent):
        self.ent = ent

    def execute(self):
        if (eq := WORLD.try_component(self.ent, COMPONENTS["Equipment"])):
            for k, v in eq.equipment.items():
                if not WORLD.entity_exists(v.item):
                    continue
                for x in GETTERS["GetAllContainedEntities"](v.item).execute():
                    yield x
                yield v.item
        if (inv := WORLD.try_component(self.ent, COMPONENTS["Inventory"])):
            for i in inv.inventory:
                if not WORLD.entity_exists(i):
                    continue
                for x in GETTERS["GetAllContainedEntities"](i).execute():
                    yield x
                yield i