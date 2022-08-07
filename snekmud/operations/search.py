from snekmud import COMPONENTS, WORLD, OPERATIONS, MODULES
from snekmud.typing import Entity


class GetRoomLocation:

    def __init__(self, ent):
        self.ent = ent

    async def execute(self):
        if (in_room := WORLD.try_component(self.ent, COMPONENTS["InRoom"])):
            return in_room.holder
        return None


class EntityFromKey:

    def __init__(self, module_name: str, entity_key: str):
        self.module_name = module_name
        self.entity_key = entity_key

    async def execute(self):
        if not (m := MODULES.get(self.module_name, None)):
            return None
        return m.entities.get(self.entity_key, None)


class EntityFromKeyAndGridCoordinates:
    comp = "GridMap"

    def __init__(self, module_name: str, entity_key: str, coordinates):
        self.module_name = module_name
        self.entity_key = entity_key
        self.coordinates = coordinates

    async def execute(self):
        if not (e := await OPERATIONS["EntityFromKey"](self.module_name, self.entity_key).execute()):
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


class VisibleEntities:
    """
    Return a list of all entities which the viewer can see.
    """

    def __init__(self, viewer, entities, **kwargs):
        self.viewer = viewer
        self.entities = entities
        self.kwargs = kwargs

    async def execute(self) -> list[Entity]:
        return self.entities


class GetContents:
    """
    Retrieve every Entity in an Entity's INventory.
    """

    def __init__(self, entity, **kwargs):
        self.entity = entity
        self.kwargs = kwargs

    async def execute(self) -> list[Entity]:
        if (inv := WORLD.try_component(self.entity, COMPONENTS["Inventory"])):
            return [i for i in inv.inventory if WORLD.entity_exists(i)]
        return []


class VisibleTo:
    """
    Check to see if viewer can see entity.
    """

    def __init__(self, viewer, entity, **kwargs):
        self.viewer = viewer
        self.entity = entity
        self.kwargs = kwargs

    async def execute(self) -> bool:
        return True


class VisibleContents:
    """
    Wrapper for VisibleEntities that retrieves contents from room.
    """

    def __init__(self, viewer, entity, **kwargs):
        self.viewer = viewer
        self.entity = entity
        self.kwargs = kwargs

    async def execute(self) -> list[Entity]:
        vis_to = OPERATIONS["VisibleTo"]
        contents = await OPERATIONS["GetContents"](self.entity, **self.kwargs).execute()
        return [x for x in contents if await vis_to(self.viewer, x, **self.kwargs).execute()]