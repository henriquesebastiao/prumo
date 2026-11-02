"""FastAPI dependencies that belong to the infrastructure.

The authenticated user (`CurrentUser`) lives in `prumo.system.auth.deps`, because `core` must not
import `system`.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from prumo.core.db import get_session

SessionDep = Annotated[Session, Depends(get_session)]
