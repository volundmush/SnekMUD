from snekmud.utils import callables_from_module
import snekmud
import mudforge
import os
import sys


def early_launch():
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    import django
    from django.conf import settings
    from server.conf import django_settings
    settings.configure(default_settings=django_settings)
    django.setup()


async def pre_start(entrypoint=None, services=None):
    mod_paths = mudforge.CONFIG.MODIFIERS

    for mod_path in mod_paths:
        for k, v in callables_from_module(mod_path).items():
            snekmud.MODIFIERS_NAMES[v.category][v.get_name()] = v
            snekmud.MODIFIERS_ID[v.category][v.modifier_id] = v

    for com_path in mudforge.CONFIG.COMPONENTS:
        snekmud.COMPONENTS.update(callables_from_module(com_path))

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

    for p in mudforge.CONFIG.EQUIP_CLASS_PATHS:
        slots = callables_from_module(p)
        for k, v in slots.items():
            if not v.key and v.category:
                continue
            snekmud.EQUIP_SLOTS[v.category][v.key] = v

    for op_path in mudforge.CONFIG.OPERATION_CLASS_PATHS:
        snekmud.OPERATIONS.update({k: v for k, v in callables_from_module(op_path).items() if hasattr(v, "execute")})