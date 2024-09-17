from pydantic import BaseModel

class ToBeRankedTextList(BaseModel):
    texts: list[str]
    folds: int
    groups: int
