#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

TARGET_DIR="frontend/cesium"
SHARED_CESIUM="../flight-forecast-engine/frontend/cesium"
CESIUM_VER=$(tr -d '[:space:]' < frontend/cesium_version.txt 2>/dev/null || echo "1.121")

rm -rf "${TARGET_DIR}"

if [ -f "${SHARED_CESIUM}/Cesium.js" ]; then
  echo "=== Linking existing CesiumJS v${CESIUM_VER} from ${SHARED_CESIUM} ==="
  ln -s "../${SHARED_CESIUM}" "${TARGET_DIR}"
  echo "Done! Linked ${TARGET_DIR} -> ${SHARED_CESIUM}"
  exit 0
fi

echo "=== Downloading CesiumJS v${CESIUM_VER} into ${TARGET_DIR} ==="
mkdir -p "${TARGET_DIR}"
cd "${TARGET_DIR}"

curl -L -o cesium.zip "https://github.com{CESIUM_VER}/Cesium-${CESIUM_VER}.zip"
python3 -m zipfile -e cesium.zip .
mv Build/Cesium/* .
rm -rf Build Apps ThirdParty cesium.zip index.html server.cjs package.json LICENSE.md CHANGES.md README.md

echo "Done! CesiumJS v${CESIUM_VER} installed in ${TARGET_DIR}"
