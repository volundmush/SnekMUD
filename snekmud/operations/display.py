from mudforge.utils import make_iter, is_iter
from snekmud.typing import Entity
from snekmud import COMPONENTS, WORLD, OPERATIONS, MODULES
from rich.text import Text

class GetDisplayName:

    def __init__(self, viewer, target, rich=False, plain=False, **kwargs):
        self.viewer = viewer
        self.target = target
        self.kwargs = kwargs
        self.rich = rich
        self.plain = plain

    async def execute(self):
        if (name := WORLD.try_component(self.target, COMPONENTS["Name"])):
            if self.rich:
                return name.rich
            if self.plain:
                return name.plain
            return name.color
        elif (comp := WORLD.try_component(self.target, COMPONENTS["EntityID"])):
            fmt = f"{comp.module_name}/{comp.ent_id}"
        else:
            fmt = f"Entity {self.target}"
        if self.rich:
            return Text(fmt)
        return fmt


class DistributeMessage:

    def __init__(self, text: str, recipients: list[Entity], msg_type=None, from_obj=None, mapping=None, oob=None,
                 check_visible: bool = False, **kwargs):
        """
        Render and distribute a message to all recipients.

        Args:
            text (str): Message to send. The message will be parsed for `{key}` formatting and
                `$You/$you()/$You()`, `$obj(name)`, `$conj(verb)` and `$pron(pronoun, option)`
                inline function callables.
                The `name` is taken from the `mapping` kwarg {"name": object, ...}`.
                The operation `GetDisplayName(viewer=recipient)` will be called
                for that key for every recipient of the string.
            msg_type (str, optional): The msg_type, used for determining what sort of message
                it is. If set, operational hooks will be called to filter or mutate the message.
            from_obj (Entity, optional): An object designated as the
                "sender" of the message. Used for formatting
            mapping (dict, optional): A mapping of formatting keys
                `{"key":<object>, "key2":<object2>,...}.
                The keys must either match `{key}` or `$You(key)/$you(key)` markers
                in the `text` string. If not set, a key `you` will
                be auto-added to point to `from_obj` if given.
            oob (dict, optional): Any OOB data that should be sent with the formatted message.
                This will only be sent if the message itself is.
            check_visible (bool): If True, recipients who cannot detect from_obj will be excluded.
            **kwargs: Keyword arguments retained for any overloading.
        """
        self.text = text
        self.recipients = recipients
        self.from_obj = from_obj
        self.mapping = mapping
        self.oob = oob
        self.check_visible = check_visible
        self.kwargs = kwargs

    async def execute(self):
        pass

class MsgContents:
    """
    Emits a message to all objects inside this object.
    """

    def __init__(self, ent, text=None, msg_type=None, exclude=None, from_obj=None, mapping=None, oob=None,
                 check_visible: bool = False, **kwargs):
        self.ent = ent
        self.text = text
        self.msg_type = msg_type
        self.exclude = make_iter(exclude) if exclude is not None else []
        self.from_obj = from_obj
        self.mapping = mapping
        self.oob = oob
        self.check_visible = check_visible
        self.kwargs = kwargs

    async def execute(self):
        contents = await OPERATIONS["GetContents"](self.ent).execute()
        for x in self.exclude:
            if x in contents:
                contents.remove(x)
        await OPERATIONS["DistributeMessage"](self.text, contents, msg_type=self.msg_type, from_obj=self.from_obj,
                                              mapping=self.mapping, oob=self.oob, check_visible=self.check_visible,
                                              **self.kwargs).execute()


class DisplayRoom:

    def __init__(self, viewer, room, **kwargs):
        self.viewer = viewer
        self.room = room
        self.kwargs = kwargs

    async def execute(self):
        pass


class DisplayInRoom:

    def __init__(self, viewer, room, entity, **kwargs):
        self.viewer = viewer
        self.room = room
        self.entity = entity
        self.kwargs = kwargs

    async def execute(self):
        if (long := WORLD.try_component(self.entity, COMPONENTS["LongDescription"])) and long.plain:
            return long.rich
        return Text(f"Entity {self.entity} is here.")
