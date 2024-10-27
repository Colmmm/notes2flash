#!/bin/bash

# Function to get hash of requirements.txt
get_requirements_hash() {
    if [ -f "requirements.txt" ]; then
        sha256sum requirements.txt | cut -d' ' -f1
    else
        echo ""
    fi
}

# Function to get stored hash
get_stored_hash() {
    if [ -f "addon/libs/.requirements_hash" ]; then
        cat "addon/libs/.requirements_hash"
    else
        echo ""
    fi
}

# Get current and stored hashes
CURRENT_HASH=$(get_requirements_hash)
STORED_HASH=$(get_stored_hash)

# Determine if we need to rebuild
if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
    echo "Requirements have changed, rebuilding..."
    BUILD_FLAG="--build"
    # Store new hash after successful build
    mkdir -p addon/libs
    echo "$CURRENT_HASH" > "addon/libs/.requirements_hash"
else
    echo "Requirements unchanged, skipping rebuild..."
    BUILD_FLAG=""
fi

# Step 1: Run Docker Compose to bundle the addon
echo "Bundling the addon using Docker Compose..."
docker-compose up $BUILD_FLAG --exit-code-from addon_bundler

# Step 2: Define paths
ANKI_DIR="Anki_23.12.1"
ANKI_BASE="${ANKI_DIR}/anki_config"
ADDON_DIR="${ANKI_BASE}/addons21/notes2flash"
BUNDLED_ZIP="output/notes2flash.ankiaddon"
UNZIP_DIR="output/unzipped"

# Check if bundling was successful
if [ ! -f "$BUNDLED_ZIP" ]; then
    echo "Error: Addon bundling failed. Bundle file not found: $BUNDLED_ZIP"
    exit 1
fi

# Step 3: Remove the old notes2flash addon in Anki_23.12.1
if [ -d "$ADDON_DIR" ]; then
    echo "Removing the old notes2flash addon..."
    rm -rf "$ADDON_DIR"
else
    echo "No existing notes2flash addon found."
fi

# Step 4: Create the addons directory if it doesn't exist
mkdir -p "${ANKI_BASE}/addons21"

# Step 5: Copy the newly bundled addon zip to the Anki addon directory
echo "Copying the newly bundled addon to the Anki addons directory..."
cp "$BUNDLED_ZIP" "${ANKI_BASE}/addons21/"

# Step 6: Unzip the bundled addon into the appropriate Anki directory
echo "Unzipping the addon to the Anki addons directory..."
mkdir -p "$ADDON_DIR"
unzip -o "${ANKI_BASE}/addons21/notes2flash.ankiaddon" -d "$ADDON_DIR"

# Verify the addon was extracted correctly
if [ ! -f "$ADDON_DIR/manifest.json" ]; then
    echo "Error: Addon extraction failed. manifest.json not found in $ADDON_DIR"
    exit 1
fi

# Step 7: Copy the my_notes2flash_config.json to the Anki addon directory as config.json
echo "Copying my_notes2flash_config.json to the Anki addons directory as config.json..."
cp "my_notes2flash_config.json" "${ANKI_BASE}/addons21/notes2flash/config.json"

# Step 8: Clean up the old zip file
echo "Cleaning up..."
rm "${ANKI_BASE}/addons21/notes2flash.ankiaddon"

echo "Addon replaced successfully!"

# Step 9: Run Anki with the new bundled addon
export ANKI_BASE="${ANKI_BASE}"
echo "Running Anki with ANKI_BASE=${ANKI_BASE}..."
./${ANKI_DIR}/anki
