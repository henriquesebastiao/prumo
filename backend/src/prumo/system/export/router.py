from fastapi import APIRouter, Response

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.system.auth.deps import CurrentUser
from prumo.system.export import service

router = APIRouter(tags=["users"], responses=error_responses(401, 403))


@router.get(
    "/me/export",
    response_class=Response,
    responses={200: {"content": {"application/zip": {}}, "description": "The ZIP archive."}},
)
def export_data(session: SessionDep, user: CurrentUser) -> Response:
    """Every record of the user (D38): `data.json`, one CSV per table and the uploaded files."""
    name, archive = service.build_archive(session, user)
    return Response(
        archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{name}"',
            "Cache-Control": "no-store",
        },
    )
