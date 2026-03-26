-- ============================================================================
-- Energy Storage Investment Decision System - City Policy Schema
-- Migration: 20260326000000_city_policy_schema.sql
-- ============================================================================

-- Verification method enum for policy data
CREATE TYPE verification_method AS ENUM ('manual', 'automated');

-- Monitoring check type enum
CREATE TYPE monitoring_check_type AS ENUM ('scheduled', 'user_report', 'automated');

-- ============================================================================
-- Table: city_policies
-- Purpose: Store city-level electricity pricing policies for energy storage calculations
-- Key Design: City-level granularity (NOT province-level) because
--             广州、深圳、佛山、东莞 have different rates within the same province
-- ============================================================================
CREATE TABLE IF NOT EXISTS city_policies (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Location identifiers (CITY-LEVEL, not province)
  city_name TEXT NOT NULL,                    -- e.g., "深圳市"
  province_code TEXT NOT NULL,                -- e.g., "GD"
  province_name TEXT NOT NULL,                -- e.g., "广东"

  -- Pricing (元/kWh)
  peak_price NUMERIC(10, 4) NOT NULL,         -- 峰时电价
  valley_price NUMERIC(10, 4) NOT NULL,       -- 谷时电价
  flat_price NUMERIC(10, 4) NOT NULL,         -- 平时电价

  -- Peak/valley hours (24-hour format)
  peak_hours TEXT NOT NULL,                   -- e.g., "10:00-12:00,14:00-19:00"
  valley_hours TEXT NOT NULL,                 -- e.g., "00:00-08:00,19:00-24:00"

  -- Subsidy information
  subsidy_amount NUMERIC(10, 4) DEFAULT 0,    -- 元/kWh, 0 if none

  -- Data provenance and freshness
  source_url TEXT NOT NULL,                   -- 深圳市发改委官网URL
  effective_date DATE NOT NULL,               -- YYYY-MM-DD
  last_verified_at TIMESTAMP WITH TIME ZONE,  -- Last manual verification
  verification_method verification_method DEFAULT 'manual',
  confidence_score INTEGER DEFAULT 3 CHECK (confidence_score BETWEEN 1 AND 5),  -- 1-5 scale

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Constraints
  CONSTRAINT city_policies_unique_city UNIQUE (city_name, province_code)
);

-- Indexes for common queries
CREATE INDEX idx_city_policies_city_name ON city_policies(city_name);
CREATE INDEX idx_city_policies_province_code ON city_policies(province_code);
CREATE INDEX idx_city_policies_effective_date ON city_policies(effective_date DESC);
CREATE INDEX idx_city_policies_last_verified ON city_policies(last_verified_at DESC);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_city_policies_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_city_policies_updated_at
  BEFORE UPDATE ON city_policies
  FOR EACH ROW
  EXECUTE FUNCTION update_city_policies_updated_at();

-- ============================================================================
-- Table: policy_monitoring
-- Purpose: Track policy changes and data freshness monitoring
-- Key Design: Hash comparison detects policy changes, tracks verification history
-- ============================================================================
CREATE TABLE IF NOT EXISTS policy_monitoring (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign key to city_policies
  city_policy_id UUID NOT NULL REFERENCES city_policies(id) ON DELETE CASCADE,

  -- Monitoring metadata
  check_type monitoring_check_type NOT NULL,
  previous_hash TEXT,                          -- Hash of previous policy data
  new_hash TEXT,                               -- Hash of current policy data
  change_detected BOOLEAN NOT NULL DEFAULT false,

  -- Audit trail
  checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  notes TEXT,                                  -- Human notes on what changed

  -- Constraints
  CONSTRAINT policy_monitoring_hash_check CHECK (
    (previous_hash IS NULL AND new_hash IS NULL) OR
    (previous_hash IS NOT NULL AND new_hash IS NOT NULL)
  )
);

-- Indexes for monitoring queries
CREATE INDEX idx_policy_monitoring_city_policy_id ON policy_monitoring(city_policy_id);
CREATE INDEX idx_policy_monitoring_checked_at ON policy_monitoring(checked_at DESC);
CREATE INDEX idx_policy_monitoring_change_detected ON policy_monitoring(change_detected);
CREATE INDEX idx_policy_monitoring_check_type ON policy_monitoring(check_type);

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

-- Enable RLS on city_policies (read-only for authenticated users)
ALTER TABLE city_policies ENABLE ROW LEVEL SECURITY;

-- Policy: All authenticated users can read city policies
CREATE POLICY "Authenticated users can read city policies"
  ON city_policies FOR SELECT
  TO authenticated
  USING (true);

-- Policy: Only service role can insert/update/delete city policies
CREATE POLICY "Service role can manage city policies"
  ON city_policies FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Enable RLS on policy_monitoring (read-only for authenticated users)
ALTER TABLE policy_monitoring ENABLE ROW LEVEL SECURITY;

-- Policy: All authenticated users can read monitoring logs
CREATE POLICY "Authenticated users can read monitoring logs"
  ON policy_monitoring FOR SELECT
  TO authenticated
  USING (true);

-- Policy: Only service role can insert monitoring records
CREATE POLICY "Service role can insert monitoring logs"
  ON policy_monitoring FOR INSERT
  TO service_role
  WITH CHECK (true);

-- ============================================================================
-- Helper function: Generate policy hash
-- Purpose: Create a hash of policy data for change detection
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_policy_hash(policy_id UUID)
RETURNS TEXT AS $$
DECLARE
  policy_data TEXT;
BEGIN
  SELECT CONCAT(
    city_name, '|',
    province_code, '|',
    peak_price::TEXT, '|',
    valley_price::TEXT, '|',
    flat_price::TEXT, '|',
    peak_hours, '|',
    valley_hours, '|',
    subsidy_amount::TEXT, '|',
    effective_date::TEXT
  ) INTO policy_data
  FROM city_policies
  WHERE id = policy_id;

  RETURN encode(sha256(policy_data::bytea), 'hex');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- Comments for documentation
-- ============================================================================
COMMENT ON TABLE city_policies IS 'City-level electricity pricing policies for energy storage IRR calculations. CRITICAL: China pricing varies by CITY, not province.';
COMMENT ON COLUMN city_policies.city_name IS 'City name in Chinese (e.g., 深圳市). This is the KEY granularity level.';
COMMENT ON COLUMN city_policies.peak_price IS 'Peak-hour electricity price in 元/kWh (e.g., 1.2)';
COMMENT ON COLUMN city_policies.valley_price IS 'Valley-hour electricity price in 元/kWh (e.g., 0.4)';
COMMENT ON COLUMN city_policies.flat_price IS 'Flat-rate electricity price in 元/kWh (e.g., 0.8)';
COMMENT ON COLUMN city_policies.peak_hours IS 'Peak hours in 24h format (e.g., "10:00-12:00,14:00-19:00")';
COMMENT ON COLUMN city_policies.valley_hours IS 'Valley hours in 24h format (e.g., "00:00-08:00,19:00-24:00")';
COMMENT ON COLUMN city_policies.subsidy_amount IS 'Government subsidy in 元/kWh (0 if none)';
COMMENT ON COLUMN city_policies.confidence_score IS 'Data confidence 1-5: 1=unverified, 5=verified from official source';
COMMENT ON COLUMN city_policies.last_verified_at IS 'Last time a human verified this policy data. STALE if >90 days';

COMMENT ON TABLE policy_monitoring IS 'Audit trail of policy data freshness checks and changes';
COMMENT ON COLUMN policy_monitoring.previous_hash IS 'Hash of policy data before this check';
COMMENT ON COLUMN policy_monitoring.new_hash IS 'Hash of policy data after this check';
COMMENT ON COLUMN policy_monitoring.change_detected IS 'true if policy data changed since last check';
