#!/usr/bin/env bash

set -ex

COMPOSE_FILE=mcri_deploy/docker-compose/docker-compose.yml
COMPOSE_BUILD_FILE=mcri_deploy/docker-compose/docker-compose.build.yml
COMPOSE_ENV_FILE=mcri_deploy/docker-compose/seqr.sample.env

docker-compose -f $COMPOSE_FILE -f $COMPOSE_BUILD_FILE --env-file=$COMPOSE_ENV_FILE up -d seqr
docker-compose -f $COMPOSE_FILE -f $COMPOSE_BUILD_FILE --env-file=$COMPOSE_ENV_FILE logs postgres
docker-compose -f $COMPOSE_FILE -f $COMPOSE_BUILD_FILE --env-file=$COMPOSE_ENV_FILE logs redis

sleep 30
docker-compose -f $COMPOSE_FILE -f $COMPOSE_BUILD_FILE --env-file=$COMPOSE_ENV_FILE logs seqr
echo -ne 'testpassword\n' docker-compose -f $COMPOSE_FILE -f $COMPOSE_BUILD_FILE --env-file=$COMPOSE_ENV_FILE exec seqr python manage.py createsuperuser --username test --email test@test.com
