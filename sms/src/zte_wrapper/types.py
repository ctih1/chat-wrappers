from dataclasses import dataclass

PhoneNumber = str

class AuthError(Exception): pass

@dataclass
class SMSMessage:
    content: str
    tag: int
    id: int
