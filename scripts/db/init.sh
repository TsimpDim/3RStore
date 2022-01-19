#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER local_user WITH password 'local-3rstore';
    CREATE DATABASE main;
    GRANT ALL PRIVILEGES ON DATABASE main TO local_user;
EOSQL
