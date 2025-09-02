-- Create database (run this in PostgreSQL)
CREATE DATABASE nepl_lims_local;

-- Create user (optional, for security)
CREATE USER nepl_dev WITH PASSWORD 'Aimlsn@2025';
GRANT ALL PRIVILEGES ON DATABASE nepl_lims_local TO nepl_dev;
