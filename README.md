# RetailIQ - AI Powered Retail Store Intelligence Platform

## Overview

RetailIQ is an AI-powered retail analytics platform that transforms CCTV footage and POS transaction data into actionable business intelligence.

The system processes retail surveillance videos using computer vision, generates structured behavioral events, correlates them with transaction data, and exposes analytics through REST APIs and an interactive dashboard.

RetailIQ helps retailers understand customer behavior, store performance, operational bottlenecks, and conversion trends without requiring manual observation.

The project was developed as part of the Purplle Retail Intelligence Challenge.

---

# Core Objective

The primary objective of RetailIQ is to measure and improve the **Offline Store Conversion Rate**.

## North Star Metric

The primary metric driving the platform is the Offline Store Conversion Rate.

Conversion Rate =
Converted Customer Sessions ÷ Unique Non-Staff Visitor Sessions

A visitor is considered converted when the system detects a completed purchase through one of the following signals:

1. Queue completion events.
2. POS transaction matching within a configurable time window.
3. Billing queue participation without abandonment.

Staff members are excluded from both the numerator and denominator to prevent operational activity from inflating customer conversion metrics.


---

# Key Features

## Computer Vision Analytics

* Real-time person detection using YOLOv8
* Multi-object tracking using ByteTrack
* Visitor re-identification
* Customer movement tracking
* Zone activity analysis
* Billing queue monitoring
* Staff detection and exclusion
* Heatmap generation

---

## Customer Journey Analytics

Track customer movement through:

```text
Store Entry
      ↓
Zone Browsing
      ↓
Billing Queue
      ↓
Purchase
```

The system calculates:

* Funnel progression
* Drop-off rates
* Zone conversion performance
* Attention-without-sales zones

---

## Business Intelligence

Integrated POS analytics provide:

* Revenue tracking
* Transaction counts
* Top-performing brands
* Top-performing products
* Conversion measurement
* Customer-to-purchase correlation

---

## Operational Monitoring

Monitor store operations through:

* Queue length monitoring
* Queue abandonment analysis
* Dwell time analytics
* Camera feed health checks
* Conversion drop alerts
* Queue spike alerts
* Stale feed detection

---

# System Architecture

The platform consists of four major layers.

---

## 1. Video Analytics Layer

Implemented in:

```text
pipeline/process_video.py
```

This layer processes CCTV footage and performs:

### Detection

YOLOv8 detects people in video frames.

### Tracking

ByteTrack assigns persistent track IDs to visitors.

### Re-Identification

When tracking temporarily breaks because of:

* Occlusions
* Crowded scenes
* Temporary camera loss

the system compares appearance signatures using HSV color histograms and reconnects identities.

### Zone Mapping

Customer centroids are mapped to predefined store zones including:

* Entry Gates
* Browsing Areas
* Billing Zones
* Storage Areas

### Staff Classification

Staff members are identified using behavioral and spatial signals and are excluded from customer conversion calculations.

---

## 2. Event Processing Layer

The platform follows an event-driven architecture.

Instead of directly calculating analytics from video frames, all customer actions are converted into structured events.

Examples include:

```text
ENTRY
EXIT
REENTRY
ZONE_ENTER
ZONE_EXIT
ZONE_DWELL
BILLING_QUEUE_JOIN
QUEUE_COMPLETED
```

Events are written into:

```text
data/output/events.jsonl
```

Benefits:

* Decouples analytics from video processing
* Easier debugging
* Supports replayability
* Enables future streaming pipelines
* Simplifies testing

---

## 3. Analytics API Layer

Implemented using FastAPI.

The backend consumes:

* Event data from events.jsonl
* POS transaction data from CSV datasets

### Available APIs

#### Health

```http
GET /health
```

Returns system health status.

---

#### Dashboard

```http
GET /dashboard
```

Returns consolidated dashboard analytics.

---

#### Metrics

```http
GET /stores/{store_id}/metrics
```

Returns:

* Footfall
* Staff count
* Conversion rate
* Queue metrics
* Re-entry metrics

---

#### Funnel

```http
GET /stores/{store_id}/funnel
```

Returns:

* Customer journey stages
* Funnel progression
* Drop-off counts
* Drop-off rates
* Zone conversion analysis

---

#### Heatmap

```http
GET /stores/{store_id}/heatmap
```

Returns hotspot distributions for store activity visualization.

---

#### Anomalies

```http
GET /stores/{store_id}/anomalies
```

Returns:

* Queue spikes
* Conversion drops
* Stale camera feeds

---

## 4. Dashboard Layer

Implemented using:

* React
* Vite
* Material UI
* Recharts

The dashboard visualizes both operational and business metrics.

### Dashboard KPIs

* Revenue
* Transactions
* Footfall
* Conversion Rate
* Average Dwell Time

### Dashboard Visualizations

* Conversion Funnel
* Top Brands
* Top Products
* Zone Activity
* Heatmaps
* Diagnostics

---

# Technology Stack

## Backend

* Python
* FastAPI
* Pandas
* NumPy

## Computer Vision

* YOLOv8
* ByteTrack
* OpenCV
* Ultralytics

## Frontend

* React
* Vite
* Material UI
* Recharts
* Axios

## Storage

* JSONL Event Stream
* CSV POS Data

## Deployment

* Docker
* Docker Compose

---

# Project Structure

```text
store-intelligence/
│
├── app/
│   ├── main.py
│   ├── metrics.py
│   ├── funnel.py
│   ├── heatmap.py
│   ├── dashboard.py
│   └── ...
│
├── pipeline/
│   ├── process_video.py
│   └── ...
│
├── frontend/
│
├── tests/
│
├── data/
│   ├── resources/
│   └── output/
│
├── README.md
├── DESIGN.md
├── CHOICES.md
├── Dockerfile
└── docker-compose.yml
```

---

# Running the Project Locally

## Clone Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd RetailIQ-AI-Powered-Retail-Store-Intelligence-Platform
```

---

## Backend Setup

Create virtual environment:

```bash
python -m venv venv
```

Activate:

Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start API server:

```bash
uvicorn app.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

Swagger Documentation:

```text
http://localhost:8000/docs
```

---

## Run Detection Pipeline

Execute:

```bash
python pipeline/process_video.py
```

The pipeline processes store video clips and generates:

```text
data/output/events.jsonl
```

This file serves as the event source for all analytics.

---

## Frontend Setup

Navigate to frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start development server:

```bash
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

---

# Docker Deployment

Build and run:

```bash
docker compose up --build
```

Backend API:

```text
http://localhost:8000
```

---

# Running Tests

Execute:

```bash
pytest
```

Tests cover:

* Event ingestion
* Metrics calculations
* Funnel analytics
* API endpoints

---

# Demo

## Dashboard URL

```text
http://localhost:5173
```

## API URL

```text
http://localhost:8000
```

## Demo Video

Replace with uploaded demo video:

```text
[<DEMO_VIDEO_LINK>](https://youtu.be/ZhcQTR1jOAM?si=ikIMFr7r-LBhUEAN)
```

---

# Deliverables Included

* Source Code
* Dockerfile
* docker-compose.yml
* README.md
* DESIGN.md
* CHOICES.md
* Test Suite
* Event Log File (JSONL)
* Dashboard Implementation

---

# Future Improvements

* Deep-learning ReID models
* Multi-camera identity matching
* Kafka-based streaming ingestion
* Database-backed event storage
* Employee badge recognition
* Predictive queue forecasting
* Multi-store analytics aggregation
* Cloud deployment

---

# Author

Chanchal Doijod

Purplle Retail Intelligence Challenge Submission
