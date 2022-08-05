from snekmud.db.accounts.models import Account
from enum import IntEnum
from django.core.exceptions import ValidationError
from snekmud.exceptions import CommandError
from .conn_base import ConnParser
from django.core.validators import EmailValidator

_email_valid = EmailValidator()


class LoginState(IntEnum):
    NAME = 0
    CONFNAME = 1
    PASSWORD = 2
    CONFPASS = 3
    EMAIL = 4
    CONFEMAIL = 5


class LoginParser(ConnParser):

    def __init__(self, conn):
        super().__init__(conn)
        self.user_data = {}
        self.state = LoginState.NAME
        self.account = None

        self.state_map = {
            LoginState.NAME: self.parse_name,
            LoginState.CONFNAME: self.parse_confname,
            LoginState.PASSWORD: self.parse_password,
            LoginState.CONFPASS: self.parse_confpass,
            LoginState.EMAIL: self.parse_email,
            LoginState.CONFEMAIL: self.parse_confemail
        }

    def send_greet(self):
        pass

    async def start(self):
        self.send_circle("\r\n@cEnter your desired username or the username you have already made.\r\n@CEnter Username:")
        self.user_data.clear()
        self.account = None
        self.state = LoginState.NAME

    async def parse(self, s: str):
        if s.lower == "return":
            await self.start()
            return

        try:
            await self.state_map[self.state](s)
        except CommandError as err:
            self.send(str(err))
        except ValidationError as err:
            self.send(str(err))

    async def parse_name(self, s):
        Account.username_validator(s)

        if account := Account.objects.filter(username__iexact=s).first():
            self.account = account
            self.user_data.clear()
            self.state = LoginState.PASSWORD
            self.send("Please enter password or 'return' to cancel.")
            self.send("Password:")
        else:
            self.user_data["username"] = s
            self.state = LoginState.CONFNAME
            self.send(f"Please confirm username ({s}):")

    async def parse_confname(self, s):
        try:
            if s != self.user_data["username"]:
                raise CommandError("Usernames do not match!")

            self.state = LoginState.PASSWORD
            self.send("Please enter password or 'return' to cancel.")
            self.send("Password:")
        except CommandError as err:
            self.send(str(err))
            self.user_data.clear()
            self.state = LoginState.NAME
            self.send("Enter Username:")

    async def parse_password(self, s):
        if self.account:
            if self.account.check_password(s):
                await self.conn.login_as(self.account)
                return
            else:
                self.send("That was not the correct password.")
                self.send("Password:")
                return
        else:
            if not s:
                self.send("Please enter a password.")
                self.send("Password:")
                return
            self.user_data["password"] = s
            self.state = LoginState.CONFPASS
            self.send("Got it. Please enter password again to verify:")


    async def parse_confpass(self, s):
        if s == self.user_data["password"]:
            self.state = LoginState.EMAIL
            self.send("ALmost done! Now please provide an email address. Or, type 'return' to cancel.")
            self.send("Email:")
            return

        self.send("Passwords did not match. Let's try that again.")
        self.send("Password:")
        self.state = LoginState.PASSWORD

    async def parse_email(self, s):
        try:
            _email_valid(s)
            self.user_data["email"] = s
            self.state = LoginState.CONFEMAIL
            self.send("One last time, please verify that email address for us.")
            self.send("Email:")
        except ValidationError as err:
            self.send(str(err))
            self.send("That doesn't look like an email address. Please try again.")
            self.send("Email:")

    async def parse_confemail(self, s):
        if s != self.user_data["email"]:
            self.send("Those emails didn't match. Let's try again.")
            self.send("Email:")
            self.state = LoginState.EMAIL
            return

        acc = Account.objects.create_user(**self.user_data)
        await self.conn.login_as(acc)