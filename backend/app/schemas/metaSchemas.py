from pydantic import BaseModel


class OptionItem(BaseModel):
    value: str
    label: str


class OptionsResponse(BaseModel):
    ageRanges: list[OptionItem]
    durations: list[OptionItem]
    warningSigns: list[OptionItem]
