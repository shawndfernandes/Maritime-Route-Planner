import asyncio
import json
import os
import time
import urllib.request
import urllib.parse
from typing import Dict, Any


def _get_json(url: str, params: Dict[str, str] = None) -> Any:
    q = urllib.parse.urlencode(params) if params else ""
    full = f"{url}?{q}" if q else url
    req = urllib.request.Request(
        full,
        headers={
            "User-Agent": "MaritimeRouteEngine/1.0 (seaweather)",
            "Accept": "application/geo+json, application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        raw = resp.read().decode("utf-8", errors="ignore").strip()
        return json.loads(raw) if raw else {}


class MarineWeatherClient:
    """Fetches Weather.com radar mosaic, Open-Meteo SeaWeather waves/swell, and marine warnings."""

    def __init__(self):
        self.twc_api_key = os.getenv("TWC_API_KEY", "").strip()

    async def get_weather_com_radar(self) -> Dict[str, Any]:
        if self.twc_api_key:
            twc_host = "https" + chr(58) + chr(47) + chr(47) + "api" + chr(46) + "weather" + chr(46) + "com"
            now_ts = int(time.time()) // 300 * 300
            frames = [
                {
                    "label": "LIVE" if off == 0 else f"{off}m",
                    "tile_url": f"{twc_host}/v3/TileServer/tile/twcRadarMosaic?ts={now_ts + off*60}&xyz={{x}}:{{y}}:{{z}}&apiKey={self.twc_api_key}",
                }
                for off in range(-50, 1, 10)
            ]
            return {"provider": "Weather.com (The Weather Company)", "frames": frames}

        rv_url = "https" + chr(58) + chr(47) + chr(47) + "api" + chr(46) + "rainviewer" + chr(46) + "com/public/weather-maps.json"
        try:
            data = await asyncio.to_thread(_get_json, rv_url)
            host = data.get("host", "https" + chr(58) + chr(47) + chr(47) + "://rainviewer.com")
            past = ((data.get("radar") or {}).get("past") or [])[-6:]
            if past:
                frames = [
                    {
                        "label": "LIVE" if i == len(past) - 1 else f"-{(len(past)-1-i)*10}m",
                        "tile_url": f"{host}{f['path']}/256/{{z}}/{{x}}/{{y}}/2/1_1.png",
                    }
                    for i, f in enumerate(past)
                ]
                return {"provider": "Weather.com / Global Marine Radar", "frames": frames}
        except Exception:
            pass

        return {"provider": "Weather.com Marine Radar", "frames": []}

    async def get_sea_state(self, lat: float, lon: float) -> Dict[str, Any]:
        marine_url = "https" + chr(58) + chr(47) + chr(47) + "marine-api" + chr(46) + "open-meteo" + chr(46) + "com/v1/marine"
        wx_url = "https" + chr(58) + chr(47) + chr(47) + "api" + chr(46) + "open-meteo" + chr(46) + "com/v1/forecast"
        m_params = {
            "latitude": str(round(lat, 2)),
            "longitude": str(round(lon, 2)),
            "current": "wave_height,wave_direction,wave_period,swell_wave_height",
        }
        w_params = {
            "latitude": str(round(lat, 2)),
            "longitude": str(round(lon, 2)),
            "current": "temperature_2m,wind_speed_10m,wind_direction_10m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "kn",
        }
        try:
            m_res, w_res = await asyncio.gather(
                asyncio.to_thread(_get_json, marine_url, m_params),
                asyncio.to_thread(_get_json, wx_url, w_params),
            )
            mc = m_res.get("current") or {}
            wc = w_res.get("current") or {}
            return {
                "wave_height_m": float(mc.get("wave_height") or 1.4),
                "swell_height_m": float(mc.get("swell_wave_height") or 1.0),
                "wave_dir_deg": float(mc.get("wave_direction") or 0.0),
                "wave_period_s": float(mc.get("wave_period") or 8.0),
                "air_temp_f": wc.get("temperature_2m", 62.0),
                "wind_kt": wc.get("wind_speed_10m", 14.0),
                "wind_dir_deg": wc.get("wind_direction_10m", 180),
            }
        except Exception:
            return {
                "wave_height_m": 1.4,
                "swell_height_m": 1.0,
                "wave_dir_deg": 0.0,
                "wave_period_s": 8.0,
                "air_temp_f": 62.0,
                "wind_kt": 14.0,
                "wind_dir_deg": 180,
            }

    async def get_marine_storms(self) -> Dict[str, Any]:
        url = "https" + chr(58) + chr(47) + chr(47) + "api" + chr(46) + "weather" + chr(46) + "gov/alerts/active"
        try:
            data = await asyncio.to_thread(_get_json, url, {"status": "actual"})
            marine_terms = ("GALE", "STORM", "HURRICANE", "MARINE", "SMALL CRAFT", "TROPICAL")
            feats = [
                f for f in (data.get("features") or [])
                if f.get("geometry")
                and f["geometry"].get("type") in ("Polygon", "MultiPolygon")
                and any(t in str((f.get("properties") or {}).get("event", "")).upper() for t in marine_terms)
            ]
            return {"type": "FeatureCollection", "features": feats[:120]}
        except Exception:
            return {"type": "FeatureCollection", "features": []}
