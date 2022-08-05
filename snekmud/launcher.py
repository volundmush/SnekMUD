import os
import sys
import snekmud
from mudforge.launcher import Launcher


class SnekLauncher(Launcher):
    name = "SnekMUD"
    cmdname = "snekmud"
    root = os.path.abspath(os.path.dirname(snekmud.__file__))

    game_template = os.path.abspath(
        os.path.join(
            os.path.abspath(os.path.dirname(snekmud.__file__)), "game_template"
        )
    )

    def operation_passthru(self, op, args, unknown):
        self.tb_show_locals = False
        self.set_profile_path(args)
        os.chdir(self.profile_path)
        sys.path.insert(0, os.getcwd())

        import django
        from django.conf import settings
        from server.conf import django_settings
        settings.configure(default_settings=django_settings)
        django.setup()
        from django.core.management import call_command
        call_command(op, *unknown)