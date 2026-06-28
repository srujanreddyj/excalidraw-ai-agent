import modal


image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi>=0.124.0",
        "openai>=2.38.0",
        "pydantic>=2.13.4",
        "python-dotenv>=1.2.2",
    )
    .add_local_dir("src", remote_path="/root/src")
    .env({"PYTHONPATH": "/root/src"})
)

app = modal.App("diagram-agent-api")


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("diagram-agent-secrets")],
    timeout=60,
    scaledown_window=60,
)
@modal.asgi_app()
def fastapi_app():
    from diagram_agent.api import app as fastapi_api

    return fastapi_api
