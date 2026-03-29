from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class Statement:
    label: str | None
    line_no: int


@dataclass(frozen=True)
class In(Statement):
    name: str


@dataclass(frozen=True)
class Out(Statement):
    pass


@dataclass(frozen=True)
class Step(Statement):
    op: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class Fork(Statement):
    depth: int
    raw_depth: str
    branch_names: tuple[str, ...]


@dataclass(frozen=True)
class Merge(Statement):
    mode: str
    branch_names: tuple[str, ...]
    output_keys: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Record(Statement):
    output_name: str
    branch_names: tuple[str, ...]
    field_keys: tuple[str, ...]


@dataclass(frozen=True)
class Back(Statement):
    target_label: str


@dataclass(frozen=True)
class ShapeDecl(Statement):
    paths: tuple[str, ...]


@dataclass(frozen=True)
class Bridge(Statement):
    runtime: str
    source: str


StatementT: TypeAlias = In | Out | Step | Fork | Merge | Record | Back | ShapeDecl | Bridge


@dataclass(frozen=True)
class Branch:
    name: str
    flow: tuple[StatementT, ...]
    line_no: int


@dataclass(frozen=True)
class Program:
    main_flow: tuple[StatementT, ...]
    branches: dict[str, Branch]
    source: str
