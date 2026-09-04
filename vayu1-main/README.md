# 🌀 Cyclone SIH2026 — Technical & Frontend Integration Documentation

> **System Status**: Phase 1 & Phase 2 Core ML, Backend, Geospatial APIs, and Reference UI Complete  
> **Test Suite**: 21 / 21 Tests Passing (`pytest`)  
> **Target Region**: North Indian Ocean (Bay of Bengal `BOB` & Arabian Sea `AS`)  
> **Architecture**: Django 5 + GeoDjango (PostGIS/SpatiaLite) • PyTorch 2.x • Celery + Redis • DRF-GIS • Leaflet.js

---

## 📌 1. Project Overview & Current Stage of Development

Cyclone SIH2026 is an AI-driven, end-to-end cyclone monitoring, tracking, intensity estimation, rainfall forecasting, and disaster response decision-support system tailored specifically for the Indian subcontinent.

### Current Development Milestones Achieved:
1. **Machine Learning Core**:
   - **Vortex Detection & Eye Confidence**: Multi-head CNN extracting bounding box coordinates and continuous sigmoid confidence scores (calibrated to IMD eye structure stages).
   - **Environmental Physics Fusion**: Multi-modal fusion integrating satellite thermal IR (TIR-1) imagery with 5 atmospheric/oceanic variables (Shear, SST, Relative Humidity, Vorticity, and Mean Sea Level Pressure).
   - **Multi-Horizon Trajectory Forecasting**: Deep spatio-temporal tracker projecting coordinates across operational IMD horizons: **T+6h, T+12h, T+24h, and T+72h**, incorporating intensity decay.
   - **Parametric Rainfall Engine (Tier 1)**: Physics-based R-CLIPER model generating high-resolution precipitation accumulation grids (mm) and IMD 4-tier risk categories per forecast horizon.
   - **ML Rainfall Engine Skeleton (Tier 2)**: FiLM-conditioned spatial U-Net ready for NASA GPM IMERG training.
2. **Backend & Geospatial Infrastructure**:
   - GeoDjango models with spatial indexing for storm tracks, observations, and shelters.
   - High-performance spatial k-NN indexing for cyclone shelter routing.
   - Pincode / District danger zone resolver with dynamic storm-radius calculations.
   - Consolidated asynchronous Celery beat scheduler polling BOB & AS streams every 15 minutes.
3. **Frontend Integration Readiness**:
   - Clean, standardized REST & GeoJSON API endpoints.
   - Complete reference implementation dashboard (`/api/predictions/map/`) utilizing Leaflet.js, Leaflet.heat, dynamic uncertainty cones, and glassmorphism telemetry panels.

### 1.1. Recent Codebase Refactor & Updates (Sept 2026)
*   **Architecture Simplification**: Unified prediction heads in `IntensityClassifier` and successfully integrated the `Postprocessor` directly into `CyclonePipeline`.
*   **Bug Fixes**: Resolved dimension mismatch in `RainfallUNet`, corrected cone polygon geometries in `map.html`, and patched input validation in spatial views.
*   **Boilerplate Cleanup**: Removed legacy `SIH2026/` scaffolding directory and unused models/serializers (`RainfallForecast`, `PincodeLocationSerializer`). Created a proper root `manage.py` pointing to `config.settings`.
*   **Documentation & Frontend**: Generated the [Frontend PRD](frontend_prd.md) and an [Implementation Plan](implementation_plan.md) for a new ML Training Dashboard.

---

## ⚠️ 2. Inactive / Dead Code & Legacy Data Notice

> [!WARNING]
> **To Backend, ML, and Frontend Teams:**  
> The codebase contains certain legacy files, unhooked modules, and satellite ingestion clients from earlier exploratory stages that are **NOT active in the live operational pipeline**. Do not attempt to wire these into frontend views or live inference workflows without reviewing the table below.

| Component / File | Original Purpose | Current Status in Operational Pipeline | Action / Handoff Guideline |
|---|---|---|---|
| [`ml_engine/utils/himawari_client.py`](file:///c:/Users/yashy/Downloads/Cyclone%20SIH2026/ml_engine/utils/himawari_client.py) | Ingestion client for JMA Himawari satellite imagery (covering South Pacific & East Asia). | **DEAD / INACTIVE in Live Pipeline**. Live pipeline strictly monitors North Indian Ocean (BOB & AS) via INSAT-3D/3DS (`MOSDACClient`). Requesting `basin=SP` explicitly raises `ValueError`. | Retained only as a reference utility for potential offline global dataset building. Do not call in live frontend/backend flows. |
| **South Pacific Categories** (`south_pacific_category` in [`models.py`](file:///c:/Users/yashy/Downloads/Cyclone%20SIH2026/apps/predictions/models.py) & [`wind_standards.py`](file:///c:/Users/yashy/Downloads/Cyclone%20SIH2026/ml_engine/training/wind_standards.py)) | Australian/Fiji WMO Category 1–5 classification. | **LEGACY / SECONDARY**. Included in API response payloads for schema backward compatibility, but irrelevant for India disaster management. | **Frontend Team:** Always use `imd_category` and `msw_3min` for UI badges, warnings, and alerts in Indian territory. |
| **`SIH2026/` Directory** (Removed) | Default Django scaffolding created by `django-admin startproject`. | **REMOVED**. The actual project settings and routing live in `config/`. | Always use the `manage.py` located at the root of the project. |
| [`ml_engine/architectures/rainfall_unet.py`](file:///c:/Users/yashy/Downloads/Cyclone%20SIH2026/ml_engine/architectures/rainfall_unet.py) | Deep U-Net with FiLM conditioning for spatial rainfall prediction. | **TIER 2 SKELETON (UNINITIALIZED)**. Inactive during live inference. Live system currently runs the physics-based Tier-1 R-CLIPER parametric model in `rainfall_estimator.py`. | **ML Team:** Do not load weights in production until trained on NASA GPM IMERG collocated dataset. |
| **Basin Choices `SP` & `SI`** in [`apps/cyclones/models.py`](file:///c:/Users/yashy/Downloads/Cyclone%20SIH2026/apps/cyclones/models.py) | Legacy database model choices for South Pacific and South Indian Ocean. | **DORMANT**. Live Celery Beat scheduler and `SatelliteStreamRouter` only accept and trigger `BOB` and `AS`. | Retained only to avoid schema conflicts with historical records. |

---

## 🏗️ 3. System Architecture & Component Layout

```
Cyclone SIH2026/
├── apps/
│   ├── cyclones/                 # Core Cyclone & Infrastructure Domain
│   │   ├── models.py             # StormEvent, SatelliteObservation, CycloneShelter (GeoDjango)
│   │   ├── serializers.py        # GeoFeatureModelSerializers for Observations & Shelters
│   │   ├── views.py              # StormEvent, Observation & Shelter ViewSets (k-NN + Availability)
│   │   ├── urls.py               # /api/cyclones/ router
│   │   └── management/commands/  # load_shelters.py (bulk CSV loader)
│   │
│   └── predictions/              # ML Inference & Decision Support APIs
│       ├── models.py             # ForecastTrack, RainfallForecast, PincodeLocation
│       ├── serializers.py        # ForecastTrackSerializer, RainfallForecastSerializer
│       ├── views.py              # Live Inference, AffectedAreaView, RainfallView, CycloneMapView
│       ├── urls.py               # /api/predictions/ router + map/ + affected-area/ + rainfall/
│       ├── tasks.py              # Celery tasks: run_live_pipeline
│       ├── templates/            # Leaflet Reference Dashboard (map.html)
│       └── management/commands/  # load_pincodes.py (bulk CSV loader)
│
├── ml_engine/                    # Machine Learning Engine & Pipelines
│   ├── architectures/            # PyTorch Deep Neural Networks
│   │   ├── detector.py           # SimpleVortexDetector (box_head + conf_head)
│   │   ├── classifier.py         # IntensityClassifier (Visual + 5-dim Env Fusion)
│   │   ├── tracker.py            # MultimodalTrackPredictor (T+6h/12h/24h/72h)
│   │   └── rainfall_unet.py      # RainfallUNet (FiLM-conditioned Tier-2 ML architecture)
│   ├── pipelines/                # Inference Orchestration
│   │   ├── predictor.py          # CyclonePipeline (Singleton orchestrator)
│   │   ├── preprocessor.py       # TIR-1 normalization & Coriolis flip
│   │   ├── postprocessor.py      # Clamping, alert categorization & payload trimming
│   │   └── rainfall_estimator.py # Tier-1 Parametric R-CLIPER rainfall engine
│   ├── training/                 # Data Ingestion & Model Training
│   │   ├── global_dataset.py     # PyTorch Dataset for IBTrACS + Env physics
│   │   ├── trainer.py            # Two-stage Trainer (Global pretrain -> Regional finetune)
│   │   ├── ibtracs_loader.py     # NOAA IBTrACS CSV parser
│   │   └── wind_standards.py     # 1-min (JTWC) ↔ 3-min (IMD) ↔ 10-min (WMO) conversions
│   └── utils/                    # Data Ingestion & Satellite Streaming
│       ├── stream_router.py      # Enforces BOB/AS basins, routes imagery & CDS physics
│       ├── mosdac_client.py      # ISRO MOSDAC INSAT-3D/3DS TIR-1 client
│       ├── cds_client.py         # Copernicus Climate Data Store ERA5/physics client
│       └── himawari_client.py    # JMA Himawari client (offline training)
│
├── config/                       # Project Configuration
│   ├── settings.py               # Django & GeoDjango configuration (PostGIS / SpatiaLite)
│   ├── celery.py                 # Celery Beat schedules (15-min BOB & AS cycles)
│   └── urls.py                   # Root URL routing
├── data/                         # Datasets & Seed Data
│   ├── cyclone_shelters.csv      # Multipurpose Cyclone Shelter coordinates (AP, OD, WB, TN, GJ)
│   └── shelter_data_availability.json # State-wise data transparency registry
└── tests/
    └── test_inference.py         # 21 comprehensive test suites
```

---

## 🔌 4. Frontend Integration & API Contracts

All endpoints are hosted under `/api/` and return standard JSON or GeoJSON (RFC 7946).

### 3.1. Live Storm Inference Telemetry
* **Endpoint**: `GET /api/predictions/tracks/live/`
* **Query Parameters**: `basin=BOB` (default) or `basin=AS`
* **Response Status**: `200 OK`

```json
{
  "basin": "BOB",
  "satellite_source": "INSAT-3D/3DS Imager",
  "is_southern_hemisphere": false,
  "center_lat": 15.1245,
  "center_lon": 86.8421,
  "msw": 78.45,
  "msw_3min": 78.45,
  "msw_10min": 74.22,
  "msw_1min": 84.35,
  "category": "Very Severe Cyclonic Storm",
  "imd_category": "Very Severe Cyclonic Storm",
  "south_pacific_category": "Category 3 Severe Tropical Cyclone",
  "central_pressure_hpa": 974.2,
  "eye_confidence": 0.884,
  "eye_confidence_label": "Well-Defined Eye",
  "forecast_timeline": [
    {
      "forecast_hour": 6,
      "lat": 15.4211,
      "lon": 86.5123,
      "msw_kt": 77.41,
      "imd_category": "Very Severe Cyclonic Storm",
      "max_rainfall_mm": 112.5,
      "rainfall_grid": [
        {
          "lat": 15.0,
          "lon": 86.0,
          "distance_km": 42.1,
          "rainfall_mm": 98.4,
          "risk_level": "HIGH"
        }
      ]
    },
    { "forecast_hour": 12, "lat": 15.8214, "lon": 86.1042, "msw_kt": 74.52, "imd_category": "Very Severe Cyclonic Storm", "max_rainfall_mm": 185.2, "rainfall_grid": [...] },
    { "forecast_hour": 24, "lat": 16.5102, "lon": 85.3401, "msw_kt": 68.21, "imd_category": "Severe Cyclonic Storm", "max_rainfall_mm": 310.4, "rainfall_grid": [...] },
    { "forecast_hour": 72, "lat": 18.4201, "lon": 83.9214, "msw_kt": 52.14, "imd_category": "Cyclonic Storm", "max_rainfall_mm": 480.0, "rainfall_grid": [...] }
  ]
}
```

---

### 3.2. Pincode / District Hazard Checker
Determines whether a citizen or district is in the direct impact zone, calculates distance from the storm eye, evaluates expected rainfall, provides an advisory, and resolves the nearest cyclone shelter.

* **Endpoint**: `GET /api/predictions/affected-area/`
* **Query Parameters**:
  - `?pincode=530001` (Recommended) OR
  - `?district=Visakhapatnam` OR
  - `?lat=17.6868&lon=83.2185`

```json
{
  "query": {
    "pincode": "530001",
    "district": "Visakhapatnam",
    "state": "Andhra Pradesh"
  },
  "location": {
    "lat": 17.6868,
    "lon": 83.2185
  },
  "is_affected": true,
  "distance_km": 142.3,
  "affected_radius_km": 350.0,
  "risk_level": "HIGH",
  "expected_rainfall_mm": 98.4,
  "imd_category": "Very Severe Cyclonic Storm",
  "msw_knots": 78.45,
  "central_pressure_hpa": 974.2,
  "eye_confidence": 0.884,
  "eye_confidence_label": "Well-Defined Eye",
  "nearest_shelter": {
    "name": "MPCS Visakhapatnam-1",
    "state": "Andhra Pradesh",
    "district": "Visakhapatnam",
    "lat": 17.7231,
    "lon": 83.3012,
    "capacity": 1500,
    "distance_km": 9.24
  },
  "shelter_data_note": null,
  "advisory": "You are in a HIGH risk zone. Be prepared to evacuate."
}
```

*Note on Data Transparency*: If the user queries a state where government shelter coordinates are not publicly released (e.g., Maharashtra or Goa), `nearest_shelter` is `null` and `shelter_data_note` contains an advisory string.

---

### 3.3. District-Level Multi-Horizon Rainfall
* **Endpoint**: `GET /api/predictions/rainfall/?district=Visakhapatnam`
* **Optional**: `&horizon=24` (Filters for a specific hour: 6, 12, 24, 72)

```json
{
  "district": "Visakhapatnam",
  "state": "Andhra Pradesh",
  "district_lat": 17.6868,
  "district_lon": 83.2185,
  "forecasts": [
    {
      "forecast_hour": 6,
      "max_mm": 45.2,
      "mean_mm": 32.1,
      "risk_level": "MODERATE",
      "storm_lat": 15.4211,
      "storm_lon": 86.5123,
      "storm_msw_kt": 77.41,
      "storm_category": "Very Severe Cyclonic Storm"
    },
    { "forecast_hour": 12, "max_mm": 88.4, "mean_mm": 64.2, "risk_level": "HIGH", ... },
    { "forecast_hour": 24, "max_mm": 195.0, "mean_mm": 142.3, "risk_level": "SEVERE", ... },
    { "forecast_hour": 72, "max_mm": 340.2, "mean_mm": 210.8, "risk_level": "SEVERE", ... }
  ]
}
```

---

### 3.4. Cyclone Shelters & Geospatial Routing
* **List Shelters (GeoJSON)**: `GET /api/cyclones/shelters/`
  - Optional Filters: `?state=Odisha` or `?district=Puri`
* **Nearest k-NN Shelters**: `GET /api/cyclones/shelters/nearest/?lat=17.72&lon=83.30&limit=5`

```json
[
  {
    "id": 1,
    "name": "MPCS Visakhapatnam-1",
    "state": "Andhra Pradesh",
    "district": "Visakhapatnam",
    "lat": 17.7231,
    "lon": 83.3012,
    "capacity": 1500,
    "shelter_type": "MPCS",
    "distance_km": 0.38
  },
  {
    "id": 2,
    "name": "MPCS Visakhapatnam-2",
    "state": "Andhra Pradesh",
    "district": "Visakhapatnam",
    "lat": 17.6975,
    "lon": 83.2241,
    "capacity": 1200,
    "shelter_type": "MPCS",
    "distance_km": 8.61
  }
]
```

* **State Data Availability Audit**: `GET /api/cyclones/shelters/availability/`

```json
{
  "states_with_data": [
    "Andhra Pradesh",
    "Odisha",
    "West Bengal",
    "Tamil Nadu",
    "Gujarat"
  ],
  "states_without_data": [
    {
      "state": "Kerala",
      "message": "KSDMA publishes shelter names and addresses but no coordinates. RTI application recommended for geo-coordinates."
    },
    {
      "state": "Maharashtra",
      "message": "MSDMA does not publish cyclone shelter locations publicly. Contact MSDMA at msdma@maharashtra.gov.in."
    },
    {
      "state": "Goa",
      "message": "No SDMA geospatial portal exists for Goa. Contact the Goa State Disaster Management Authority."
    }
  ],
  "total_shelters_loaded": 37
}
```

---

## 🔬 5. Machine Learning & Forecasting Mechanics

### 5.1. Intensity & Category Standards
Wind speeds in the system are normalized and cross-converted across international meteorological standards:
- **IMD Standard (India)**: 3-minute average sustained wind speed ($V_{3\text{min}} = V_{1\text{min}} \times 0.93$).
- **WMO Standard**: 10-minute average ($V_{10\text{min}} = V_{1\text{min}} \times 0.88$).
- **JTWC Standard (USA)**: 1-minute average ($V_{1\text{min}}$).

```
IMD Classification Tiers:
  < 28 kt        : Depression
  28 – 33 kt     : Deep Depression
  34 – 47 kt     : Cyclonic Storm
  48 – 63 kt     : Severe Cyclonic Storm
  64 – 89 kt     : Very Severe Cyclonic Storm
  90 – 119 kt    : Extremely Severe Cyclonic Storm
  ≥ 120 kt       : Super Cyclonic Storm
```

### 5.2. Multi-Modal Environmental Physics Vector
Inference fuses visual features with 5 environmental parameters retrieved from the CDS ERA5 reanalysis client:
$$\text{Vector} = [ \text{Vertical Wind Shear (kt)},\, \text{SST (K)},\, \text{Relative Humidity (\text{\%})},\, \text{Vorticity } (\text{s}^{-1}),\, \text{MSLP (hPa)} ]$$

### 5.3. Eye Confidence Metric
The detector’s confidence head outputs a value $c \in [0.0, 1.0]$ representing convective eye definition:
- $c < 0.35$: *No Organised Circulation*
- $0.35 \le c < 0.60$: *Partial Circulation / Weak Eye*
- $0.60 \le c < 0.80$: *Developing Eye*
- $c \ge 0.80$: *Well-Defined Eye*

This confidence score dynamically modulates the **Uncertainty Cone Radius** on the map:
$$R_{\text{cone}}(c, t) = \left(50 + (1 - c) \times 150\right) + \left(\frac{t}{12} \times 30\right) \text{ km}$$

---

## 🛠️ 6. Technical Quickstart & Developer Workflow

### 6.1. Environment Setup

```bash
# 1. Activate Virtual Environment
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # Linux/macOS

# 2. Install Requirements
pip install -r requirements/base.txt
pip install pytest
```

### 6.2. Database & Seed Data Ingestion

The backend uses GeoDjango. It supports **SpatiaLite** (local default) and **PostGIS** (production PostgreSQL).

```bash
# 1. Run Migrations
python manage.py makemigrations cyclones predictions
python manage.py migrate

# 2. Ingest Cyclone Shelter Dataset (AP, Odisha, WB, TN, Gujarat)
python manage.py load_shelters data/cyclone_shelters.csv

# 3. Ingest All-India Pincode Centroids (Download CSV from data.gov.in)
python manage.py load_pincodes data/pincodes.csv
```

### 6.3. Running the Dev Server & Celery Workers

```bash
# Terminal 1: Run Django REST API & Reference UI
python manage.py runserver 127.0.0.1:8000

# Terminal 2: Run Celery Worker for Live Stream Ingestion
celery -A config worker --loglevel=info -P solo

# Terminal 3: Run Celery Beat Scheduler (Every 15 mins for BOB & AS)
celery -A config beat --loglevel=info
```

### 6.4. Running the Test Suite

```bash
# Run all 21 automated unit and regression tests
pytest tests/test_inference.py -v
```

---

## 🗺️ 7. Frontend Team Reference Guide

1. **Dashboard URL**: `http://localhost:8000/api/predictions/map/` serves a standalone reference web application implementing Leaflet.js, CartoDB Dark Matter / ESRI Satellite basemaps, pulsating cyclone eyes, cone polygons, and `Leaflet.heat` precipitation layers.
2. **Polling Frequency**: The backend ingests satellite frames every 15 minutes. Recommended frontend polling interval: **every 5 to 15 minutes**.
3. **Color Palette Standard for Weather Alerts**:
   - `YELLOW` (`#fbbf24`): Depression & Deep Depression
   - `ORANGE` (`#fb923c`): Cyclonic Storm & Severe Cyclonic Storm
   - `RED` (`#ef4444`): Very Severe Cyclonic Storm & above
   - `SUCCESS` (`#10b981`): Shelters & Outside Threat Area

---

## 🚀 8. Next Sprints & Roadmap (Handoff Notes)

| Item | Priority | Description | Owner |
|---|---|---|---|
| **Model Weights Training** | High | Run `ml_engine/training/trainer.py` on GPU cluster against complete 2001–2024 IBTrACS + GPM IMERG dataset to replace initialized weights. | ML Team |
| **Custom Frontend App** | High | Build dedicated React/Next.js/Vite frontend consuming the DRF API endpoints detailed in Section 3. | Frontend Team |
| **Live MOSDAC Ingestion** | Medium | Connect active ISRO MOSDAC FTP/API credentials in `ml_engine/utils/mosdac_client.py` for automated live TIR-1 frame pulls. | Backend/Data Team |
| **SDMA Shelter Expansion** | Medium | File RTI / request SDMA datasets for missing coastal states (Maharashtra, Kerala, Karnataka, Goa) to populate remaining state registries. | Ops/Data Team |
| **Tier 2 Rainfall U-Net** | Low | Complete training loop for `RainfallUNet` using NASA GPM IMERG 30-minute accumulated grids. | ML Team |
