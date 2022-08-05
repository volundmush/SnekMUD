import re
import snekmud

from .base import Command, ConnectionCommandHandler
from snekmud.exceptions import CommandError
from snekmud.db.accounts.models import Account