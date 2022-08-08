from snekmud.typing import Entity
import snekmud
import time
from snekmud.serialize import serialize_entity, deserialize_entity
import logging


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

    def get_admin_level(self):
        if self.owner.is_superuser:
            return 99999999999999999999999
        return 0


class GameSessionHandler:

    def __init__(self, owner):
        self.owner = owner
        self.connections = dict()
        self.account = owner.account
        self.character = None
        self.puppet = None
        self.cmdhandler = None
        self.cmdhandler_name = None
        self.time_last_activity = time.monotonic()

    def copyover_export(self) -> dict:
        out = {"time_last_activity": self.time_last_activity,
               "cmdhandler": self.cmdhandler_name}
        return out

    async def copyover_recover(self, data):
        self.time_last_activity = data.pop("time_last_activity")
        await self.at_start(copyover=True, cmdhandler=data.pop("cmdhandler"))

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
        self.cmdhandler_name = cmdhandler
        await self.cmdhandler.start()

    async def process_input_text(self, data: str):
        self.time_last_activity = time.monotonic()
        if self.cmdhandler:
            await self.cmdhandler.parse(data)

    def time_connected(self):
        return time.monotonic() - self.owner.start_time

    def time_idle(self):
        return time.monotonic() - self.time_last_activity

    async def at_start(self, copyover=None, cmdhandler: str = "Puppet"):
        """
        Called when the GameSession object is started.
        This should prepare the character for play, display updates
        to the player, etc.
        """
        await self.set_cmdhandler(cmdhandler)
        await self.deserialize_character(copyover)
        await self.deploy_character(copyover)

    loc_last = "You appear right where you left off."
    loc_none = "Cannot find a safe place to put you. Contact staff!"

    async def find_start_room(self):
        if (s_inroom := snekmud.WORLD.try_component(self.character, snekmud.COMPONENTS["SaveInRoom"])):
            if (ent := await snekmud.OPERATIONS["EntityFromKeyAndGridCoordinates"](s_inroom.module_name, s_inroom.ent_id, s_inroom.coordinates).execute()):
                snekmud.WORLD.remove_component(self.character, snekmud.COMPONENTS["SaveInRoom"])
                return ent, self.loc_last
        return None, self.loc_none

    async def deserialize_character(self, copyover=None):
        data = dict(self.owner.id.data)
        if (eq := self.owner.id.equipment):
            data["Equipment"] = eq
        if (inv := self.owner.id.inventory):
            data["Inventory"] = inv
        self.character = deserialize_entity(data)
        self.puppet = self.character
        c = self.character
        cmd = snekmud.COMPONENTS["HasCmdHandler"](entity=c, session=self.owner)
        snekmud.WORLD.add_component(c, cmd)
        await cmd.set_cmdhandler("Play")

    async def deploy_character(self, copyover=None):
        loc_ent, loc_msg = await self.find_start_room()

        if not loc_ent:
            self.send(line=loc_msg)
            logging.error(f"Cannot deploy_character() for {self.owner.id.name}, No Acceptable locations.")
            return
        c = self.character

        await snekmud.OPERATIONS["AddToRoom"](c, loc_ent, move_type="login").execute()
        await snekmud.OPERATIONS["MsgContents"](loc_ent, text="$You() has entered the game.", exclude=c, from_obj=c).execute()

    async def possess(self, ent, msg=None):
        if msg is None:
            display_name = await snekmud.OPERATIONS["GetDisplayName"](self.character, ent).execute()
            msg = f"You become {display_name}"
        self.puppet = ent
        self.send(line=msg)
        await self.at_possess(ent)

    async def at_possess(self, ent):
        pass

    def is_possessing(self):
        return self.character != self.puppet

    async def unposess(self, msg=None):
        puppet = self.puppet
        if msg is None:
            display_name = await snekmud.OPERATIONS["GetDisplayName"](self.character, puppet).execute()
            my_name = await snekmud.OPERATIONS["GetDisplayName"](self.character, self.character).execute()
            msg = f"You stop possessing {display_name} and return to being {my_name}"
        self.send(line=msg)
        self.puppet = self.character
        await self.at_unpossess(puppet)

    async def at_unpossess(self, ent):
        pass

    async def cleanup_misc(self):
        if self.is_possessing():
            await self.unposess()

    async def save_character(self):
        data = serialize_entity(self.character)
        inventory = data.pop("Inventory", None)
        equipment = data.pop("Equipment", None)
        pc = self.owner.id
        pc.data = data
        pc.inventory = inventory
        pc.equipment = equipment
        pc.save(update_fields=["data", "inventory", "equipment"])

    async def extract_character(self):
        await snekmud.OPERATIONS["ExtractEntity"].execute(self.character)

    async def update_stats(self):
        pass

    async def terminate_play(self):
        await self.cleanup_misc()
        await self.save_character()
        await self.extract_character()
        await self.update_stats()
        for conn in list(self.connections.values()):
            await self.remove_connection(conn, expected=True)
        self.owner.delete()

    async def add_connection(self, conn):
        conn.session = self.owner
        self.connections[conn.conn_id] = conn

    async def remove_connection(self, conn, expected=True):
        conn.session = None
        self.connections.pop(conn.conn_id, None)
        if not self.connections and not expected:
            await self.on_linkdead()

    async def on_additional_connection(self, conn):
        pass

    async def on_first_connection(self, conn):
        await self.at_start()

    async def on_linkdead(self):
        await self.terminate_play()

class PlayerCharacterHandler:

    def __init__(self, owner):
        self.owner = owner
        self.ent = None
        self.game_session = None

    def send(self, **kwargs):
        if not self.game_session:
            return
        self.game_session.send(**kwargs)
