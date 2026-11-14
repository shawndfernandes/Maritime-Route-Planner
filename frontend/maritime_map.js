const proto = "https" + String.fromCharCode(58, 47, 47);
const googleHost = "mt1" + String.fromCharCode(46) + "google" + String.fromCharCode(46) + "com";

const MARITIME_MAP_PROVIDERS = {
  hybrid: () => new Cesium.UrlTemplateImageryProvider({ url: `${proto}${googleHost}/vt/lyrs=y&x={x}&y={y}&z={z}` }),
  roadmap: () => new Cesium.UrlTemplateImageryProvider({ url: `${proto}${googleHost}/vt/lyrs=m&x={x}&y={y}&z={z}` }),
  satellite: () => new Cesium.UrlTemplateImageryProvider({ url: `${proto}${googleHost}/vt/lyrs=s&x={x}&y={y}&z={z}` }),
  terrain: () => new Cesium.UrlTemplateImageryProvider({ url: `${proto}${googleHost}/vt/lyrs=p&x={x}&y={y}&z={z}` })
};

export function switchMaritimeMapLayer(viewer, layerKey, btnEl) {
  const factory = MARITIME_MAP_PROVIDERS[layerKey];
  if (!factory) return;

  if (viewer.imageryLayers.length > 0) {
    viewer.imageryLayers.remove(viewer.imageryLayers.get(0), true);
  }
  const newBase = viewer.imageryLayers.addImageryProvider(factory(), 0);
  viewer.imageryLayers.lowerToBottom(newBase);

  document.querySelectorAll(".map-tab").forEach(b => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");
  viewer.scene.requestRender();
}

const seamapHost = "tiles" + String.fromCharCode(46) + "openseamap" + String.fromCharCode(46) + "org";
const seaChartUrl = `${proto}${seamapHost}/seamark/{z}/{x}/{y}.png`;

export function initMaritimeGlobe(containerId) {
  const viewer = new Cesium.Viewer(containerId, {
    baseLayer: new Cesium.ImageryLayer(MARITIME_MAP_PROVIDERS.hybrid()),
    baseLayerPicker: false,
    timeline: false,
    animation: false,
    geocoder: false,
    homeButton: false,
    navigationHelpButton: false,
    requestRenderMode: true
  });
  viewer.camera.setView({ destination: Cesium.Cartesian3.fromDegrees(-40.0, 38.0, 5500000) });

  viewer.scene.screenSpaceCameraController.minimumZoomDistance = 250.0;
  const seaChartLayer = viewer.imageryLayers.addImageryProvider(
    new Cesium.UrlTemplateImageryProvider({
      url: seaChartUrl,
      maximumLevel: 18,
      credit: "OpenSeaMap / SeaWeather"
    })
  );
  seaChartLayer.alpha = 0.85;

  const sources = {
    sea: new Cesium.CustomDataSource("sea"),
    ais: new Cesium.CustomDataSource("ais"),
    voyage: new Cesium.CustomDataSource("voyage")
  };
  Object.values(sources).forEach(s => viewer.dataSources.add(s));

  return { viewer, sources, seaChartLayer };
}

export function createShipCanvas() {
  const c = document.createElement("canvas");
  c.width = 28;
  c.height = 28;
  const ctx = c.getContext("2d");
  ctx.translate(14, 14);
  ctx.fillStyle = "#38bdf8";
  ctx.strokeStyle = "#020617";
  ctx.lineWidth = 1.6;
  ctx.beginPath();
  ctx.moveTo(0, -11);
  ctx.lineTo(5, -3);
  ctx.lineTo(5, 10);
  ctx.lineTo(-5, 10);
  ctx.lineTo(-5, -3);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  return c;
}

export function extractFirstRingDegrees(geometry) {
  if (!geometry || !geometry.coordinates) return [];
  let rawPoly = geometry.coordinates;
  if (geometry.type === "MultiPolygon") {
    for (const item of geometry.coordinates) {
      rawPoly = item;
      break;
    }
  }
  let ring = null;
  if (Array.isArray(rawPoly)) {
    for (const item of rawPoly) {
      ring = item;
      break;
    }
  }
  if (!Array.isArray(ring)) return [];

  const flat = [];
  for (const pair of ring) {
    if (Array.isArray(pair) && pair.length >= 2) {
      const [lon, lat] = pair;
      if (Number.isFinite(Number(lon)) && Number.isFinite(Number(lat))) {
        flat.push(Number(lon), Number(lat));
      }
    }
  }
  return flat;
}

export class MarineRadarController {
  constructor(viewer, seaChartLayer) {
    this.viewer = viewer;
    this.seaChartLayer = seaChartLayer;
    this.layer = null;
    this.frames = [];
    this.enabled = true;
    this.alpha = 0.75;
    this.animTimer = null;
    this.animIdx = 0;
  }

  setFrames(frames) {
    this.frames = frames || [];
    if (this.enabled && this.frames.length && !this.animTimer) {
      this.renderFrame(this.frames[this.frames.length - 1]);
    }
  }

  renderFrame(frame) {
    if (!frame || !frame.tile_url) return;
    if (this.layer) {
      this.viewer.imageryLayers.remove(this.layer, true);
      this.layer = null;
    }
    if (!this.enabled) return;
    this.layer = this.viewer.imageryLayers.addImageryProvider(
      new Cesium.UrlTemplateImageryProvider({
        url: frame.tile_url,
        maximumLevel: 7
      })
    );
    this.layer.alpha = this.alpha;
    if (this.seaChartLayer) {
      this.viewer.imageryLayers.raiseToTop(this.seaChartLayer);
    }
    this.viewer.scene.requestRender();
  }

  toggle(btn) {
    this.enabled = !this.enabled;
    if (btn) {
      btn.classList.toggle("active", this.enabled);
      btn.innerText = this.enabled ? "Weather.com Radar: ON" : "Weather.com Radar: OFF";
    }
    if (this.enabled && this.frames.length) {
      this.renderFrame(this.frames[this.frames.length - 1]);
    } else if (this.layer) {
      this.viewer.imageryLayers.remove(this.layer, true);
      this.layer = null;
      this.viewer.scene.requestRender();
    }
  }

  toggleAnimation(btn) {
    if (this.animTimer) {
      clearInterval(this.animTimer);
      this.animTimer = null;
      if (btn) {
        btn.classList.remove("active");
        btn.innerText = "▶ Animate";
      }
      if (this.frames.length) this.renderFrame(this.frames[this.frames.length - 1]);
      return;
    }
    if (!this.frames.length) return;
    if (btn) {
      btn.classList.add("active");
      btn.innerText = "⏸ Pause";
    }
    this.animTimer = setInterval(() => {
      this.renderFrame(this.frames[this.animIdx % this.frames.length]);
      this.animIdx++;
    }, 900);
  }

  setOpacity(pct) {
    this.alpha = Math.max(0, Math.min(1, Number(pct) / 100.0));
    if (this.layer) {
      this.layer.alpha = this.alpha;
      this.viewer.scene.requestRender();
    }
  }
}
