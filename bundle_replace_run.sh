#!/bin/bash

# Step 1: Run Docker Compose to bundle the addon
echo "Bundling the addon using Docker Compose..."
docker-compose up

# Step 2: Define paths
ANKI_DIR="Anki_23.12.1"
ANKI_BASE="${ANKI_DIR}/anki_config"
ADDON_DIR="${ANKI_BASE}/addons21/notes2flash"
BUNDLED_ZIP="output/notes2flash.ankiaddon"
UNZIP_DIR="output/unzipped"

# Step 3: Remove the old notes2flash addon in Anki_23.12.1
if [ -d "$ADDON_DIR" ]; then
  echo "Removing the old notes2flash addon..."
  rm -rf "$ADDON_DIR"
else
  echo "No existing notes2flash addon found."
fi

# Step 4: Copy the newly bundled addon zip to the Anki addon directory
if [ -f "$BUNDLED_ZIP" ]; then
  echo "Copying the newly bundled addon to the Anki addons directory..."
  cp "$BUNDLED_ZIP" "${ANKI_BASE}/addons21/"
else
  echo "Error: Bundled addon zip file not found: $BUNDLED_ZIP"
  exit 1
fi

# Step 5: Unzip the bundled addon into the appropriate Anki directory
echo "Unzipping the addon to the Anki addons directory..."
mkdir -p "$ADDON_DIR"
unzip -o "${ANKI_BASE}/addons21/notes2flash.ankiaddon" -d "$ADDON_DIR"

# Step 6: Clean up the old zip file (optional)
echo "Cleaning up..."
rm "${ANKI_BASE}/addons21/notes2flash.ankiaddon"

echo "Addon replaced successfully!"

# Step 7: Run Anki with the new bundled addon
export ANKI_BASE="${ANKI_BASE}"
echo "Running Anki with ANKI_BASE=${ANKI_BASE}..."
./${ANKI_DIR}/anki
