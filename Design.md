# Retail Store Intelligence System

## Architecture Overview

This project implements an end-to-end Retail Store Intelligence platform that transforms CCTV footage and POS transaction data into actionable business insights.

The primary objective is to measure the store's **Offline Conversion Rate** by correlating visitor behavior captured through video analytics with checkout activity recorded through POS transactions.

The solution follows an event-driven architecture consisting of four major layers:

1. Computer Vision Pipeline
2. Event Processing Layer
3. Analytics API Layer
4. Dashboard Visualization Layer

This separation allows video processing, analytics computation, and dashboard rendering to evolve independently while sharing a common event stream.

---

## 1. Computer Vision Pipeline

The computer vision pipeline is implemented in `pipeline/process_video.py`.

Each camera stream is processed independently and converted into structured behavioral events.

### Detection

Person detection is performed using **YOLOv8**, selected for its balance between accuracy, inference speed, and ease of deployment.

Only person detections are retained because visitor movement is the primary source of business intelligence in this challenge.

### Tracking

Detected visitors are tracked using **ByteTrack**.

Each individual receives a persistent tracking identifier which enables:

* Entry and exit counting
* Dwell-time measurement
* Queue monitoring
* Visitor journey reconstruction

To improve performance, frame skipping is used while preserving tracking continuity through ByteTrack.

---

## 2. Identity Tracking and Re-Identification

Retail environments frequently introduce:

* Occlusions
* Crowded aisles
* Temporary tracking loss
* Short-duration exits and re-entries

To reduce visitor double-counting, the system implements lightweight appearance-based re-identification.

For each visitor:

1. Appearance features are extracted from the person crop.
2. Features are stored in a temporary registry.
3. New tracks are compared against recently exited visitors.
4. Similar matches within a configurable time window are treated as re-entries.

This allows the platform to distinguish between:

* New visitors
* Returning visitors
* Tracking interruptions

without requiring a dedicated deep-learning ReID model.

---

## 3. Zone Analytics Layer

The physical store is represented as a collection of predefined operational zones.

Examples include:

* Entry Gates
* Shopping Areas
* Billing Counters
* Queue Zones

Visitor centroids are continuously evaluated against zone boundaries.

The system generates:

* `zone_entered`
* `zone_exited`
* `zone_dwell`

events whenever visitor movement intersects these zones.

These events become the foundation for:

* Funnel analytics
* Dwell-time calculations
* Heatmaps
* Conversion measurement

---

## 4. Staff Detection Layer

Store employees should not influence customer conversion metrics.

To prevent contamination of business KPIs, the system includes a dedicated staff-classification stage.

Classification uses multiple signals rather than relying on a single visual attribute.

Signals include:

* Presence within staff-only areas
* Long stationary durations
* Repetitive movement patterns
* Appearance-based indicators

Once identified, staff members are excluded from customer-focused analytics such as footfall, conversion rate, and dwell time.

---

## 5. Queue Analytics

Billing areas are treated as specialized operational zones.

The system tracks visitor interactions with checkout queues and generates events including:

* `billing_queue_join`
* `billing_queue_abandon`
* `queue_completed`

These events support:

* Queue depth measurement
* Queue abandonment analysis
* Checkout efficiency monitoring
* Purchase conversion estimation

---

## 6. Event Processing Layer

Rather than computing analytics directly from video frames, the system follows an event-driven design.

Every meaningful behavioral action is converted into a structured JSON event.

Examples include:

* `entry`
* `exit`
* `reentry`
* `zone_entered`
* `zone_exited`
* `billing_queue_join`
* `queue_completed`

Events are persisted to:

`data/output/events.jsonl`

This append-only event stream serves as the single source of truth for all analytics calculations.

### Benefits

* Decouples video processing from analytics
* Simplifies debugging
* Enables event replay
* Supports future streaming architectures
* Allows metrics to be recomputed without rerunning video processing

---

## 7. Analytics API Layer

The analytics backend is implemented using FastAPI.

The API consumes:

* Behavioral events from `events.jsonl`
* POS transaction records from CSV files

and exposes analytics endpoints used by the dashboard.

### Store Metrics

The metrics service computes:

* Footfall
* Staff count
* Conversion rate
* Queue metrics
* Re-entry counts
* Zone visit counts

### Funnel Analytics

Visitor journeys are reconstructed across store zones to generate a retail funnel:

Entry → Browsing → Billing → Purchase

The service calculates:

* Stage counts
* Drop-off counts
* Drop-off percentages
* Zone-level conversion metrics

### Heatmap Analytics

Visitor hotspot coordinates are aggregated into spatial distributions to identify highly visited store regions.

### Anomaly Detection

Operational monitoring includes:

* Stale camera feeds
* Queue spikes
* Sudden conversion drops

These alerts provide visibility into potential operational issues.

---

## 8. Dashboard Layer

The frontend is implemented using React and Material UI.

The dashboard combines camera analytics with POS analytics to provide a unified operational view.

### Camera Analytics

* Footfall
* Conversion Rate
* Funnel Performance
* Zone Activity
* Queue Metrics
* Heatmaps
* Re-entry Analytics

### POS Analytics

* Revenue
* Transactions
* Top Brands
* Top Products

The dashboard continuously refreshes and demonstrates live connectivity between the analytics engine and user interface.

---

# Edge-Case Mitigation Matrix

The challenge footage contains several real-world scenarios that can negatively impact analytics quality.

The pipeline includes explicit safeguards against these situations.

### Occlusion Recovery

Temporary tracking loss caused by shelves, crowds, or camera blind spots is handled through ByteTrack tracking continuity and appearance matching.

### Re-Entry Detection

Visitors who briefly leave and re-enter the store are matched against recently exited identities to prevent double counting.

### Staff Contamination

Employee movements are isolated from customer analytics through dedicated staff-classification logic.

### Queue Congestion

Queue join, completion, and abandonment events are tracked separately to maintain checkout visibility.

### Zone Boundary Noise

Zone transitions are only emitted when genuine movement between zones occurs, reducing duplicate counts caused by tracking jitter.

### End-of-Video Cleanup

Before pipeline shutdown, active tracks are finalized to prevent loss of dwell-time and conversion-related analytics.

---

# AI-Assisted Decisions

## 1. Event-Driven Architecture

**AI Recommendation:** Compute metrics directly inside the video processing pipeline.

**My Decision:** Overrode.

Instead of tightly coupling analytics to video processing, I implemented an event-driven architecture where the pipeline only generates events and analytics are calculated downstream.

This improves maintainability, debugging, and metric reproducibility.

---

## 2. Re-Identification Strategy

**AI Recommendation:** Use lightweight appearance-based re-identification instead of deploying a heavy deep-learning ReID network.

**My Decision:** Agreed.

Given the challenge constraints, HSV appearance matching provided a practical balance between implementation complexity and accuracy while still enabling re-entry detection.

---

## 3. Staff Detection Strategy

**AI Recommendation:** Use appearance cues as the primary staff identifier.

**My Decision:** Partially Overrode.

Appearance alone is unreliable in retail environments.

The final implementation combines appearance cues with behavioral signals such as dwell time, movement patterns, and staff-area presence to improve robustness.

---

## VLM Usage

No Vision Language Model (VLM) was used in the production pipeline.

Large Language Models were used exclusively as engineering assistants for architecture exploration, implementation review, debugging support, and documentation generation.

All runtime analytics are produced using computer vision models, tracking algorithms, event processing, and rule-based analytics.
