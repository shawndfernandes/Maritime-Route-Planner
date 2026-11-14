from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from marine_weather import MarineWeatherClient
from maritime_router import MAJOR_PORTS, compute_safe_sea_route
from ais_client import LiveAISClient

app = FastAPI(title="Maritime Sea-Lane, Live AIS, SeaWeather & Weather.com Engine")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
marine_wx = MarineWeatherClient()
ais_client = LiveAISClient()


@app.get("/api/maritime/snapshot")
async def maritime_snapshot(lat: float = Query(40.5), lon: float = Query(-70.0)):
    storms, sea_state, vessels, radar_cfg = await asyncio.gather(
        marine_wx.get_marine_storms(),
        marine_wx.get_sea_state(lat, lon),
        ais_client.get_live_vessels(limit=150),
        marine_wx.get_weather_com_radar(),
    )
    first_vessel = next(iter(vessels), None)
    active_source = first_vessel["source"] if first_vessel else "none"
    return {
        "ais_source": active_source,
        "vessels": vessels,
        "ports": MAJOR_PORTS,
        "storms_geojson": storms,
        "sea_state": sea_state,
        "radar_config": radar_cfg,
    }


@app.get("/api/maritime/route")
async def plan_sea_voyage(
    origin: str = Query("USNYC"),
    destination: str = Query("NLRTM"),
    speed_kt: float = Query(18.0, ge=5.0, le=35.0),
):
    o_key, d_key = origin.strip().upper(), destination.strip().upper()
    if o_key not in MAJOR_PORTS or d_key not in MAJOR_PORTS:
        raise HTTPException(status_code=404, detail=f"Use port codes: {', '.join(MAJOR_PORTS.keys())}")

    o_lat, o_lon, o_name = MAJOR_PORTS[o_key]
    d_lat, d_lon, d_name = MAJOR_PORTS[d_key]
    storms = await marine_wx.get_marine_storms()
    route = compute_safe_sea_route((o_lat, o_lon), (d_lat, d_lon), storms, cruise_knots=speed_kt)

    wps = route["safe_waypoints"]
    step = max(1, len(wps) // 10)
    sampled = wps[::step][:10]
    wave_samples = await asyncio.gather(*[marine_wx.get_sea_state(w["lat"], w["lon"]) for w in sampled])

    return {
        "origin": {"code": o_key, "name": o_name, "lat": o_lat, "lon": o_lon},
        "destination": {"code": d_key, "name": d_name, "lat": d_lat, "lon": d_lon},
        **route,
        "wave_profile": [{"lat": w["lat"], "lon": w["lon"], **s} for w, s in zip(sampled, wave_samples)],
    }
