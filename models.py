# Standard Library Imports
from typing import Optional

# Third Party Imports
from pydantic import BaseModel

# Applications Imports
from constants import STARTING_CREDITS


class User(BaseModel):
    user_name: str
    api_key: str
    credits: Optional[int] = STARTING_CREDITS
