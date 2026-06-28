from pydantic import BaseModel, Field

class CanvasElement(BaseModel):
    id: str
    type: str
    x: float = 0
    y: float = 0
    width: float = 120
    height: float = 60
    text: str | None = None
    start_id: str | None = None
    end_id: str | None = None

class CanvasElementUpdate(BaseModel):
    id: str
    type: str | None = None
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    text: str | None = None
    start_id: str | None = None
    end_id: str | None = None

class CanvasState(BaseModel):
    elements: dict[str, CanvasElement] = Field(default_factory=dict)

    def query(self) -> list[CanvasElement]:
        return list(self.elements.values())

    def add_elements(self, elements: list[CanvasElement]) -> list[CanvasElement]:
        for element in elements:
            self.elements[element.id] = element
        return elements
    
    def remove_elements(self, ids: list[str]) -> list[str]:
        removed: list[str] = []
        for element_id in ids:
            if element_id in self.elements:
                del self.elements[element_id]
                removed.append(element_id)
        return removed

    def to_elements(self) -> list[dict]:
        return [element.model_dump() for element in self.query()]

    def update_elements(self, updates: list[CanvasElementUpdate]) -> list[CanvasElement]:
        updated: list[CanvasElement] = []

        for update in updates:
            existing = self.elements.get(update.id)
            if existing is None:
                continue

            update_data = update.model_dump(
                exclude_unset=True,
                exclude_none=True,
                exclude={"id"},
            )
            new_data = existing.model_dump()
            new_data.update(update_data)
            self.elements[update.id] = CanvasElement(**new_data)
            updated.append(self.elements[update.id])

        return updated

    def find_overlaps(self) -> list[dict]:
        overlaps: list[dict] = []
        elements = [
            element
            for element in self.query()
            if element.type != "arrow"
        ]

        for index, first in enumerate(elements):
            for second in elements[index + 1:]:
                if _elements_overlap (first, second):
                    overlaps.append(
                        {
                            "first_id": first.id,
                            "second_id": second.id
                        }
                    )

        return overlaps

    def to_compact_text(self) -> str:
        parts: list[str] = []

        for element in self.query():
            if element.type == "arrow":
                parts.append(f"{element.id}: arrow {element.start_id}->{element.end_id}")
            else:
                label = element.text or element.id
                parts.append(
                    f"{element.id}: {element.type} '{label}' at ({element.x:g},{element.y:g})"
                )
        return "\n".join(parts)

    
def _elements_overlap(first: CanvasElement, second: CanvasElement) -> bool:
    first_right = first.x + first.width
    first_bottom = first.y + first.height
    second_right = second.x + second.width
    second_bottom = second.y + second.height

    return not (
        first_right <= second.x
        or second_right <= first.x 
        or first_bottom <= second.y
        or second_bottom <= first.y
    )
