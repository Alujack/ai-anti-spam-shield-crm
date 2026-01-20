-- AI Anti-Spam Shield - PostgreSQL Initialization Script
-- This script is run when the PostgreSQL container starts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables (Prisma will handle the actual schema, but we ensure the database is ready)

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'AI Shield Database initialized successfully';
END $$;
