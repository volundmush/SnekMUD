from mudforge.utils import make_iter, is_iter
from snekmud.typing import Entity
from snekmud import COMPONENTS, WORLD, OPERATIONS, MODULES, GETTERS
from rich.text import Text
from server.conf import settings
from snekmud import funcparser
from snekmud.utils import get_or_emplace


# init the actor-stance funcparser for msg_contents
_MSG_CONTENTS_PARSER = funcparser.FuncParser(funcparser.ACTOR_STANCE_CALLABLES)


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
        self.msg_type = msg_type
        self.kwargs = kwargs

    async def execute(self):
        # we also accept an outcommand on the form (message, {kwargs})
        is_outcmd = self.text and is_iter(self.text)
        inmessage = self.text[0] if is_outcmd else self.text
        outkwargs = self.text[1] if is_outcmd and len(self.text) > 1 else {}
        mapping = self.mapping or {}
        you = self.from_obj

        if "you" not in mapping:
            mapping["you"] = you

        print(f"MAPPING: {mapping}")

        recv_comp = COMPONENTS["Receiver"]
        print(f"Distributing to: {self.recipients}")
        for receiver in self.recipients:
            # actor-stance replacements
            send_message = _MSG_CONTENTS_PARSER.parse(
                inmessage,
                raise_errors=True,
                return_string=True,
                caller=you,
                receiver=receiver,
                mapping=mapping,
            )

            # director-stance replacements
            outmessage = send_message.format_map(
                {
                    key: GETTERS["GetDisplayName"](receiver, obj).execute()
                    if WORLD.entity_exists(obj)
                    else str(obj)
                    for key, obj in mapping.items()
                }
            )
            print(f"sending to {receiver}")
            recv = get_or_emplace(receiver, recv_comp)
            recv.receive(outmessage, from_ent=you, msg_type=self.msg_type, **self.kwargs)


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
        contents = GETTERS["GetContents"](self.ent).execute()
        for x in self.exclude:
            if x in contents:
                contents.remove(x)
        await OPERATIONS["DistributeMessage"](self.text, contents, msg_type=self.msg_type, from_obj=self.from_obj,
                                              mapping=self.mapping, oob=self.oob, check_visible=self.check_visible,
                                              **self.kwargs).execute()


class Say:

    def __init__(self, speaker, dialogue: str, **kwargs):
        self.speaker = speaker
        self.dialogue = dialogue
        self.kwargs = kwargs

    def format_msg(self):
        return f'$You() $conj(says), "{self.dialogue}"'

    async def execute(self):
        formatted = self.format_msg()
        room = GETTERS["GetRoomLocation"](self.speaker).execute()
        await OPERATIONS["MsgContents"](room, text=formatted, msg_type="say", from_obj=self.speaker, **self.kwargs).execute()