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
from mudforge.utils import make_iter
from server.conf import settings
import textwrap
import re
from ast import literal_eval
from simpleeval import simple_eval
import json


class OrJSONEncoder(json.JSONEncoder):
    def encode(self, o) -> str:
        return orjson.dumps(o, option=orjson.OPT_INDENT_2).decode(encoding="utf-8")


class OrJSONDecoder(json.JSONDecoder):
    def decode(self, s: str, _w = ...):
        return orjson.loads(s)


def read_json_file(p: Path):
    data = open(p, mode='rb').read()
    if not data:
        return None
    return orjson.loads(data)


def write_json_file(p: Path, data):
    with open(p, mode="wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))


def get_or_emplace(ent: Entity, component: typing.Type) -> typing.Any:
    if (c := WORLD.try_component(ent, component)):
        return c
    c = component()
    WORLD.add_component(ent, c)
    if (func := getattr(c, "at_post_deserialize", None)):
        func(ent)
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

def variable_from_module(module, variable=None, default=None):
    """
    Retrieve a variable or list of variables from a module. The
    variable(s) must be defined globally in the module. If no variable
    is given (or a list entry is `None`), all global variables are
    extracted from the module.

    Args:
      module (string or module): Python path, absolute path or a module.
      variable (string or iterable, optional): Single variable name or iterable
          of variable names to extract. If not given, all variables in
          the module will be returned.
      default (string, optional): Default value to use if a variable fails to
          be extracted. Ignored if `variable` is not given.

    Returns:
        variables (value or list): A single value or a list of values
        depending on if `variable` is given or not. Errors in lists
        are replaced by the `default` argument.

    """

    if not module:
        return default

    mod = mod_import(module)

    if not mod:
        return default

    if variable:
        result = []
        for var in make_iter(variable):
            if var:
                # try to pick a named variable
                result.append(mod.__dict__.get(var, default))
    else:
        # get all
        result = [
            val for key, val in mod.__dict__.items() if not (key.startswith("_") or ismodule(val))
        ]

    if len(result) == 1:
        return result[0]
    return result




def to_str(text, session=None):
    """
    Try to decode a bytestream to a python str, using encoding schemas from settings
    or from Session. Will always return a str(), also if not given a str/bytes.

    Args:
        text (any): The text to encode to bytes. If a str, return it. If also not bytes, convert
            to str using str() or repr() as a fallback.
        session (Session, optional): A Session to get encoding info from. Will try this before
            falling back to settings.ENCODINGS.

    Returns:
        decoded_text (str): The decoded text.

    Notes:
        If `text` is already str, return it as is.
    """
    if isinstance(text, str):
        return text
    if not isinstance(text, bytes):
        # not a byte, convert directly to str
        try:
            return str(text)
        except Exception:
            return repr(text)

    default_encoding = session.protocol_flags.get("ENCODING", "utf-8") if session else "utf-8"
    try:
        return text.decode(default_encoding)
    except (LookupError, UnicodeDecodeError):
        for encoding in settings.ENCODINGS:
            try:
                return text.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                pass
        # no valid encoding found. Replace unconvertable parts with ?
        return text.decode(default_encoding, errors="replace")


def wrap(text, width=None, indent=0):
    """
    Safely wrap text to a certain number of characters.

    Args:
        text (str): The text to wrap.
        width (int, optional): The number of characters to wrap to.
        indent (int): How much to indent each line (with whitespace).

    Returns:
        text (str): Properly wrapped text.

    """
    width = width if width else settings.CLIENT_DEFAULT_WIDTH
    if not text:
        return ""
    indent = " " * indent
    return to_str(textwrap.fill(text, width, initial_indent=indent, subsequent_indent=indent))


# alias - fill
fill = wrap


def pad(text, width=None, align="c", fillchar=" "):
    """
    Pads to a given width.

    Args:
        text (str): Text to pad.
        width (int, optional): The width to pad to, in characters.
        align (str, optional): This is one of 'c', 'l' or 'r' (center,
            left or right).
        fillchar (str, optional): The character to fill with.

    Returns:
        text (str): The padded text.

    """
    width = width if width else settings.CLIENT_DEFAULT_WIDTH
    align = align if align in ("c", "l", "r") else "c"
    fillchar = fillchar[0] if fillchar else " "
    if align == "l":
        return text.ljust(width, fillchar)
    elif align == "r":
        return text.rjust(width, fillchar)
    else:
        return text.center(width, fillchar)


def crop(text, width=None, suffix="[...]"):
    """
    Crop text to a certain width, throwing away text from too-long
    lines.

    Args:
        text (str): Text to crop.
        width (int, optional): Width of line to crop, in characters.
        suffix (str, optional): This is appended to the end of cropped
            lines to show that the line actually continues. Cropping
            will be done so that the suffix will also fit within the
            given width. If width is too small to fit both crop and
            suffix, the suffix will be dropped.

    Returns:
        text (str): The cropped text.

    """
    width = width if width else settings.CLIENT_DEFAULT_WIDTH
    ltext = len(text)
    if ltext <= width:
        return text
    else:
        lsuffix = len(suffix)
        text = text[:width] if lsuffix >= width else "%s%s" % (text[: width - lsuffix], suffix)
        return to_str(text)


def dedent(text, baseline_index=None, indent=None):
    """
    Safely clean all whitespace at the left of a paragraph.

    Args:
        text (str): The text to dedent.
        baseline_index (int, optional): Which row to use as a 'base'
            for the indentation. Lines will be dedented to this level but
            no further. If None, indent so as to completely deindent the
            least indented text.
        indent (int, optional): If given, force all lines to this indent.
            This bypasses `baseline_index`.

    Returns:
        text (str): Dedented string.

    Notes:
        This is useful for preserving triple-quoted string indentation
        while still shifting it all to be next to the left edge of the
        display.

    """
    if not text:
        return ""
    if indent is not None:
        lines = text.split("\n")
        ind = " " * indent
        indline = "\n" + ind
        return ind + indline.join(line.strip() for line in lines)
    elif baseline_index is None:
        return textwrap.dedent(text)
    else:
        lines = text.split("\n")
        baseline = lines[baseline_index]
        spaceremove = len(baseline) - len(baseline.lstrip(" "))
        return "\n".join(
            line[min(spaceremove, len(line) - len(line.lstrip(" "))) :] for line in lines
        )


def justify(text, width=None, align="f", indent=0):
    """
    Fully justify a text so that it fits inside `width`. When using
    full justification (default) this will be done by padding between
    words with extra whitespace where necessary. Paragraphs will
    be retained.

    Args:
        text (str): Text to justify.
        width (int, optional): The length of each line, in characters.
        align (str, optional): The alignment, 'l', 'c', 'r' or 'f'
            for left, center, right or full justification respectively.
        indent (int, optional): Number of characters indentation of
            entire justified text block.

    Returns:
        justified (str): The justified and indented block of text.

    """
    width = width if width else settings.CLIENT_DEFAULT_WIDTH

    def _process_line(line):
        """
        helper function that distributes extra spaces between words. The number
        of gaps is nwords - 1 but must be at least 1 for single-word lines. We
        distribute odd spaces randomly to one of the gaps.
        """
        line_rest = width - (wlen + ngaps)
        gap = " "  # minimum gap between words
        if line_rest > 0:
            if align == "l":
                if line[-1] == "\n\n":
                    line[-1] = " " * (line_rest - 1) + "\n" + " " * width + "\n" + " " * width
                else:
                    line[-1] += " " * line_rest
            elif align == "r":
                line[0] = " " * line_rest + line[0]
            elif align == "c":
                pad = " " * (line_rest // 2)
                line[0] = pad + line[0]
                if line[-1] == "\n\n":
                    line[-1] += (
                        pad + " " * (line_rest % 2 - 1) + "\n" + " " * width + "\n" + " " * width
                    )
                else:
                    line[-1] = line[-1] + pad + " " * (line_rest % 2)
            else:  # align 'f'
                gap += " " * (line_rest // max(1, ngaps))
                rest_gap = line_rest % max(1, ngaps)
                for i in range(rest_gap):
                    line[i] += " "
        elif not any(line):
            return [" " * width]
        return gap.join(line)

    # split into paragraphs and words
    paragraphs = re.split("\n\s*?\n", text, re.MULTILINE)
    words = []
    for ip, paragraph in enumerate(paragraphs):
        if ip > 0:
            words.append(("\n", 0))
        words.extend((word, len(word)) for word in paragraph.split())
    ngaps, wlen, line = 0, 0, []

    lines = []
    while words:
        if not line:
            # start a new line
            word = words.pop(0)
            wlen = word[1]
            line.append(word[0])
        elif (words[0][1] + wlen + ngaps) >= width:
            # next word would exceed word length of line + smallest gaps
            lines.append(_process_line(line))
            ngaps, wlen, line = 0, 0, []
        else:
            # put a new word on the line
            word = words.pop(0)
            line.append(word[0])
            if word[1] == 0:
                # a new paragraph, process immediately
                lines.append(_process_line(line))
                ngaps, wlen, line = 0, 0, []
            else:
                wlen += word[1]
                ngaps += 1

    if line:  # catch any line left behind
        lines.append(_process_line(line))
    indentstring = " " * indent
    return "\n".join([indentstring + line for line in lines])


def columnize(string, columns=2, spacing=4, align="l", width=None):
    """
    Break a string into a number of columns, using as little
    vertical space as possible.

    Args:
        string (str): The string to columnize.
        columns (int, optional): The number of columns to use.
        spacing (int, optional): How much space to have between columns.
        width (int, optional): The max width of the columns.
            Defaults to client's default width.

    Returns:
        columns (str): Text divided into columns.

    Raises:
        RuntimeError: If given invalid values.

    """
    columns = max(1, columns)
    spacing = max(1, spacing)
    width = width if width else settings.CLIENT_DEFAULT_WIDTH

    w_spaces = (columns - 1) * spacing
    w_txt = max(1, width - w_spaces)

    if w_spaces + columns > width:  # require at least 1 char per column
        raise RuntimeError("Width too small to fit columns")

    colwidth = int(w_txt / (1.0 * columns))

    # first make a single column which we then split
    onecol = justify(string, width=colwidth, align=align)
    onecol = onecol.split("\n")

    nrows, dangling = divmod(len(onecol), columns)
    nrows = [nrows + 1 if i < dangling else nrows for i in range(columns)]

    height = max(nrows)
    cols = []
    istart = 0
    for irows in nrows:
        cols.append(onecol[istart : istart + irows])
        istart = istart + irows
    for col in cols:
        if len(col) < height:
            col.append(" " * colwidth)

    sep = " " * spacing
    rows = []
    for irow in range(height):
        rows.append(sep.join(col[irow] for col in cols))

    return "\n".join(rows)

def safe_convert_to_types(converters, *args, raise_errors=True, **kwargs):
    """
    Helper function to safely convert inputs to expected data types.

    Args:
        converters (tuple): A tuple `((converter, converter,...), {kwarg: converter, ...})` to
            match a converter to each element in `*args` and `**kwargs`.
            Each converter will will be called with the arg/kwarg-value as the only argument.
            If there are too few converters given, the others will simply not be converter. If the
            converter is given as the string 'py', it attempts to run
            `safe_eval`/`literal_eval` on  the input arg or kwarg value. It's possible to
            skip the arg/kwarg part of the tuple, an empty tuple/dict will then be assumed.
        *args: The arguments to convert with `argtypes`.
        raise_errors (bool, optional): If set, raise any errors. This will
            abort the conversion at that arg/kwarg. Otherwise, just skip the
            conversion of the failing arg/kwarg. This will be set by the FuncParser if
            this is used as a part of a FuncParser callable.
        **kwargs: The kwargs to convert with `kwargtypes`

    Returns:
        tuple: `(args, kwargs)` in converted form.

    Raises:
        utils.funcparser.ParsingError: If parsing failed in the `'py'`
            converter. This also makes this compatible with the FuncParser
            interface.
        any: Any other exception raised from other converters, if raise_errors is True.

    Notes:
        This function is often used to validate/convert input from untrusted sources. For
        security, the "py"-converter is deliberately limited and uses `safe_eval`/`literal_eval`
        which  only supports simple expressions or simple containers with literals. NEVER
        use the python `eval` or `exec` methods as a converter for any untrusted input! Allowing
        untrusted sources to execute arbitrary python on your server is a severe security risk,

    Example:
    ::

        $funcname(1, 2, 3.0, c=[1,2,3])

        def _funcname(*args, **kwargs):
            args, kwargs = safe_convert_input(((int, int, float), {'c': 'py'}), *args, **kwargs)
            # ...

    """

    def _safe_eval(inp):
        if not inp:
            return ""
        if not isinstance(inp, str):
            # already converted
            return inp

        try:
            return literal_eval(inp)
        except Exception as err:
            literal_err = f"{err.__class__.__name__}: {err}"
            try:
                return simple_eval(inp)
            except Exception as err:
                simple_err = f"{str(err.__class__.__name__)}: {err}"
                pass

        if raise_errors:
            from .funcparser import ParsingError

            err = (
                f"Errors converting '{inp}' to python:\n"
                f"literal_eval raised {literal_err}\n"
                f"simple_eval raised {simple_err}"
            )
            raise ParsingError(err)

    # handle an incomplete/mixed set of input converters
    if not converters:
        return args, kwargs
    arg_converters, *kwarg_converters = converters
    arg_converters = make_iter(arg_converters)
    kwarg_converters = kwarg_converters[0] if kwarg_converters else {}

    # apply the converters
    if args and arg_converters:
        args = list(args)
        arg_converters = make_iter(arg_converters)
        for iarg, arg in enumerate(args[: len(arg_converters)]):
            converter = arg_converters[iarg]
            converter = _safe_eval if converter in ("py", "python") else converter
            try:
                args[iarg] = converter(arg)
            except Exception:
                if raise_errors:
                    raise
        args = tuple(args)
    if kwarg_converters and isinstance(kwarg_converters, dict):
        for key, converter in kwarg_converters.items():
            converter = _safe_eval if converter in ("py", "python") else converter
            if key in {**kwargs}:
                try:
                    kwargs[key] = converter(kwargs[key])
                except Exception:
                    if raise_errors:
                        raise
    return args, kwargs


def copy_word_case(base_word, new_word):
    """
    Converts a word to use the same capitalization as a first word.

    Args:
        base_word (str): A word to get the capitalization from.
        new_word (str): A new word to capitalize in the same way as `base_word`.

    Returns:
        str: The `new_word` with capitalization matching the first word.

    Notes:
        This is meant for words. Longer sentences may get unexpected results.

        If the two words have a mix of capital/lower letters _and_ `new_word`
        is longer than `base_word`, the excess will retain its original case.

    """

    # Word
    if base_word.istitle():
        return new_word.title()
    # word
    elif base_word.islower():
        return new_word.lower()
    # WORD
    elif base_word.isupper():
        return new_word.upper()
    else:
        # WorD - a mix. Handle each character
        maxlen = len(base_word)
        shared, excess = new_word[:maxlen], new_word[maxlen - 1 :]
        return (
            "".join(
                char.upper() if base_word[ic].isupper() else char.lower()
                for ic, char in enumerate(new_word)
            )
            + excess
        )