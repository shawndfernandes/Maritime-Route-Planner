# Maritime Sea-Lane, Live AIS & SeaWeather Pathfinder

Real-time 3D maritime voyage routing, Eurostat Marnet ocean shipping lanes, live AIS vessel telemetry, OpenSeaMap nautical seamarks, Weather.com marine radar, and wave/swell avoidance built with **FastAPI**, **Shapely**, **Searoute**, and **CesiumJS**.

## Key Features
* **Ocean-Only Sea-Lane Routing:** Uses `searoute` (Eurostat Marnet network) and Natural Earth coastline masking to route between global ports without crossing land, with automatic offshore storm detours.
* **Live AIS Vessel Telemetry:** Streams real-time moving ships with vessel names, MMSI numbers, speeds (`kt`), courses, and ongoing destination ports.
* **SeaWeather & Radar Overlays:** Combines OpenSeaMap nautical charts, Weather.com animated marine radar, marine storm warning polygons, and 2D significant wave height (`m`) profiles.

## Quick Setup
```bash
chmod +x setup.sh restart.sh
./setup.sh
./restart.sh
```
Open **`http://localhost:3002/`** in your browser.

## Project Structure
* `setup.sh` / `setup_cesium.sh` / `restart.sh`: Automated environment setup and service launcher scripts.
* `backend/`: FastAPI server (`main.py`), `searoute` + Shapely ocean router (`maritime_router.py`), coastline mask (`landmask_client.py`), live AIS client (`ais_client.py`), and marine weather client (`marine_weather.py`).
* `frontend/`: CesiumJS globe & radar controller (`maritime_map.js`), HUD (`index.html`), 3D vessel/voyage renderers (`maritime_renderer.js`), and wave profile chart (`maritime_chart.js`).
