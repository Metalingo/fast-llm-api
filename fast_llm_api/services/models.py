import uuid
from pydantic import BaseModel, Field
from typing import Optional, List


class EloFightSetting(BaseModel):
    texts: List[str]
    folds: Optional[int]
    groups: Optional[int]

class OneStudentEntry(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    answer: str

    class Config:
        extra = "allow"  # Allows dynamic field creation

    # Add __getitem__ to allow subscripting
    def __getitem__(self, item):
        return getattr(self, item)
    
    # Add __setitem__ to allow subscripting (for setting values)
    def __setitem__(self, key, value):
        setattr(self, key, value)

