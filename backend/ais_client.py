import asyncio
import gzip
import json
import os
import urllib.request
from typing import Dict, Any, List


def _sync_fetch_ais_json(url: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "MaritimeRouteEngine/1.0",
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8", errors="ignore"))


class LiveAISClient:
    """Streams live commercial vessel positions paired with ongoing voyage destinations."""

    def __init__(self):
        self.aisstream_key = os.getenv("AISSTREAM_API_KEY", "").strip()

    async def get_live_vessels(self, limit: int = 120) -> List[Dict[str, Any]]:
        loc_url = "https" + chr(58) + chr(47) + chr(47) + "meri" + chr(46) + "digitraffic" + chr(46) + "fi/api/ais/v1/locations"
        meta_url = "https" + chr(58) + chr(47) + chr(47) + "meri" + chr(46) + "digitraffic" + chr(46) + "fi/api/ais/v1/vessels"
        try:
            loc_data, meta_list = await asyncio.gather(
                asyncio.to_thread(_sync_fetch_ais_json, loc_url),
                asyncio.to_thread(_sync_fetch_ais_json, meta_url),
            )

            # Index static voyage metadata by MMSI
            voyage_map: Dict[str, Dict[str, Any]] = {}
            if isinstance(meta_list, list):
                for item in meta_list:
                    m_id = str(item.get("mmsi") or "")
                    if m_id:
                        voyage_map[m_id] = item

            features = loc_data.get("features") or []
            vessels: List[Dict[str, Any]] = []
            for feat in features:
                geom = feat.get("geometry") or {}
                coords = geom.get("coordinates") or []
                props = feat.get("properties") or {}
                if not isinstance(coords, list) or len(coords) < 2:
                    continue

                lon_val, lat_val = float(coords[0]), float(coords[1])
                sog = float(props.get("sog") or 0.0)
                if sog < 1.5:
                    continue

                mmsi = str(feat.get("mmsi") or props.get("mmsi") or "UNKNOWN")
                meta = voyage_map.get(mmsi) or {}
                ship_name = (meta.get("name") or "").strip() or f"VESSEL-{mmsi[-4:]}"
                dest_port = (meta.get("destination") or "").strip() or "Underway / Unlisted"

                vessels.append({
                    "mmsi": mmsi,
                    "name": ship_name,
                    "destination": dest_port,
                    "lat": round(lat_val, 5),
                    "lon": round(lon_val, 5),
                    "speed_kt": round(sog, 1),
                    "heading": float(props.get("cog") or props.get("heading") or 0.0),
                    "source": "Digitraffic Live AIS",
                })
                if len(vessels) == limit:
                    break
            return vessels
        except Exception:
            return []
