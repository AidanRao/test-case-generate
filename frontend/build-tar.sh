#!/bin/bash

VERSION=$(date +"%Y%m%d%H%M")
IMAGE_NAME="test-case-generate-frontend"

IMAGE_TAG="${IMAGE_NAME}:${VERSION}"
TAR_NAME="${IMAGE_NAME}-${VERSION}.tar"


docker buildx build \
  --platform linux/amd64 \
  -t test-case-generate-frontend \
  . \
  --output type=docker,dest=${TAR_NAME}


echo "Build ${IMAGE_TAG} success, tar name: ${TAR_NAME}"
