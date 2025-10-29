\connect postgres
DO $$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'curated_user'
   ) THEN
      CREATE ROLE curated_user WITH LOGIN PASSWORD 'curatedpass';
   END IF;
END
$$;

SELECT 'CREATE DATABASE curated OWNER curated_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'curated')\gexec

\connect curated
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS gold;

GRANT ALL PRIVILEGES ON DATABASE curated TO curated_user;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO curated_user;
GRANT ALL PRIVILEGES ON SCHEMA gold TO curated_user;

DO $$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'debezium_user'
   ) THEN
      CREATE ROLE debezium_user WITH LOGIN REPLICATION PASSWORD 'debezpass';
   END IF;
END
$$;

GRANT CONNECT ON DATABASE curated TO debezium_user;
GRANT USAGE ON SCHEMA gold TO debezium_user;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO debezium_user;
ALTER DEFAULT PRIVILEGES FOR ROLE curated_user IN SCHEMA gold GRANT SELECT ON TABLES TO debezium_user;
