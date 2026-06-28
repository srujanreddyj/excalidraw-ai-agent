from diagram_agent.canvas import CanvasElement, CanvasState, CanvasElementUpdate


def test_canvas_add_query_and_serialize() -> None:
    canvas = CanvasState()

    canvas.add_elements(
        [
            CanvasElement(id="user", type="rectangle", text="User"),
            CanvasElement(id="api", type="rectangle", x=200, text="API"),
        ]
    )

    elements = canvas.query()

    assert len(elements) == 2
    assert elements[0].id == "user"
    assert elements[1].id == "api"
    assert canvas.to_elements()[0]["text"] == "User"


def test_canvas_remove_elements() -> None:
    canvas = CanvasState()
    canvas.add_elements([CanvasElement(id="user", type="rectangle", text="User")])

    removed = canvas.remove_elements(["user", "missing"])

    assert removed == ["user"]
    assert canvas.query() == []

def test_canvas_update_elements() -> None:
    canvas = CanvasState()
    canvas.add_elements([CanvasElement(id="api", type="rectangle", text="API")])

    updated = canvas.update_elements(
        [
            CanvasElementUpdate(id="api", text="Auth API", x=240),
            CanvasElementUpdate(id="missing", text="Ignored"),
        ]
    )

    assert len(updated) == 1
    assert updated[0].id == "api"
    assert updated[0].text == "Auth API"
    assert updated[0].x == 240
    assert canvas.elements["api"].text == "Auth API"


def test_canvas_find_overlaps_detects_overlapping_shapes() -> None:
    canvas = CanvasState()
    canvas.add_elements(
        [
            CanvasElement(id="a", type="rectangle", x=0, y=0, width=100, height=100),
            CanvasElement(id="b", type="rectangle", x=50, y=50, width=100, height=100),
        ]
    )

    assert canvas.find_overlaps() == [{"first_id": "a", "second_id": "b"}]


def test_canvas_find_overlaps_ignores_arrows() -> None:
    canvas = CanvasState()
    canvas.add_elements(
        [
            CanvasElement(id="a", type="rectangle", x=0, y=0, width=100, height=100),
            CanvasElement(id="arrow", type="arrow", x=0, y=0, width=100, height=100),
        ]
    )

    assert canvas.find_overlaps() == []


def test_canvas_compact_text_serializes_nodes_and_arrows() -> None:
    canvas = CanvasState()
    canvas.add_elements(
        [
            CanvasElement(id="user", type="rectangle", text="User"),
            CanvasElement(id="api", type="rectangle", x=220, text="API"),
            CanvasElement(
                id="user_to_api",
                type="arrow",
                start_id="user",
                end_id="api",
            ),
        ]
    )

    assert canvas.to_compact_text() == "\n".join(
        [
            "user: rectangle 'User' at (0,0)",
            "api: rectangle 'API' at (220,0)",
            "user_to_api: arrow user->api",
        ]
    )