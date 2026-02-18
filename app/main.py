from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.exceptions import register_exception_handlers
from app.routers import analytics, budgets, categories, transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Budget & Expense Tracker API",
        description="REST API for tracking budgets and expenses with analytical endpoints",
        version="0.1.0",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.include_router(categories.router)
    app.include_router(transactions.router)
    app.include_router(budgets.router)
    app.include_router(analytics.router)

    return app


app = create_app()
