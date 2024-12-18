from pydantic import BaseModel


class DeleteMasteredWordsInput(BaseModel):
    """The input data for delete mastered words."""

    words: list[str]
