-- Auto-run on first postgres container init (mounted into /docker-entrypoint-initdb.d).
-- unaccent is used for Vietnamese diacritic-insensitive search (see exercise repository).
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS vector;
