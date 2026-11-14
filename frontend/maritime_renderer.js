import { createShipCanvas, extractFirstRingDegrees } from "./maritime_map.js";

const SHIP_ICON = createShipCanvas();

export function renderPortsAndStorms(seaSource, ports, stormFeatures) {
  seaSource.entities.removeAll();

  Object.entries(ports || {}).forEach(([code, coordsTuple]) => {
    const [lat, lon] = coordsTuple;
    seaSource.entities.add({
      position: Cesium.Cartesian3.fromDegrees(lon, lat, 200),
      point: { pixelSize: 9, color: Cesium.Color.LIMEGREEN, outlineColor: Cesium.Color.BLACK, outlineWidth: 2 },
      label: { text: code, font: "11px sans-serif", pixelOffset: new Cesium.Cartesian2(0, -14) }
    });
  });

  (stormFeatures || []).forEach(f => {
    const props = f.properties || {};
    const flat = extractFirstRingDegrees(f.geometry);
    if (flat.length >= 6) {
      seaSource.entities.add({
        properties: {
          kind: "MARINE_STORM",
          event: props.event || "Marine Warning",
          severity: props.severity || "Severe",
          headline: props.headline || ""
        },
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
          height: 0,
          material: Cesium.Color.RED.withAlpha(0.30),
          outline: true,
          outlineColor: Cesium.Color.YELLOW
        }
      });
    }
  });
}

export function renderLiveVessels(aisSource, vessels) {
  aisSource.entities.removeAll();

  (vessels || []).forEach(v => {
    aisSource.entities.add({
      name: `${v.name} (MMSI ${v.mmsi})`,
      properties: { kind: "AIS_VESSEL", ...v },
      position: Cesium.Cartesian3.fromDegrees(v.lon, v.lat, 50),
      billboard: {
        image: SHIP_ICON,
        width: 18,
        height: 18,
        rotation: -Cesium.Math.toRadians(v.heading || 0),
        alignedAxis: Cesium.Cartesian3.UNIT_Z
      },
      label: {
        text: `${v.name} · ${v.speed_kt}kt`,
        font: "10px sans-serif",
        fillColor: Cesium.Color.LIGHTSKYBLUE,
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cesium.Cartesian2(0, -14),
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 900000)
      }
    });
  });
}

export function renderSeaVoyage(voyageSource, data) {
  voyageSource.entities.removeAll();

  voyageSource.entities.add({
    polyline: {
      positions: Cesium.Cartesian3.fromDegreesArray(data.direct_waypoints.flatMap(w => [w.lon, w.lat])),
      width: 4,
      material: Cesium.Color.ORANGE
    }
  });

  voyageSource.entities.add({
    polyline: {
      positions: Cesium.Cartesian3.fromDegreesArray(data.safe_waypoints.flatMap(w => [w.lon, w.lat])),
      width: 6,
      material: Cesium.Color.CYAN
    }
  });
}
