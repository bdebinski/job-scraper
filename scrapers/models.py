from pydantic import BaseModel, Field
from typing import Optional

class JobOffer(BaseModel):
    employer: Optional[str] = None
    position: str
    salary: str
    requirements: str
    url: str
