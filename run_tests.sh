#!/usr/bin/env bash

db_container_name=google-standup-bot-postgres
db_host=localhost
db_port=55123

echo -e "Start PostgreSQL container"
docker run -d --rm \
  --name ${db_container_name} \
  -e POSTGRES_PASSWORD=postgres \
  -p ${db_port}:5432 \
  postgres:13

echo -e "Check PostgreSQL container"
while ! pg_isready -h ${db_host} -p ${db_port} -t 10 -U postgres
do
  echo "$(date) - waiting for database to start"
  sleep 1
done

export DB_HOST=${db_host}
export DB_PORT=${db_port}
export DB_NAME=postgres
export DB_USERNAME=postgres
export DB_PASSWORD=postgres

echo -e "Run Flake8"
flake8 ./bot --count --max-line-length=120 --show-source --statistics
flake8 ./bot --count --exit-zero --max-complexity=20 --max-line-length=120 --statistics

echo -e "Run unit tests"
pytest-3

echo -e "Stop PostgreSQL container"
docker stop ${db_container_name}
