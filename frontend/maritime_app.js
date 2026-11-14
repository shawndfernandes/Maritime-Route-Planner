import { initMaritimeGlobe, switchMaritimeMapLayer, MarineRadarController } from "./maritime_map.js";
import { renderPortsAndStorms, renderLiveVessels, renderSeaVoyage } from "./maritime_renderer.js";
import { drawWaveChart } from "./maritime_chart.js";

const API = "http://localhost:8002/api/maritime";
const { viewer, sources, seaChartLayer } = initMaritimeGlobe("cesiumContainer");
const radar = new MarineRadarController(viewer, seaChartLayer);

window.setMaritimeMapLayer = (key, btn) => switchMaritimeMapLayer(viewer, key, btn);

window.toggleSeaCharts = (btn) => {
  if (!seaChartLayer) return;
  seaChartLayer.show = !seaChartLayer.show;
  btn.classList.toggle("active", seaChartLayer.show);
  btn.innerText = seaChartLayer.show ? "SeaWeather Charts: ON" : "SeaWeather Charts: OFF";
  viewer.scene.requestRender();
};

window.toggleMarineRadar = (btn) => radar.toggle(btn);
window.toggleMarineRadarAnim = (btn) => radar.toggleAnimation(btn);
window.setMarineRadarOpacity = (pct) => radar.setOpacity(pct);

function populatePortDropdowns(ports) {
  const origSel = document.getElementById("origPort");
  const destSel = document.getElementById("destPort");
  if (!origSel || !destSel || origSel.options.length > 0) return;

  Object.entries(ports || {}).forEach(([code, tuple]) => {
    const label = tuple[2] || code;
    origSel.add(new Option(label, code));
    destSel.add(new Option(label, code));
  });

  if (origSel.querySelector('option[value="USNYC"]')) origSel.value = "USNYC";
  if (destSel.querySelector('option[value="NLRTM"]')) destSel.value = "NLRTM";
}

async function loadMarineSnapshot() {
  try {
    const res = await fetch(`${API}/snapshot`);
    const data = await res.json();

    radar.setFrames(data.radar_config?.frames || []);
    populatePortDropdowns(data.ports || {});
    renderPortsAndStorms(sources.sea, data.ports || {}, data.storms_geojson?.features || []);
    renderLiveVessels(sources.ais, data.vessels || []);

    const ss = data.sea_state || {};
    document.getElementById("seaWeatherCard").innerHTML = `
      <div style="display:flex; justify-content:space-between;">
        <strong>SeaWeather & Weather.com Marine</strong>
        <span>${data.radar_config?.provider || "Marine Radar"}</span>
      </div>
      <div style="margin-top:3px;">
        <strong>Wave Height:</strong> ${ss.wave_height_m}m (Swell ${ss.swell_height_m}m @ ${ss.wave_period_s}s) · <strong>Marine Wind:</strong> ${ss.wind_kt} kt (${ss.wind_dir_deg}°) · <strong>Air:</strong> ${ss.air_temp_f}°F
      </div>
    `;

    document.getElementById("status").innerText =
      `AIS: ${data.ais_source} (${(data.vessels || []).length} ships) | Marine Warnings: ${(data.storms_geojson?.features || []).length}`;
    viewer.scene.requestRender();
  } catch (err) {
    document.getElementById("status").innerText = "Waiting for Maritime backend (:8002)...";
  }
}

window.planVoyage = async () => {
  const o = document.getElementById("origPort").value.trim();
  const d = document.getElementById("destPort").value.trim();
  const spdEl = document.getElementById("vesselSpeedInput");
  const spd = spdEl ? Math.max(5, Math.min(35, Number(spdEl.value) || 18)) : 18;
  if (!o || !d) return;

  document.getElementById("status").innerText = `Computing storm-free sea lane ${o} -> ${d} @ ${spd} kt...`;
  const res = await fetch(`${API}/route?origin=${encodeURIComponent(o)}&destination=${encodeURIComponent(d)}&speed_kt=${spd}`);
  const data = await res.json();

  renderSeaVoyage(sources.voyage, data);

  const maxWave = Math.max(0, ...(data.wave_profile || []).map(w => w.wave_height_m));
  const card = document.getElementById("card");
  card.style.display = "block";
  card.innerHTML = `
    <div><strong>Voyage:</strong> ${data.origin.name} → ${data.destination.name}</div>
    <div><strong>Direct Distance:</strong> ${data.direct_nm} NM | <strong>Safe Sea Lane:</strong> ${data.safe_nm} NM</div>
    <div><strong>Est. Transit Time (@${spd} kt):</strong> ${data.eta_hours} hrs | <strong>Peak Wave Height:</strong> ${maxWave.toFixed(1)} m</div>
  `;

  drawWaveChart(data.wave_profile || []);
  viewer.flyTo(sources.voyage.entities);
  viewer.scene.requestRender();
};

const clickHandler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
clickHandler.setInputAction((movement) => {
  const picked = viewer.scene.pick(movement.position);
  if (!Cesium.defined(picked) || !picked.id || !picked.id.properties) return;
  const p = picked.id.properties.getValue(Cesium.JulianDate.now());
  const card = document.getElementById("card");
  if (p.kind === "AIS_VESSEL") {
    card.style.display = "block";
    card.innerHTML = `
      <div><strong>Live AIS Vessel:</strong> ${p.name} (MMSI: ${p.mmsi})</div>
      <div><strong>Ongoing Destination:</strong> ${p.destination || "Underway"}</div>
      <div><strong>Position:</strong> ${p.lat}°, ${p.lon}°</div>
      <div><strong>Speed:</strong> ${p.speed_kt} kt · <strong>Course:</strong> ${Math.round(p.heading)}°</div>
    `;
  } else if (p.kind === "MARINE_STORM") {
    card.style.display = "block";
    card.innerHTML = `<strong>${p.event} (${p.severity})</strong><br/>${p.headline}`;
  }
}, Cesium.ScreenSpaceEventType.LEFT_CLICK);

loadMarineSnapshot();
setInterval(loadMarineSnapshot, 30000);
