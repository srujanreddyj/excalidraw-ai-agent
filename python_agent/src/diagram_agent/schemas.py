from typing import Literal
from pydantic import BaseModel, Field, model_validator

ElementType = Literal["rectangle", "ellipse", "diamond", "arrow", "text"]

class LabelSpec(BaseModel):
    text: str
    fontSize: float | None = None
    textAlign: Literal["left", "center", "right"] | None = None

class EndpointSpec(BaseModel):
    id: str

class ElementSpec(BaseModel):
    id: str
    type: ElementType
    x: float = 0
    y: float = 0
    width: float = 120
    height: float = 60
    label: LabelSpec | None = None
    text: str | None = None
    start: EndpointSpec | None = None
    end: EndpointSpec | None = None
    start_id: str | None = None
    end_id: str | None = None

    @model_validator(mode="after")
    def _normalize_endpoints(self) -> "ElementSpec":
        if self.start is None and self.start_id:
            self.start = EndpointSpec(id=self.start_id)
        if self.end is None and self.end_id:
            self.end = EndpointSpec(id=self.end_id)
        return self

class ElementUpdateSpec(BaseModel):
    id: str
    type: ElementType | None = None
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    label: LabelSpec | None = None
    text: str | None = None
    start: EndpointSpec | None = None
    end: EndpointSpec | None = None
    start_id: str | None = None
    end_id: str | None = None

    @model_validator(mode="after")
    def _normalize_endpoints(self) -> "ElementUpdateSpec":
        if self.start is None and self.start_id:
            self.start = EndpointSpec(id=self.start_id)
        if self.end is None and self.end_id:
            self.end = EndpointSpec(id=self.end_id)
        return self

class AddElementsInput(BaseModel):
    elements: list[ElementSpec] = Field(min_length=1)

class UpdateElementsInput(BaseModel):
    updates: list[ElementUpdateSpec] = Field(min_length=1)

class RemoveElementsInput(BaseModel):
    ids: list[str] = Field(min_length=1)