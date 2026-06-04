from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class EventType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    REENTRY = "reentry"
    ZONE_ENTER = "zone_entered"
    ZONE_EXIT = "zone_exited"
    ZONE_DWELL = "zone_dwell"
    BILLING_QUEUE_JOIN = "billing_queue_join"
    BILLING_QUEUE_ABANDON = "queue_abandoned"
    BILLING_QUEUE_COMPLETED = "queue_completed"


class EventPayload(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    store_id: str = "ST1008"
    camera_id: Optional[str] = None
    visitor_id: Optional[str] = None   # ReID-stable global ID
    track_id: Optional[int] = None     # per-camera ByteTrack ID
    zone_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dwell_seconds: Optional[float] = None
    queue_depth: Optional[int] = None
    is_staff: bool = False
    embedding_hash: Optional[str] = None  # for idempotency
    x: Optional[float] = None
    y: Optional[float] = None
    confidence: Optional[float] = None
    metadata: Optional[dict] = None


class IngestResponse(BaseModel):
    accepted: int
    duplicate: int
    rejected: int


class MetricsResponse(BaseModel):
    store_id: str
    window_start: datetime
    window_end: datetime
    total_unique_visitors: int
    total_entries: int
    total_exits: int
    total_reentries: int
    staff_count: int
    conversion_rate: float
    avg_dwell_seconds: float
    queue_depth_current: int
    queue_completions: int
    queue_abandons: int


class FunnelStage(BaseModel):
    stage: str
    count: int
    drop_off: float  # percentage who dropped off at this stage


class FunnelResponse(BaseModel):
    store_id: str
    stages: List[FunnelStage]
    conversion_rate: float


class HeatmapResponse(BaseModel):
    store_id: str
    camera_id: Optional[str]
    grid: List[List[float]]   # normalized 0.0–1.0 intensity
    zone_labels: Optional[dict]


class AnomalyType(str, Enum):
    CROWD_SURGE = "crowd_surge"
    STALE_FEED = "stale_feed"
    LONG_QUEUE = "long_queue"
    UNUSUAL_DWELL = "unusual_dwell"


class AnomalyEvent(BaseModel):
    anomaly_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_id: str
    anomaly_type: AnomalyType
    description: str
    severity: str  # low / medium / high
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str   # ok / degraded / down
    db_connected: bool
    active_camera_feeds: int
    stale_feeds: List[str]
    last_event_at: Optional[datetime]
    uptime_seconds: float
