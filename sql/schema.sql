CREATE TABLE assets (
	id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	street_name TEXT,
	address TEXT,
	ref_catastral TEXT UNIQUE,
	lat FLOAT8,
	lng FLOAT8,
	business_name TEXT,
	surface_m2 INT,
	usage TEXT,
	updated_at TIMESTAMPTZ DEFAULT now(),
	snapshot_date TIMESTAMPTZ DEFAULT now(),
	is_vacant BOOLEAN DEFAULT FALSE
);
