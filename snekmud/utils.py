import os
import importlib
import logging
from pathlib import Path
from inspect import ismodule, trace, getmembers, getmodule, getmro
import types
from snekmud import WORLD
from snekmud.typing import Entity, GridCoordinates, SpaceCoordinates
import typing
import orjson
from ruamel.yaml import YAML

_Y = YAML(typ="safe")


def read_json_file(p: Path):
    return orjson.loads(open(p, mode='rb').read())


def read_yaml_file(p: Path):
    return _Y.load(open(p, mode="r"))


def read_data_file(p: Path):
    if p.name.lower().endswith(".json"):
        return read_json_file(p)
    elif p.name.lower().endswith(".yaml"):
        return read_yaml_file(p)
    return None


def get_or_emplace(ent: Entity, component: typing.Type) -> typing.Any:
    if (c := WORLD.try_component(ent, component)):
        return c
    c = component()
    WORLD.add_component(ent, c)
    return c


def mod_import_from_path(path):
    """
    Load a Python module at the specified path.
    Args:
        path (str): An absolute path to a Python module to load.
    Returns:
        (module or None): An imported module if the path was a valid
        Python module. Returns `None` if the import failed.
    """
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    dirpath, filename = path.rsplit(os.path.sep, 1)
    modname = filename.rstrip(".py")

    try:
        return importlib.machinery.SourceFileLoader(modname, path).load_module()
    except OSError:
        logging.error(f"Could not find module '{modname}' ({modname}.py) at path '{dirpath}'")
        return None


def mod_import(module):
    """
    A generic Python module loader.
    Args:
        module (str, module): This can be either a Python path
            (dot-notation like `evennia.objects.models`), an absolute path
            (e.g. `/home/eve/evennia/evennia/objects/models.py`) or an
            already imported module object (e.g. `models`)
    Returns:
        (module or None): An imported module. If the input argument was
        already a module, this is returned as-is, otherwise the path is
        parsed and imported. Returns `None` and logs error if import failed.
    """
    if not module:
        return None

    if isinstance(module, types.ModuleType):
        # if this is already a module, we are done
        return module

    if module.endswith(".py") and os.path.exists(module):
        return mod_import_from_path(module)

    try:
        return importlib.import_module(module)
    except ImportError:
        return None


def all_from_module(module):
    """
    Return all global-level variables defined in a module.
    Args:
        module (str, module): This can be either a Python path
            (dot-notation like `evennia.objects.models`), an absolute path
            (e.g. `/home/eve/evennia/evennia/objects.models.py`) or an
            already imported module object (e.g. `models`)
    Returns:
        variables (dict): A dict of {variablename: variable} for all
            variables in the given module.
    Notes:
        Ignores modules and variable names starting with an underscore.
    """
    mod = mod_import(module)
    if not mod:
        return {}
    # make sure to only return variables actually defined in this
    # module if available (try to avoid not imports)
    members = getmembers(mod, predicate=lambda obj: getmodule(obj) in (mod, None))
    return dict((key, val) for key, val in members if not key.startswith("_"))


def callables_from_module(module):
    """
    Return all global-level callables defined in a module.
    Args:
        module (str, module): A python-path to a module or an actual
            module object.
    Returns:
        callables (dict): A dict of {name: callable, ...} from the module.
    Notes:
        Will ignore callables whose names start with underscore "_".
    """
    mod = mod_import(module)
    if not mod:
        return {}
    # make sure to only return callables actually defined in this module (not imports)
    members = getmembers(mod, predicate=lambda obj: callable(obj) and getmodule(obj) == mod)
    return dict((key, val) for key, val in members if not key.startswith("_"))