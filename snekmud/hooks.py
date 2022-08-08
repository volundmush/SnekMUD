from snekmud.utils import callables_from_module
from mudforge.utils import import_from_module
import snekmud
import mudforge
import os
import logging


def setup_django():
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    import django
    from django.conf import settings
    from server.conf import django_settings
    settings.configure(default_settings=django_settings)
    django.setup()


def load_modifiers():
    mod_paths = mudforge.CONFIG.MODIFIERS

    for mod_path in mod_paths:
        for k, v in callables_from_module(mod_path).items():
            snekmud.MODIFIERS_NAMES[v.category][v.get_name()] = v
            snekmud.MODIFIERS_ID[v.category][v.modifier_id] = v


def load_components():
    for com_path in mudforge.CONFIG.COMPONENTS:
        snekmud.COMPONENTS.update(callables_from_module(com_path))


def load_commands():
    # load command classes.
    for cmd_path in mudforge.CONFIG.COMMAND_PATHS:
        for k, v in callables_from_module(cmd_path).items():
            if not hasattr(v, "execute"):
                continue
            for sub in v.sub_categories:
                snekmud.COMMANDS[v.main_category][sub].append(v)

    # now to sort the commands.
    for k, v in snekmud.COMMANDS.items():
        for subcat, cmds in v.items():
            cmds.sort(key=lambda x: x.priority)


def load_equip():
    for p in mudforge.CONFIG.EQUIP_CLASS_PATHS:
        slots = callables_from_module(p)
        for k, v in slots.items():
            if not v.key and v.category:
                continue
            snekmud.EQUIP_SLOTS[v.category][v.key] = v


def load_cmdhandlers():
    for category, v in mudforge.CONFIG.CMDHANDLERS.items():
        for sub_category, path in v.items():
            snekmud.CMDHANDLERS[category][sub_category] = import_from_module(path)


def load_operations():
    for op_path in mudforge.CONFIG.OPERATION_CLASS_PATHS:
        snekmud.OPERATIONS.update({k: v for k, v in callables_from_module(op_path).items() if hasattr(v, "execute")})


def load_meta():
    for meta_type, paths in mudforge.CONFIG.METATYPE_INTEGRITY.items():
        for p in paths:
            snekmud.METATYPE_INTEGRITY[meta_type].append(import_from_module(p))


def clean_gamesessions():
    from snekmud.db.gamesessions.models import GameSession
    GameSession.objects.all().delete()


def early_launch():
    setup_django()
    load_modifiers()
    load_components()
    load_commands()
    load_equip()
    load_cmdhandlers()
    load_operations()
    load_meta()

    snekmud.PY_DICT["snekmud"] = snekmud
    snekmud.PY_DICT["mudforge"] = mudforge


def cold_start():
    clean_gamesessions()


def copyover(data_dict):
    from snekmud.db.gamesessions.models import GameSession

    sessions = dict()

    for x in GameSession.objects.all():
        sessions[x.id.id] = x.handler.copyover_export()
    data_dict["sessions"] = sessions


async def copyover_recover_stage_2(data_dict):
    from snekmud.db.gamesessions.models import GameSession

    for k, v in data_dict.pop("sessions", dict()).items():
        if (sess := GameSession.objects.filter(id=k).first()):
            await sess.handler.copyover_recover(v)