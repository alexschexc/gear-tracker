from dataclasses import dataclass


@dataclass
class ImportResult:
    success: bool
    total_rows: int
    imported: int
    skipped: int
    overwritten: int
    errors: list[str]
    warnings: list[str]
    entity_stats: dict[str, int]


@dataclass
class ValidationError:
    row_number: int
    entity_type: str
    field_name: str
    error_type: str
    message: str
    severity: str


@dataclass
class ImportRowResult:
    row_number: int
    entity_type: str
    action: str
    error_message: str | None = None
