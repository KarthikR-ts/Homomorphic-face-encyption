-- Initialize PostgreSQL database with required extensions

-- Enable pgcrypto extension for encryption functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create database if it doesn't exist (though docker-compose handles this)
-- This is just in case
