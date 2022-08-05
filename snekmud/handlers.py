from snekmud.typing import Entity
import snekmud


class AccountHandler:

    def __init__(self, owner):
        self.owner = owner
        self.connections = dict()

    def player_ids(self):
        return self.owner.characters.all().values_list("id", flat=True)

    def characters_brief(self):
        return self.owner.characters.all().values_list("id", "name")

    def send(self, **kwargs):
        for c in self.connections.values():
            c.send(**kwargs)


class GameSessionHandler:

    def __init__(self, owner):
        self.owner = owner
        self.connections = dict()
        self.account = None
        self.character = None
        self.puppet = None
        self.cmdhandler = None

    def send(self, **kwargs):
        for c in self.connections.values():
            c.send(**kwargs)

    async def set_cmdhandler(self, cmdhandler: str, **kwargs):
        if not (p := snekmud.CMDHANDLERS["Session"].get(cmdhandler, None)):
            self.send(text=f"ERROR: CmdHandler {cmdhandler} not found for GameSessions, contact staff")
            return
        if self.cmdhandler:
            await self.cmdhandler.close()
        self.cmdhandler = p(self, **kwargs)
        await self.cmdhandler.start()

    async def process_input_text(self, data: str):
        if self.cmdhandler:
            await self.cmdhandler.parse(data)


class PlayerCharacterHandler:

    def __init__(self, owner):
        self.owner = owner
        self.ent = None
        self.game_session = None

    def send(self, **kwargs):
        if not self.game_session:
            return
        self.game_session.send(**kwargs)
