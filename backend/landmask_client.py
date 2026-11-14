import json
import os
import urllib.request
from typing import List
from shapely.geometry import shape, LineString, Point
from shapely.strtree import STRtree

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LAND_CACHE_PATH = os.path.join(DATA_DIR, "ne_110m_land.geojson")
NE_LAND_URL = (
    "https://"
    + "raw."
    + "://githubusercontent.com"
)


class LandmassMask:
    """
    Loads Natural Earth 110m coastline polygons into a fast Shapely STRtree
    to prevent maritime A* routes from crossing continents or islands.
    """

    def __init__(self):
        self.land_polys = []
        self.tree = None
        self._load_or_download()

    def _load_or_download(self) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(LAND_CACHE_PATH):
            try:
                req = urllib.request.Request(NE_LAND_URL, headers={"User-Agent": "MaritimeRouteEngine/1.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = resp.read()
                with open(LAND_CACHE_PATH, "wb") as f:
                    f.write(raw)
            except Exception:
                return

        try:
            with open(LAND_CACHE_PATH, "r", encoding="utf-8") as f:
                geojson = json.load(f)
            polys = []
            for feat in geojson.get("features") or []:
                geom = feat.get("geometry")
                if not geom:
                    continue
                # Slight negative buffer (-0.18 deg) keeps coastal harbors and straits navigable
                shrunk = shape(geom).buffer(-0.18)
                if not shrunk.is_empty:
                    polys.append(shrunk)
            self.land_polys = polys
            if self.land_polys:
                self.tree = STRtree(self.land_polys)
        except Exception:
            self.land_polys = []
            self.tree = None

    def crosses_land(self, lat1: float, lon1: float, lat2: float, lon2: float) -> bool:
        """Returns True if the sea segment from (lat1, lon1) to (lat2, lon2) intersects landmass."""
        if not self.tree:
            return False
        seg = LineString([(lon1, lat1), (lon2, lat2)])
        candidate_indices = self.tree.query(seg)
        for idx in candidate_indices:
            if self.land_polys[idx].intersects(seg):
                return True
        return False
