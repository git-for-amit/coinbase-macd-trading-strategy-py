#!/bin/bash
# Save as build-layers.sh

# Dependency list (excluding boto3)
dependencies=(
    "coinbase-advanced-py"
    "pandas"
    "requests"
    "ta"
    "python-dotenv"
)

for dep in "${dependencies[@]}"; do
    echo "Building layer for: $dep"
    
    # Create temp directory
    mkdir -p "python/lib/python3.9/site-packages"
    
    # Install dependency using AWS Linux container
    docker run --platform linux/amd64 --rm -v "$PWD":/var/task \
        public.ecr.aws/sam/build-python3.9:latest \
        /bin/sh -c "pip install $dep -t python/lib/python3.9/site-packages/ && chmod -R 755 python"
    
    # Zip layer
    zip -r "${dep}_layer.zip" python
    
    # Cleanup
    rm -rf python
done
