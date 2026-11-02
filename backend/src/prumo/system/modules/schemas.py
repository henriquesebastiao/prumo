from pydantic import BaseModel, Field


class ModuleRead(BaseModel):
    id: str = Field(examples=["finance"])
    version: str
    enabled: bool = Field(
        description="Enabled for the current user (a preference, not a permission)."
    )
    position: int = Field(description="Position in the user's navigation and dashboard order.")


class ModuleList(BaseModel):
    items: list[ModuleRead]
