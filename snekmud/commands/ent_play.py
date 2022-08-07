import re
import snekmud

from .base import Command, EntityCommandHandler
from snekmud.exceptions import CommandError
from snekmud.db.accounts.models import Account

class EntityPlayCmdHandler(EntityCommandHandler):
    sub_categories = ["play", "universal"]

class _EntityCommand(Command):
    main_category = "entity"


class _PlayCommand(_EntityCommand):
    sub_categories = ["play"]
