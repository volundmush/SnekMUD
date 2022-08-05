from .conn_base import ConnParser
import adventkai
from mudforge.net.basic import DisconnectReason
from mudforge import GAME
from snekmud import COMPONENTS, PLAYER_ID


class AccountMenu(ConnParser):

    def __init__(self, conn):
        super().__init__(conn)
        self.account = conn.account

    def get_characters(self):
        entities = list()
        for c in self.account.handler.all():
            ent = PLAYER_ID[c.id]
            entities.append(ent)
        return entities
