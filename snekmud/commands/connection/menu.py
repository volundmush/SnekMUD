import re
import snekmud
from mudforge.utils import partial_match
from rich.text import Text

from snekmud.commands.base import Command, CommandException

class AccountMenuCommand(Command):
    help_category = "Account Menu"


class CharCreateCommand(AccountMenuCommand):
    name = "@charcreate"
    syntax = "@charcreate <name>"
    re_match = re.compile(
        r"^(?P<cmd>@charcreate)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE
    )
    character_type = "PLAYER"

    async def execute(self):
        mdict = self.match_obj.groupdict()
        if not (name := mdict.get("args", None)):
            raise CommandException("Must enter a name for the character!")
        character = await snekmud.GAME.characters.create(name, self.entry.connection.account)
        await self.entry.connection.msg(line=f"{Character} '{char}' created! Use " + Text(f'''@ic {char}''', style='bold') + " to join the game!")




class CharSelectCommand(AccountMenuCommand):
    name = "@ic"
    syntax = "@ic <name>"
    re_match = re.compile(r"^(?P<cmd>@ic)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)
    character_type = "PLAYER"

    async def execute(self):
        mdict = self.match_obj.groupdict()
        acc = self.entry.connection.account

        if not (chars := acc.get_characters()):
            raise CommandException("No characters to join the game as!")
        if not (args := mdict.get("args", None)):
            names = ", ".join([str(obj) for obj in chars])
            await self.entry.connection.msg(text=f"You have the following characters: {names}")
            return
        if not (found := partial_match(args, chars)):
            await self.entry.connection.msg(text=f"Sorry, no character found named: {args}")
            return
        await snekmud.GAME.create_or_join_session(self.entry, found)


class SelectScreenCommand(AccountMenuCommand):
    name = "look"
    syntax = "look"
    re_match = re.compile(r"^(?P<cmd>look)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    async def execute(self):
        screen = await self.entry.connection.user.login_screen(self.entry.connection)
        await self.entry.connection.msg(line=screen, system_msg=True)


class LogoutCommand(AccountMenuCommand):
    name = "@logout"
    syntax = "@logout"
    re_match = re.compile(r"^(?P<cmd>@logout)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    async def execute(self):
        await self.entry.connection.logout()
        screen = await self.entry.connection.welcome_screen()
        await self.entry.connection.msg(line=screen, system_msg=True)


MENU_COMMANDS = [CharCreateCommand, CharSelectCommand, SelectScreenCommand, LogoutCommand]

