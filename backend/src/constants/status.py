from enum import StrEnum
class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
class CorrectionStatus(StrEnum):
    APPLIED = "applied"
    REJECTED = "rejected"
class NoteStatus(StrEnum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
