from django.db import models
from yamlfield.fields import YAMLField
from mudforge.utils import utcnow, lazy_property
from mudforge import CLASSES


class PlayerCharacter(models.Model):
    name = models.CharField(max_length=30, blank=False, null=False, unique=True)
    account = models.ForeignKey("accounts.Account", related_name="characters", on_delete=models.PROTECT)
    data = YAMLField(null=False, blank=False)
    playtime = models.DurationField(null=False, default=0)
    date_created = models.DateTimeField(default=utcnow)
    date_last_login = models.DateTimeField(null=True, default=None)
    approved = models.BooleanField(default=False, null=False)

    @lazy_property
    def handler(self):
        return CLASSES["PlayerCharacterHandler"](self)