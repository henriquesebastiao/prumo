from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.core.idempotency import create_once, created_responses
from prumo.core.pagination import Page, PageDep, Sort, UpdatedSince, sort_param
from prumo.modules.studies import service
from prumo.modules.studies.models import StudyArea, StudyPlan, StudySession, Subject, Topic
from prumo.modules.studies.schemas import (
    AreaCreate,
    AreaRead,
    AreaUpdate,
    DayRead,
    PlanBlocksWrite,
    PlanInForce,
    PlanList,
    PlanRead,
    PlanWrite,
    StudiesOverview,
    StudySessionCreate,
    StudySessionRead,
    StudySessionUpdate,
    SubjectCreate,
    SubjectDetail,
    SubjectRead,
    SubjectUpdate,
    TopicList,
    WeekRead,
)
from prumo.system.auth.deps import CurrentUser

router = APIRouter(responses=error_responses(401, 403, 404, 422))

Archived = Annotated[
    Literal["false", "true", "all"],
    Query(description="Archived ones too (`all`) or only them (`true`)."),
]
SubjectSort = Annotated[Sort, Depends(sort_param("name", "created_at", default="name"))]
SessionSort = Annotated[Sort, Depends(sort_param("started_at", default="-started_at"))]


def _area(area_id: UUID, session: SessionDep, user: CurrentUser) -> StudyArea:
    return service.get_area(session, user, area_id)


def _subject(subject_id: UUID, session: SessionDep, user: CurrentUser) -> Subject:
    return service.get_subject(session, user, subject_id)


def _topic(topic_id: UUID, session: SessionDep, user: CurrentUser) -> Topic:
    return service.get_topic(session, user, topic_id)


def _plan(plan_id: UUID, session: SessionDep, user: CurrentUser) -> StudyPlan:
    return service.get_plan(session, user, plan_id)


def _study_session(session_id: UUID, session: SessionDep, user: CurrentUser) -> StudySession:
    return service.get_session(session, user, session_id)


AreaDep = Annotated[StudyArea, Depends(_area)]
SubjectDep = Annotated[Subject, Depends(_subject)]
TopicDep = Annotated[Topic, Depends(_topic)]
PlanDep = Annotated[StudyPlan, Depends(_plan)]
StudySessionDep = Annotated[StudySession, Depends(_study_session)]


@router.get("/overview")
def read_overview(session: SessionDep, user: CurrentUser) -> StudiesOverview:
    """Active areas and subjects, and the sessions of this month."""
    return service.overview(session, user)


@router.get("/day")
def read_day(
    session: SessionDep,
    user: CurrentUser,
    on: Annotated[date | None, Query(description="Defaults to today.")] = None,
) -> DayRead:
    """E2-E5: each subject's goal, minutes done and status on a day."""
    return service.day(session, user, on)


@router.get("/week")
def read_week(
    session: SessionDep,
    user: CurrentUser,
    start: Annotated[
        date | None, Query(description="Any day of the week; defaults to this week.")
    ] = None,
) -> WeekRead:
    """E6: the seven days, with the totals in all and by subject."""
    return service.week(session, user, start)


# ---------------------------------------------------------------- areas


@router.get("/areas")
def list_areas(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    archived: Archived = "false",
    updated_since: UpdatedSince = None,
) -> Page[AreaRead]:
    return service.list_areas(session, user, page, archived=archived, updated_since=updated_since)


@router.post("/areas", status_code=status.HTTP_201_CREATED, responses=created_responses(AreaRead))
def create_area(
    data: AreaCreate, session: SessionDep, user: CurrentUser, response: Response
) -> AreaRead:
    area = create_once(
        session,
        StudyArea,
        user.id,
        data.id,
        response,
        lambda: service.create_area(session, user, data),
    )
    return service.area_reads(session, user, [area])[0]


@router.get("/areas/{area_id}")
def read_area(area: AreaDep, session: SessionDep, user: CurrentUser) -> AreaRead:
    return service.area_reads(session, user, [area])[0]


@router.patch("/areas/{area_id}")
def update_area(
    data: AreaUpdate, area: AreaDep, session: SessionDep, user: CurrentUser
) -> AreaRead:
    return service.area_reads(session, user, [service.update_area(session, area, data)])[0]


@router.post("/areas/{area_id}/archive")
def archive_area(area: AreaDep, session: SessionDep, user: CurrentUser) -> AreaRead:
    return service.area_reads(session, user, [service.set_area_archived(session, area, True)])[0]


@router.post("/areas/{area_id}/unarchive")
def unarchive_area(area: AreaDep, session: SessionDep, user: CurrentUser) -> AreaRead:
    return service.area_reads(session, user, [service.set_area_archived(session, area, False)])[0]


@router.delete("/areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_area(area: AreaDep, session: SessionDep, user: CurrentUser) -> None:
    """E9: only an area without subjects."""
    service.delete_area(session, user, area)


# ---------------------------------------------------------------- subjects


@router.get("/subjects")
def list_subjects(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    sort: SubjectSort,
    area_id: UUID | None = None,
    archived: Archived = "false",
    q: Annotated[str | None, Query(max_length=60, description="Name.")] = None,
    updated_since: UpdatedSince = None,
) -> Page[SubjectRead]:
    return service.list_subjects(
        session,
        user,
        page,
        area_id=area_id,
        archived=archived,
        q=q,
        sort=sort,
        updated_since=updated_since,
    )


@router.post(
    "/subjects", status_code=status.HTTP_201_CREATED, responses=created_responses(SubjectRead)
)
def create_subject(
    data: SubjectCreate, session: SessionDep, user: CurrentUser, response: Response
) -> SubjectRead:
    subject = create_once(
        session,
        Subject,
        user.id,
        data.id,
        response,
        lambda: service.create_subject(session, user, data),
    )
    return service.subject_read(session, user, subject)


@router.get("/subjects/{subject_id}")
def read_subject(subject: SubjectDep, session: SessionDep, user: CurrentUser) -> SubjectDetail:
    """With its topics, minutes per week (E7) and recent sessions."""
    return service.subject_detail(session, user, subject)


@router.patch("/subjects/{subject_id}")
def update_subject(
    data: SubjectUpdate, subject: SubjectDep, session: SessionDep, user: CurrentUser
) -> SubjectRead:
    return service.subject_read(session, user, service.update_subject(session, user, subject, data))


@router.post("/subjects/{subject_id}/archive")
def archive_subject(subject: SubjectDep, session: SessionDep, user: CurrentUser) -> SubjectRead:
    return service.subject_read(session, user, service.set_subject_archived(session, subject, True))


@router.post("/subjects/{subject_id}/unarchive")
def unarchive_subject(subject: SubjectDep, session: SessionDep, user: CurrentUser) -> SubjectRead:
    return service.subject_read(
        session, user, service.set_subject_archived(session, subject, False)
    )


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject: SubjectDep, session: SessionDep) -> None:
    """E9: removes the subject with its topics, sessions and plan blocks."""
    service.delete_subject(session, subject)


@router.get("/subjects/{subject_id}/topics")
def list_topics(subject: SubjectDep, session: SessionDep) -> TopicList:
    return TopicList(items=service.topic_reads(session, subject))


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(topic: TopicDep, session: SessionDep) -> None:
    """E10: only a topic without sessions."""
    service.delete_topic(session, topic)


# ---------------------------------------------------------------- plans (E1)


@router.get("/plans")
def list_plans(session: SessionDep, user: CurrentUser) -> PlanList:
    """Every version, newest first."""
    return service.list_plans(session, user)


@router.get("/plan")
def read_plan_in_force(
    session: SessionDep,
    user: CurrentUser,
    on: Annotated[date | None, Query(description="Defaults to today.")] = None,
) -> PlanInForce:
    """E1: the version in force on a day."""
    return service.plan_in_force(session, user, on)


@router.post(
    "/plans",
    status_code=status.HTTP_201_CREATED,
    responses={**created_responses(PlanRead), **error_responses(409)},
)
def create_plan(
    data: PlanWrite, session: SessionDep, user: CurrentUser, response: Response
) -> PlanRead:
    """A new version from `valid_from` (today or later)."""
    plan = create_once(
        session,
        StudyPlan,
        user.id,
        data.id,
        response,
        lambda: service.create_plan(session, user, data.valid_from, data.blocks, plan_id=data.id),
    )
    return service.plan_read(session, user, plan)


@router.get("/plans/{plan_id}")
def read_plan(plan: PlanDep, session: SessionDep, user: CurrentUser) -> PlanRead:
    return service.plan_read(session, user, plan)


@router.put("/plans/{plan_id}")
def update_plan(
    data: PlanBlocksWrite, plan: PlanDep, session: SessionDep, user: CurrentUser
) -> PlanRead:
    """Replaces the blocks of a version not yet in force."""
    return service.plan_read(session, user, service.update_plan(session, user, plan, data))


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan: PlanDep, session: SessionDep, user: CurrentUser) -> None:
    service.delete_plan(session, user, plan)


# ---------------------------------------------------------------- sessions


@router.get("/sessions")
def list_sessions(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    sort: SessionSort,
    subject_id: UUID | None = None,
    from_on: Annotated[date | None, Query(alias="from")] = None,
    to_on: Annotated[date | None, Query(alias="to")] = None,
    updated_since: UpdatedSince = None,
) -> Page[StudySessionRead]:
    return service.list_sessions(
        session,
        user,
        page,
        subject_id=subject_id,
        from_on=from_on,
        to_on=to_on,
        sort=sort,
        updated_since=updated_since,
    )


@router.post(
    "/sessions", status_code=status.HTTP_201_CREATED, responses=created_responses(StudySessionRead)
)
def create_session(
    data: StudySessionCreate, session: SessionDep, user: CurrentUser, response: Response
) -> StudySessionRead:
    """E3, E10: a session; `topic_name` creates the topic."""
    item = create_once(
        session,
        StudySession,
        user.id,
        data.id,
        response,
        lambda: service.create_session(session, user, data),
    )
    return service.session_read(session, user, item)


@router.get("/sessions/{session_id}")
def read_session(item: StudySessionDep, session: SessionDep, user: CurrentUser) -> StudySessionRead:
    return service.session_read(session, user, item)


@router.patch("/sessions/{session_id}")
def update_session(
    data: StudySessionUpdate, item: StudySessionDep, session: SessionDep, user: CurrentUser
) -> StudySessionRead:
    return service.session_read(session, user, service.update_session(session, user, item, data))


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(item: StudySessionDep, session: SessionDep) -> None:
    service.delete_session(session, item)
