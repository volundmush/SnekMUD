import os
import snekmud
from mudforge.launcher import Launcher


class SnekLauncher(Launcher):
    name = "SnekMUD"
    cmdname = "snekmud"
    root = os.path.abspath(os.path.dirname(snekmud.__file__))

    game_template = os.path.abspath(
        os.path.join(
            os.path.abspath(os.path.dirname(snekmud.__file__)), "profile_template"
        )
    )
