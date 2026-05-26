from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectSource:
    name: str
    read_only: bool


LOCAL_SOURCE = ProjectSource(name="local", read_only=False)
UNIPORTAL_SOURCE = ProjectSource(name="uniportal", read_only=True)
