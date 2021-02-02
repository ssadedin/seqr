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
# Clone if necessary, otherwise cd to git clone of seqr
git clone https://github.com/ssadedin/seqr.git; cd seqr

SEQR_PROJECT_PATH=$(pwd)
SEQR_GIT_BRANCH="mcri/master"
cd $SEQR_PROJECT_PATH; git submodule update --init --recursive"

git checkout -b "$SEQR_GIT_BRANCH" --track "origin/$SEQR_GIT_BRANCH"

COMPOSE_FILE="$SEQR_PROJECT_PATH/mcri_deploy/docker-compose/docker-compose.yml"
COMPOSE_BUILD_FILE="$SEQR_PROJECT_PATH/mcri_deploy/docker-compose/docker-compose.build.yml"

# Use seqr.sample.env or create your own
COMPOSE_ENV_FILE="$SEQR_PROJECT_PATH/mcri_deploy/docker-compose/seqr.test.env"
source $COMPOSE_ENV_FILE

# Set tag to be latest Git commit hash
export GIT_COMMIT_HASH=$(git rev-parse HEAD)
export SEQR_IMAGE_TAG=$GIT_COMMIT_HASH

# Build image
docker-compose --verbose \
  -f $COMPOSE_FILE \
  -f $COMPOSE_BUILD_FILE \
  --env-file=$COMPOSE_ENV_FILE \
  build \
  --build-arg "gitcommithash=$GIT_COMMIT_HASH" \
  --build-arg "SEQR_REPO=https://github.com/ssadedin/seqr" \
  --build-arg "SEQR_GIT_BRANCH=$SEQR_GIT_BRANCH"

# On top of $SEQR_IMAGE_TAG, also add latest tag
docker tag $(docker images --filter=reference="${SEQR_CONTAINER_REGISTRY}/${SEQR_IMAGE_NAME}:${SEQR_IMAGE_TAG}" --quiet) "${SEQR_CONTAINER_REGISTRY}/${SEQR_IMAGE_NAME}:latest"

# Optional: Push to container registry
# This should not be necessary for local development and it'll take a while to upload.
docker-compose -f $COMPOSE_FILE -f $COMPOSE_BUILD_FILE --env-file=$COMPOSE_ENV_FILE push
docker push "${SEQR_CONTAINER_REGISTRY}/${SEQR_IMAGE_NAME}:latest"

# Optional: Running and stopping the newly built seqr
docker-compose -f $COMPOSE_FILE -f $COMPOSE_BUILD_FILE --env-file=$COMPOSE_ENV_FILE up -d postgres

docker-compose -f $COMPOSE_FILE -f $COMPOSE_BUILD_FILE --env-file=$COMPOSE_ENV_FILE stop
```

## TODOs

* Enable Travis build to authenticate with MCRI container registry to push and pull images, here are some useful links:
  * [https://ciaranarcher.github.io/gcp/travis/2017/02/23/pushing-from-travis-to-google-container-registry.html](https://ciaranarcher.github.io/gcp/travis/2017/02/23/pushing-from-travis-to-google-container-registry.html)
  * [https://cloud.google.com/container-registry/docs/overview](https://cloud.google.com/container-registry/docs/overview)
  * [https://cloud.google.com/container-registry/docs/continuous-delivery](https://cloud.google.com/container-registry/docs/continuous-delivery)
  * [https://docs.travis-ci.com/user/docker/](https://docs.travis-ci.com/user/docker/)
  * [https://cloud.google.com/container-registry/docs/advanced-authentication](https://cloud.google.com/container-registry/docs/advanced-authentication)
  * [https://cloud.google.com/container-registry/docs/access-control](https://cloud.google.com/container-registry/docs/access-control)
