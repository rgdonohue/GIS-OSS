-- Enable PostGIS and related extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Enable pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create audit schema
CREATE SCHEMA IF NOT EXISTS audit;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.query_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_id TEXT,
    query_text TEXT NOT NULL,
    query_type TEXT,
    execution_time_ms INTEGER,
    status TEXT NOT NULL,
    error_message TEXT,
    data_sources JSONB,
    attribution JSONB,
    metadata JSONB
);

-- Create index on timestamp for efficient querying
CREATE INDEX idx_query_log_timestamp ON audit.query_log(timestamp DESC);
CREATE INDEX idx_query_log_user ON audit.query_log(user_id);
CREATE INDEX idx_query_log_status ON audit.query_log(status);

-- Create data schema
CREATE SCHEMA IF NOT EXISTS data;

-- Create sample table for spatial data
CREATE TABLE IF NOT EXISTS data.features (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT,
    category TEXT,
    geom GEOMETRY(Geometry, 4326),
    properties JSONB,
    source TEXT,
    license TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create spatial index
CREATE INDEX idx_features_geom ON data.features USING GIST(geom);
CREATE INDEX idx_features_category ON data.features(category);
CREATE INDEX idx_features_properties ON data.features USING GIN(properties);

-- Create embeddings table for RAG
CREATE TABLE IF NOT EXISTS data.embeddings (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    document_id UUID,
    chunk_text TEXT NOT NULL,
    embedding vector(384), -- Adjust dimension based on model
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create vector index for similarity search (set lists per pgvector requirements)
CREATE INDEX idx_embeddings_vector
    ON data.embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Create governance schema
CREATE SCHEMA IF NOT EXISTS governance;

-- Create license tracking table
CREATE TABLE IF NOT EXISTS governance.licenses (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    license_type TEXT NOT NULL,
    attribution_required BOOLEAN DEFAULT true,
    share_alike BOOLEAN DEFAULT false,
    commercial_use BOOLEAN DEFAULT true,
    license_url TEXT,
    attribution_text TEXT,
    metadata JSONB
);

-- Insert common licenses
INSERT INTO governance.licenses (dataset_name, license_type, attribution_required, share_alike, commercial_use, license_url, attribution_text)
VALUES
    ('OpenStreetMap', 'ODbL', true, true, true, 'https://www.openstreetmap.org/copyright', '© OpenStreetMap contributors'),
    ('Natural Earth', 'Public Domain', false, false, true, 'https://www.naturalearthdata.com/about/terms-of-use/', NULL),
    ('US Census', 'Public Domain', false, false, true, 'https://www.census.gov/data/developers/about/terms-of-service.html', NULL)
ON CONFLICT DO NOTHING;

-- Create function for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for features table
CREATE TRIGGER update_features_updated_at BEFORE UPDATE ON data.features
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create helper functions for common spatial operations
CREATE OR REPLACE FUNCTION data.buffer_meters(geom geometry, distance_meters float)
RETURNS geometry AS $$
BEGIN
    -- Buffer in meters using appropriate projection
    RETURN ST_Transform(
        ST_Buffer(
            ST_Transform(geom,
                CASE
                    WHEN ST_Y(ST_Centroid(geom)) > 70 THEN 3413  -- North Polar Stereographic
                    WHEN ST_Y(ST_Centroid(geom)) < -70 THEN 3031 -- South Polar Stereographic
                    ELSE 3857  -- Web Mercator (fallback)
                END
            ),
            distance_meters
        ),
        4326
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Grant permissions (adjust as needed)
GRANT USAGE ON SCHEMA data TO gis_user;
GRANT SELECT ON ALL TABLES IN SCHEMA data TO gis_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA data GRANT SELECT ON TABLES TO gis_user;

GRANT USAGE ON SCHEMA governance TO gis_user;
GRANT SELECT ON ALL TABLES IN SCHEMA governance TO gis_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA governance GRANT SELECT ON TABLES TO gis_user;

-- Add comment documentation
COMMENT ON SCHEMA data IS 'Main schema for spatial and vector data';
COMMENT ON SCHEMA audit IS 'Audit logging for queries and operations';
COMMENT ON SCHEMA governance IS 'Data governance and license tracking';
COMMENT ON TABLE data.features IS 'Main spatial features table';
COMMENT ON TABLE data.embeddings IS 'Vector embeddings for RAG';
COMMENT ON TABLE audit.query_log IS 'Audit trail of all queries';
COMMENT ON TABLE governance.licenses IS 'License information for datasets';
