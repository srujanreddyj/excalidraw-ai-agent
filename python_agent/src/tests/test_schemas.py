import pytest
from pydantic import ValidationError

from diagram_agent.schemas import AddElementsInput, ElementSpec, RemoveElementsInput


def test_add_elements_input_accepts_supported_element_types() -> None:
    parsed = AddElementsInput(
        elements=[
            ElementSpec(id="user", type="rectangle", text="User"),
            ElementSpec(id="db", type="ellipse", text="Database"),
        ]
    )

    assert parsed.elements[0].type == "rectangle"
    assert parsed.elements[1].text == "Database"


def test_add_elements_input_rejects_unknown_element_type() -> None:
    with pytest.raises(ValidationError):
        AddElementsInput(elements=[{"id": "bad", "type": "hexagon"}])


def test_remove_elements_input_requires_at_least_one_id() -> None:
    with pytest.raises(ValidationError):
        RemoveElementsInput(ids=[])

def test_add_elements_input_accepts_label_and_arrow_bindings() -> None:
    parsed = AddElementsInput(
        elements=[
            {
                "id": "rect_user",
                "type": "rectangle",
                "label": {"text": "User"},
            },
            {
                "id": "rect_api",
                "type": "rectangle",
                "x": 320,
                "label": {"text": "API"},
            },
            {
                "id": "arrow_user_api",
                "type": "arrow",
                "start": {"id": "rect_user"},
                "end": {"id": "rect_api"},
            },
        ]
    )

    assert parsed.elements[0].label is not None
    assert parsed.elements[0].label.text == "User"
    assert parsed.elements[2].start is not None
    assert parsed.elements[2].start.id == "rect_user"