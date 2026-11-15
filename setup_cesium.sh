#!/usr/bin/env bash

set -e
REPO="CesiumGS/cesium"
API_URL="https://github.com"
echo "Fetching latest Cesium release info..."

# Fetch the download URL for the Cesium-*.zip file
#DOWNLOAD_URL=$(curl -s "$API_URL" | grep -oE "https://github.com[^\"]+/Cesium-[0-9.]+\.zip" | head -n 1)
DOWNLOAD_URL=$(curl -s "https://cesium.com/downloads/" | grep -oE 'https://github\.com/CesiumGS/cesium/releases/download/[^"]+/Cesium-[0-9.]+\.zip' | head -n 1)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "Error: Could not find the latest release download URL."
    exit 1
fi

FILENAME=$(basename "$DOWNLOAD_URL")
echo "Downloading $FILENAME from $DOWNLOAD_URL..."
curl -L -o "$FILENAME" "$DOWNLOAD_URL"
echo "Download complete: $FILENAME"
cd ./frontend
mkdir cesium
cd cesium
mv ../../$FILENAME ./cesium.zip
python3 -m zipfile -e cesium.zip .
mv Build/Cesium/* .
rm -rf Build Apps ThirdParty cesium.zip index.html server.cjs package.json LICENSE.md CHANGES.md README.md

echo "Done! CesiumJS v${FILENAME} installed!!"
