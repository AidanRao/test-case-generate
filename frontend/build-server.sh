#!/bin/bash

# Check if version is provided as argument
if [ $# -eq 1 ]; then
  VERSION="$1"
  echo "Using provided version: ${VERSION}"
else
  VERSION=$(date +"%Y%m%d%H%M")
  echo "Using auto-generated version: ${VERSION}"
fi

IMAGE_NAME="test-case-generate-frontend"
LOCAL_TAG="${IMAGE_NAME}:${VERSION}"

# Define multiple repositories
REPOSITORIES=(
  "chenxuanrao"         # Docker Hub
  "crpi-cayqrvwyllekrteg.cn-beijing.personal.cr.aliyuncs.com/personal_demos"  # Aliyun
)

# Build image tags for all repositories
REMOTE_TAGS=()
for REPO in "${REPOSITORIES[@]}"; do
  REMOTE_TAGS+=("${REPO}/${IMAGE_NAME}:${VERSION}")
done

# Step 1: Build local image
echo "Step 1: Building local image ${LOCAL_TAG}"
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "${LOCAL_TAG}" \
  .

if [ $? -ne 0 ]; then
  echo "❌ Build failed, exiting..."
  exit 1
fi

echo "✅ Local build success"

# Step 2: Add tags for remote repositories
echo "Step 2: Adding tags for remote repositories"
for REMOTE_TAG in "${REMOTE_TAGS[@]}"; do
  echo "🔖 Adding tag ${REMOTE_TAG} to local image"
  docker tag "${LOCAL_TAG}" "${REMOTE_TAG}"
  if [ $? -ne 0 ]; then
    echo "❌ Failed to add tag ${REMOTE_TAG}"
    exit 1
  fi
done

echo "All remote tags added successfully"

# Step 3: Push to all repositories
echo "Step 3: Pushing to all repositories"
for REMOTE_TAG in "${REMOTE_TAGS[@]}"; do
  echo "📤 Pushing ${REMOTE_TAG}..."
  docker push "${REMOTE_TAG}"
  if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed ${REMOTE_TAG}"
  else
    echo "❌ Failed to push ${REMOTE_TAG}"
  fi
done

echo "✅ All push operations completed"

# Optional: Clean up local tags
echo "Step 4: Cleaning up local tags"
docker rmi "${LOCAL_TAG}"
for REMOTE_TAG in "${REMOTE_TAGS[@]}"; do
  docker rmi "${REMOTE_TAG}"
done

echo "🧹 Cleanup completed"
