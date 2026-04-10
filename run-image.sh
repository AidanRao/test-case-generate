#!/bin/bash

docker run -d \
  --name test-case-generate \
  --restart always \
  -p 8010:80 \
  -v "$(pwd)/backend/config.json:/app/config.json" \
  -v "$(pwd)/backend/data:/app/data" \
  test-case-generate
  