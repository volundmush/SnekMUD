from django.db import models
from snekmud.db.idmap import models as idmodels
from mudforge import CLASSES
from mudforge.utils import lazy_property, utcnow
import time


class GameSession(idmodels.IdMapModel):
    id = models.OneToOneField('players.PlayerCharacter', primary_key=True, null=False, related_name="session",
                              on_delete=models.PROTECT)
    account = models.ForeignKey('accounts.Account', null=False, related_name="sessions", on_delete=models.PROTECT)
    start_time = models.DateTimeField(auto_now_add=True, editable=True)

    @lazy_property
    def handler(self):
        return CLASSES["GameSessionHandler"](self)
