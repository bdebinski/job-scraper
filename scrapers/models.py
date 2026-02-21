from pydantic import BaseModel
from typing import Optional


class JobOffer(BaseModel):
    employer: Optional[str] = None
    position: str
    salary: str
    requirements: str
    url: str
    description: str
    status: str
