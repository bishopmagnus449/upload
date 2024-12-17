from enum import Enum
from dataclasses import dataclass
from typing import Optional


class Contact(Enum):
    FIRST_NAME = 'First Name'
    LAST_NAME = 'Last Name'
    EMAIL = 'Email'
    BIRTH_DATE = 'Date of Birth'
    PHONE_NUMBER = 'Phone Number'
    ADDRESS = 'Address'


class _BaseAttachment:
    pass


@dataclass
class _FileAttachment(_BaseAttachment):
    file_path: str
    file_name: str
    mime_type: str = None


@dataclass
class _ImageAttachment(_BaseAttachment):
    file_path: str
    custom_tag: str
    file_name: Optional[str] = None
    is_inline = False


@dataclass
class _InlineImageAttachment(_BaseAttachment):
    file_path: str
    custom_tag: str
    file_name: Optional[str] = None
    is_inline = True


class Attachment:
    File = _FileAttachment
    InlineImage = _InlineImageAttachment
    Base64Image = _ImageAttachment
