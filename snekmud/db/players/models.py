from django.db import models
from yamlfield.fields import YAMLField
from mudforge.utils import utcnow, lazy_property
from mudforge import CLASSES
from snekmud.db.idmap import models as idmodels


class PlayerCharacter(idmodels.IdMapModel):
    name = models.CharField(max_length=30, blank=False, null=False, unique=True)
    account = models.ForeignKey("accounts.Account", related_name="characters", on_delete=models.PROTECT)
    data = YAMLField(null=False, blank=False)
    inventory = YAMLField(null=True, blank=False)
    equipment = YAMLField(null=True, blank=False)
    playtime = models.FloatField(null=False, default=0.0)
    date_created = models.DateTimeField(default=utcnow)
    date_last_login = models.DateTimeField(null=True, default=None)
    approved = models.BooleanField(default=False, null=False)

    @lazy_property
    def handler(self):
        return CLASSES["PlayerCharacterHandler"](self)
