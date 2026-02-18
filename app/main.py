from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from app.error_handelers import register_exception_handlers

from app.base_routes.endpoints import router as base_router
from app.v1.router import router as v1_router

from app.container import ApplicationContainer
from app.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    yield
    # Shutdown - close all resources
    if hasattr(app, "container"):
        container = app.container
        try:
            if hasattr(container, "whatsapp_http_client"):
                whatsapp_client = container.whatsapp_http_client()
                await whatsapp_client.close()
        except Exception:
            pass
        try:
            if hasattr(container, "redis_client"):
                redis = container.redis_client()
                await redis.close()
        except Exception:
            pass


def create_application() -> FastAPI:
    """Create FastAPI application with all configurations"""
    settings = get_settings()

    container = ApplicationContainer()
    # Build config dict from Pydantic settings (including computed properties)
    config_dict = settings.model_dump()
    config_dict["database_url"] = settings.database_url
    config_dict["redis_url"] = settings.redis_url
    container.config.from_dict(config_dict)

    container.wire(modules=["app.deps.providers"])
    container.wire(modules=["app.v1.users.deps.providers"])
    container.wire(modules=["app.v1.users.deps.get_current_user"])
    container.wire(modules=["app.v1.messaging.deps.providers"])
    container.wire(modules=["app.base_routes.endpoints"])
    container.wire(modules=["app.v1.users.routes.endpoints"])
    container.wire(modules=["app.v1.files.routes.endpoints"])
    container.wire(modules=["app.v1.messaging.routes.endpoints"])

    app = FastAPI(
        title="Messenger API",
        description="Multi-messenger platform API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.container = container

    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    # CORS: cannot use allow_origins=["*"] with allow_credentials=True
    cors_origins = settings.cors_origins
    allow_credentials = "*" not in cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(base_router, prefix="")
    app.include_router(v1_router)

    register_exception_handlers(app)

    return app


app = create_application()


def main():
    """Entry point for running the application"""
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=False, log_level="info"
    )


if __name__ == "__main__":
    main()
