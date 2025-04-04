from starlette.middleware.base import RequestResponseEndpoint
from fastapi import Request, Response
from app.auth import get_user_from_session

async def add_user_to_request_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
    if "session" in request.scope:
        request.state.user = await get_user_from_session(request.session)
    else:
        request.state.user = None

    response = await call_next(request)
    return response
