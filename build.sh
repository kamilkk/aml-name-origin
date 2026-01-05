#!/bin/bash
# Build and run the Docker image

set -e

echo "=========================================="
echo "Building AML Name Classifier Docker Image"
echo "=========================================="

# Build the image
docker build -t aml-name-classifier:latest .

echo ""
echo "Image built successfully!"
echo ""
echo "To run the container:"
echo "  docker-compose up -d"
echo ""
echo "Or manually:"
echo "  docker run -p 5050:5050 aml-name-classifier:latest"
