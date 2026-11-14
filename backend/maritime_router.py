import math
from typing import Dict, Any, List, Tuple
import searoute as sr
from shapely.geometry import shape, LineString
from landmask_client import LandmassMask

EARTH_RADIUS_NM = 3440.065
LAND_MASK = LandmassMask()

MAJOR_PORTS: Dict[str, Tuple[float, float, str]] = {
    "USNYC": (40.5000, -73.8500, "Port of New York & New Jersey (USNYC)"),
    "USMIA": (25.7600, -80.0500, "PortMiami (USMIA)"),
    "USLAX": (33.6800, -118.2800, "Port of Los Angeles (USLAX)"),
    "USHOU": (29.3000, -94.7000, "Port of Houston / Galveston (USHOU)"),
    "NLRTM": (52.0200, 3.9500, "Port of Rotterdam (NLRTM)"),
    "GBSOU": (50.6500, -1.3000, "Port of Southampton (GBSOU)"),
    "SGSIN": (1.2000, 103.8500, "Port of Singapore (SGSIN)"),
    "JPTYO": (35.4500, 139.8500, "Port of Tokyo (JPTYO)"),
    "PABLB": (8.8500, -79.5500, "Port of Balboa / Panama Canal (PABLB)"),
    "AEDXB": (25.0100, 55.0600, "Port of Jebel Ali / Dubai (AEDXB)"),
    "BRSSZ": (-23.9800, -46.2900, "Port of Santos (BRSSZ)"),
    "AUSYD": (-33.8500, 151.2200, "Port of Sydney (AUSYD)"),
}


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    a = (
        math.sin((rlat2 - rlat1) / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin((rlon2 - rlon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_NM * math.asin(min(1.0, math.sqrt(a)))


def compute_safe_sea_route(
    orig: Tuple[float, float],
    dest: Tuple[float, float],
    storms_geojson: Dict[str, Any],
    cruise_knots: float = 18.0,
    port_pair: Tuple[str, str] = ("", ""),
) -> Dict[str, Any]:
    o_lat, o_lon = orig
    d_lat, d_lon = dest

    # 1. Compute verified Marnet shipping-lane route via searoute (expects [lon, lat])
    route_feature = sr.searoute([o_lon, o_lat], [d_lon, d_lat], units="naut")
    raw_coords = (route_feature.get("geometry") or {}).get("coordinates") or [[o_lon, o_lat], [d_lon, d_lat]]

    marnet_wps = [{"lat": round(float(lat), 4), "lon": round(float(lon), 4)} for lon, lat in raw_coords]
    marnet_nm = float((route_feature.get("properties") or {}).get("length") or 0.0)
    if marnet_nm <= 0.0:
        marnet_nm = sum(
            haversine_nm(marnet_wps[i]["lat"], marnet_wps[i]["lon"], marnet_wps[i + 1]["lat"], marnet_wps[i + 1]["lon"])
            for i in range(len(marnet_wps) - 1)
        )

    # 2. Apply offshore storm detour offsets if a segment intersects an active marine storm polygon
    storm_polys = [
        shape(f["geometry"]).buffer(0.4)
        for f in (storms_geojson.get("features") or [])
        if f.get("geometry")
    ]

    first_wp = next(iter(marnet_wps))
    last_wp = marnet_wps[-1]
    safe_wps: List[Dict[str, Any]] = [first_wp]

    for i in range(1, len(marnet_wps) - 1):
        prev_pt = safe_wps[-1]
        curr_pt = marnet_wps[i]
        seg = LineString([(prev_pt["lon"], prev_pt["lat"]), (curr_pt["lon"], curr_pt["lat"])])

        if storm_polys and any(poly.intersects(seg) for poly in storm_polys):
            dlat = curr_pt["lat"] - prev_pt["lat"]
            dlon = curr_pt["lon"] - prev_pt["lon"]
            norm = max(0.01, math.hypot(dlat, dlon))
            perp_lat, perp_lon = -dlon / norm, dlat / norm

            shifted_pt = curr_pt
            for shift in (1.5, -1.5, 2.5, -2.5):
                cand_lat = round(curr_pt["lat"] + perp_lat * shift, 4)
                cand_lon = round(curr_pt["lon"] + perp_lon * shift, 4)
                if not LAND_MASK.is_on_land(cand_lat, cand_lon) and not LAND_MASK.crosses_land(
                    prev_pt["lat"], prev_pt["lon"], cand_lat, cand_lon
                ):
                    cand_seg = LineString([(prev_pt["lon"], prev_pt["lat"]), (cand_lon, cand_lat)])
                    if not any(poly.intersects(cand_seg) for poly in storm_polys):
                        shifted_pt = {"lat": cand_lat, "lon": cand_lon}
                        break
            safe_wps.append(shifted_pt)
        else:
            safe_wps.append(curr_pt)

    safe_wps.append(last_wp)

    safe_nm = sum(
        haversine_nm(safe_wps[i]["lat"], safe_wps[i]["lon"], safe_wps[i + 1]["lat"], safe_wps[i + 1]["lon"])
        for i in range(len(safe_wps) - 1)
    )

    return {
        "direct_waypoints": marnet_wps,
        "safe_waypoints": safe_wps,
        "direct_nm": round(marnet_nm, 1),
        "safe_nm": round(safe_nm, 1),
        "eta_hours": round(safe_nm / max(5.0, cruise_knots), 1),
        "landmask_active": True,
    }
