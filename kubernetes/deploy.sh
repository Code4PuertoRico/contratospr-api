#!/bin/bash

set -e

IMAGE_NAME="gcr.io/tracking-contratos-pr/tracking-contratos-pr:latest"
docker build -t "$IMAGE_NAME" .
docker push "$IMAGE_NAME"

DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "$IMAGE_NAME")

kubectl set image deployment tracking-contratospr-web web="$DIGEST"
kubectl set image deployment tracking-contratospr-worker worker="$DIGEST"
