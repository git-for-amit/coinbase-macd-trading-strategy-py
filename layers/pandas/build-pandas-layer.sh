#!/bin/bash
# Create a minimal pandas layer for AWS Lambda (Python 3.9 x86_64)

# Settings
PANDAS_VERSION="2.2.3"  # Specify the pandas version
PYTHON_VERSION="3.9"      # Python runtime version
TARGET_DIR="python/lib/python${PYTHON_VERSION}/site-packages"
LAYER_NAME="pandas_minimal_layer"

# Create directories
mkdir -p ${TARGET_DIR}

# Install pandas and its dependencies into target directory (minimal)
docker run --platform linux/amd64 --rm -v "$PWD":/var/task \
    public.ecr.aws/sam/build-python${PYTHON_VERSION}:latest \
    /bin/bash -c "pip install --no-cache-dir pandas==${PANDAS_VERSION} -t ${TARGET_DIR}"

# Remove unnecessary files (optional, but helps reduce size)
find ${TARGET_DIR} -name "*.pyc" -delete
find ${TARGET_DIR} -name "__pycache__" -type d -delete
rm -rf ${TARGET_DIR}/pandas/tests
rm -rf ${TARGET_DIR}/numpy/tests
rm -rf ${TARGET_DIR}/scipy/tests

# Zip the layer
zip -r ${LAYER_NAME}.zip python

# Display zip file size
echo "Layer created: ${LAYER_NAME}.zip"
du -sh ${LAYER_NAME}.zip
