import json

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import RedirectResponse, Response

templates = Jinja2Templates(directory="app/templates")
templates.env.filters["escapejs"] = lambda v: json.dumps(str(v))[1:-1]


def render_template(template_name: str, request: Request, context: dict) -> Response:
    user = getattr(request.state, "user", None)
    context["user"] = user
    context["request"] = request
    context["flash"] = get_flashed_message(request)
    return templates.TemplateResponse(template_name, context)


def redirect_back(
    request: Request, fallback_url: str = "/", status_code: int = status.HTTP_302_FOUND
) -> RedirectResponse:
    ref = request.headers.get("referer")
    return RedirectResponse(ref or fallback_url, status_code=status.HTTP_302_FOUND)


def flash(request: Request, message: str, category: str = "info"):
    """Store a flash message in session."""
    request.session["_flash"] = {"message": message, "category": category}


def get_flashed_message(request: Request):
    """Retrieve and remove flash message from session."""
    return request.session.pop("_flash", None)
