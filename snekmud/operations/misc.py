from snekmud import COMPONENTS, WORLD, OPERATIONS, MODULES, GETTERS


class CleanupEntity:

    def __init__(self, ent):
        self.ent = ent

    async def execute(self):
        pass


class ExtractEntity:
    def __init__(self, ent):
        self.ent = ent

    async def execute(self):
        cleanup = OPERATIONS["CleanupEntity"]
        for x in GETTERS["GetAllContainedEntities"](self.ent).execute():
            await cleanup(x).execute()
            WORLD.delete_entity(x)
        await cleanup(self.ent).execute()
        WORLD.delete_entity(self.ent)
