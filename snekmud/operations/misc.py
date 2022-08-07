from snekmud import COMPONENTS, WORLD, OPERATIONS, MODULES

class GetAllContainedEntities:

    def __init__(self, ent):
        self.ent = ent

    async def execute(self):
        if (eq := WORLD.try_component(self.ent, COMPONENTS["Equipment"])):
            for k, v in eq.equipment.items():
                if not WORLD.entity_exists(v.item):
                    continue
                for x in await OPERATIONS["GetAllContainedEntities"](v.item).execute():
                    yield x
                yield v.item
        if (inv := WORLD.try_component(self.ent, COMPONENTS["Inventory"])):
            for i in inv.inventory:
                if not WORLD.entity_exists(i):
                    continue
                for x in await OPERATIONS["GetAllContainedEntities"](v.item).execute():
                    yield x
                yield i

class ExtractEntity:
    def __init__(self, ent):
        self.ent = ent

    async def execute(self):
        for x in await OPERATIONS["GetAllContainedEntities"](self.ent).execute():
            WORLD.delete_entity(x)
        WORLD.delete_entity(self.ent)
