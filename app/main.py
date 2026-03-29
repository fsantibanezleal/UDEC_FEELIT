"""FeelIT FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import APP_DESCRIPTION, APP_NAME, APP_VERSION
from app.haptics.factory import create_haptic_backend

static_dir = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage application startup and shutdown resources."""
    application.state.haptic_backend = create_haptic_backend()
    application.state.haptic_backend.start()
    try:
        yield
    finally:
        application.state.haptic_backend.stop()


def serve_static_page(filename: str) -> FileResponse:
    """Serve a named static HTML page from the frontend bundle."""
    return FileResponse(static_dir / filename)


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", include_in_schema=False)
async def index() -> RedirectResponse:
    """Redirect the root path to the current default user workspace."""
    return RedirectResponse(url="/braille-reader", status_code=307)


@app.get("/object-explorer", include_in_schema=False)
async def object_explorer_page() -> FileResponse:
    """Serve the 3D object explorer workspace."""
    return serve_static_page("object_explorer.html")


@app.get("/braille-reader", include_in_schema=False)
async def braille_reader_page() -> FileResponse:
    """Serve the Braille reader workspace."""
    return serve_static_page("braille_reader.html")


@app.get("/haptic-desktop", include_in_schema=False)
async def haptic_desktop_page() -> FileResponse:
    """Serve the haptic desktop workspace."""
    return serve_static_page("haptic_desktop.html")


@app.get("/haptic-workspace-manager", include_in_schema=False)
async def haptic_workspace_manager_page() -> FileResponse:
    """Serve the haptic workspace management page."""
    return serve_static_page("haptic_workspace_manager.html")


app.mount("/static", StaticFiles(directory=static_dir), name="static")
