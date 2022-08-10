from mudforge.utils import make_iter, is_iter
from snekmud.typing import Entity
from snekmud import COMPONENTS, WORLD, OPERATIONS, MODULES, GETTERS
from rich.text import Text


class DisplayRoom:

    def __init__(self, viewer, room, **kwargs):
        self.viewer = viewer
        self.room = room
        self.kwargs = kwargs

    async def execute(self):
        pass

