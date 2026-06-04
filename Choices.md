# CHOICES.md

# Design Choices and Trade-offs

This document describes three major architectural decisions made during development, the alternatives considered, how AI tools influenced the decision, and the final rationale.

---

# 1. Detection and Tracking Model Selection

## Options Considered

### Option A: YOLOv8 + ByteTrack

* Fast real-time object detection
* Mature tracking ecosystem
* Easy integration with Ultralytics
* Works well on CPU and entry-level GPUs

### Option B: RT-DETR

* Transformer-based detector
* Strong detection accuracy
* Better handling of crowded scenes
* Higher computational requirements

### Option C: DeepSORT + YOLO

* Popular tracking pipeline
* Appearance-based tracking
* Additional embedding computation required

---

## AI Suggestion

The AI suggested experimenting with transformer-based detectors such as RT-DETR because they can improve detection quality in crowded retail environments.

The AI also suggested DeepSORT as an alternative tracking framework because it includes appearance-based association.

---

## Final Choice

**YOLOv8 Nano (yolov8n.pt) with ByteTrack**

---

## Why This Choice

The challenge required processing multiple retail camera streams while maintaining acceptable runtime performance.

YOLOv8 Nano provided:

* Fast inference speed
* Low memory usage
* Simple deployment
* Reliable person detection

ByteTrack was selected because:

* It performs well in crowded environments
* It is lightweight
* It integrates directly with Ultralytics tracking APIs

The combination provided a good balance between accuracy and processing speed without requiring dedicated GPU infrastructure.

---

# 2. Event Schema Design

## Options Considered

### Option A: Frame-Level Analytics

Store every frame result and calculate analytics directly from detections.

Example:

* Bounding boxes
* Track states
* Frame timestamps

Pros:

* Maximum detail

Cons:

* Large storage footprint
* Expensive analytics computations

---

### Option B: Event-Driven Architecture

Convert important visitor actions into business events.

Examples:

* entry
* exit
* reentry
* zone_entered
* zone_exited
* zone_dwell
* billing_queue_join
* queue_completed

Store events as JSON lines.

Pros:

* Compact storage
* Easier analytics
* Faster dashboard queries

Cons:

* Less raw visual information

---

## AI Suggestion

The AI initially suggested a normalized schema where events would only store references and relationships, requiring analytics modules to join multiple data sources later.

---

## Final Choice

**Self-contained event documents stored in JSONL format**

---

## Why This Choice

The dashboard requires near real-time analytics such as:

* Footfall
* Funnel conversion
* Zone analytics
* Heatmaps
* Queue monitoring

Self-contained event records allow analytics modules to process events directly without complex joins.

A single event contains all information needed for downstream processing, including:

* Visitor ID
* Store ID
* Camera ID
* Zone information
* Timestamps
* Dwell duration
* Queue information

This simplified implementation and reduced dashboard response time.

---

# 3. API Architecture Choice

## Options Considered

### Option A: Flask + SQL Database

Pros:

* Familiar architecture
* Strong database support

Cons:

* Additional database setup
* More infrastructure overhead
* Slower development cycle

---

### Option B: FastAPI + Event File Processing

Pros:

* Automatic OpenAPI documentation
* Async support
* Simple deployment
* Fast implementation

Cons:

* Analytics computed from event files
* Less scalable than a dedicated database

---

## AI Suggestion

The AI suggested using a relational database such as PostgreSQL to persist events and calculate analytics through SQL queries.

---

## Final Choice

**FastAPI with event-based processing using events.jsonl**

---

## Why This Choice

The challenge emphasizes rapid prototyping and analytics generation rather than large-scale production deployment.

Using FastAPI allowed:

* Fast API development
* Automatic documentation
* Simple REST endpoint creation
* Easy frontend integration

The event stream stored in `events.jsonl` became the system's source of truth.

Analytics modules consume this event stream to calculate:

* Store metrics
* Conversion funnels
* Heatmaps
* Queue statistics
* Anomaly detection

This approach reduced infrastructure complexity while remaining fully aligned with the challenge requirements.

---

# Additional Engineering Decisions

## Appearance-Based Re-Identification

A full deep-learning ReID model was considered.

However:

* Deep ReID models increase latency
* Additional training data is required
* GPU resources become necessary

Instead, HSV histogram similarity was used to reconnect recently exited visitors and detect re-entries.

This lightweight approach provided acceptable performance for the challenge dataset.

---

## Frame Skipping Strategy

The pipeline processes every second frame.

Reasoning:

* Reduces computation by roughly 50%
* Maintains tracking continuity
* Improves processing speed

ByteTrack is able to maintain identities despite the reduced frame rate.

---

## Staff Detection Strategy

Instead of relying solely on appearance, a multi-signal approach was used.

Signals include:

* Storage-area presence
* Long dwell duration
* Repeated movement patterns
* Appearance characteristics

Combining multiple signals reduces false positives and better reflects real-world store behavior.
## Frame Skipping Strategy

The pipeline processes every second frame (SKIP = 2).

Options considered:

- Process every frame
- Process every second frame

AI Suggestion:
The AI recommended processing every frame to maximize detection accuracy.

Final Choice:
Process every second frame.

Why:
This reduced computation significantly while maintaining stable tracking through ByteTrack. For retail movement patterns, the accuracy impact was negligible while processing speed improved substantially.