# MCRI Deployment

This folder contains documentation and deployment descriptors specific to MCRI.
This may only be needed temporarily but does keep source code management simple
when merging in upstream changes.

The `kubernetes` folder contains Kubernetes deployment descriptors for Elasticsearch
service.

The `docker-compose` folder contains docker-compose deployment descriptors for building
and deployment Seqr application.

## Building Seqr Application

```bash
SEQR_PROJECT_PATH="/Users/tommyli/Development/mcri/seqr"
COMPOSE_FILE="$SEQR_PROJECT_PATH/mcri_deploy/docker-compose/docker-compose.yml"
COMPOSE_BUILD_FILE="$SEQR_PROJECT_PATH/mcri_deploy/docker-compose/docker-compose.build.yml"
COMPOSE_ENV_FILE="$SEQR_PROJECT_PATH/mcri_deploy/docker-compose/seqr.localbuild.env"
source "$SEQR_PROJECT_PATH/mcri_deploy/docker-compose/seqr.localbuild.env"

# Build image
docker-compose -f $COMPOSE_FILE -f $COMPOSE_BUILD_FILE --env-file=$COMPOSE_ENV_FILE build

# On top of $SEQR_IMAGE_TAG, also add latest tag
docker tag $(docker images --filter=reference="${SEQR_CONTAINER_REGISTRY}/${SEQR_IMAGE_NAME}:${SEQR_IMAGE_TAG}" --quiet) "${SEQR_CONTAINER_REGISTRY}/${SEQR_IMAGE_NAME}:latest"

# Optional: Push to container registry
# This should not be necessary for local development and it'll take a while to upload.
docker-compose -f $COMPOSE_FILE -f $COMPOSE_BUILD_FILE --env-file=$COMPOSE_ENV_FILE push
```
