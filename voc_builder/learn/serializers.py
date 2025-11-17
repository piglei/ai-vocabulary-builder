import datetime

from pydantic import BaseModel


class DeleteMasteredWordsInput(BaseModel):
    """The input data for delete mastered words."""

    words: list[str]


class ExportAnkiInput(BaseModel):
    """The input data for exporting words as Anki deck."""

    start_date: datetime.date
    end_date: datetime.date
