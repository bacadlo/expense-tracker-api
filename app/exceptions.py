from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class NotFoundException(Exception):
    def __init__(self, entity: str, entity_id: int):
        self.entity = entity
        self.entity_id = entity_id
        self.message = f"{entity} with id {entity_id} not found"


class ConflictException(Exception):
    def __init__(self, message: str):
        self.message = message


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundException)
    async def not_found_handler(request: Request, exc: NotFoundException):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(ConflictException)
    async def conflict_handler(request: Request, exc: ConflictException):
        return JSONResponse(status_code=409, content={"detail": exc.message})
