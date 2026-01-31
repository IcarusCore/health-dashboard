-- ==============================================
-- Personal Health Dashboard - Database Schema
-- ==============================================
-- This script initializes the database with TimescaleDB
-- and creates all necessary tables, indexes, and functions

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ==============================================
-- USERS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    units_system VARCHAR(20) DEFAULT 'metric', -- 'metric' or 'imperial'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- ==============================================
-- USER SETTINGS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Dashboard preferences
    default_date_range INTEGER DEFAULT 30, -- days
    show_weekly_summary BOOLEAN DEFAULT TRUE,
    show_monthly_summary BOOLEAN DEFAULT TRUE,
    
    -- Notification preferences
    email_notifications BOOLEAN DEFAULT TRUE,
    discord_notifications BOOLEAN DEFAULT FALSE,
    pushover_notifications BOOLEAN DEFAULT FALSE,
    
    -- Alert thresholds
    resting_hr_low_threshold INTEGER DEFAULT 40,
    resting_hr_high_threshold INTEGER DEFAULT 100,
    weight_change_alert_percent DECIMAL(5,2) DEFAULT 5.0,
    sleep_duration_min_hours DECIMAL(4,2) DEFAULT 6.0,
    
    -- Health goals
    daily_steps_goal INTEGER DEFAULT 10000,
    daily_calories_goal INTEGER DEFAULT 2000,
    daily_active_minutes_goal INTEGER DEFAULT 30,
    sleep_hours_goal DECIMAL(4,2) DEFAULT 8.0,
    weight_goal_kg DECIMAL(5,2),
    
    -- Theme preferences
    theme VARCHAR(20) DEFAULT 'dark', -- 'dark', 'light', 'system'
    accent_color VARCHAR(20) DEFAULT 'cyan',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- ==============================================
-- DATA SOURCES TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL, -- 'apple_health', 'manual', etc.
    source_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(20) DEFAULT 'never', -- 'never', 'syncing', 'success', 'error'
    sync_error_message TEXT,
    total_records_imported BIGINT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_data_sources_user ON data_sources(user_id);
CREATE INDEX idx_data_sources_type ON data_sources(source_type);

-- ==============================================
-- METRIC DEFINITIONS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS metric_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_key VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- 'vitals', 'activity', 'sleep', 'body', 'nutrition', 'custom'
    unit VARCHAR(50) NOT NULL,
    data_type VARCHAR(20) NOT NULL, -- 'numeric', 'duration', 'percentage', 'boolean'
    aggregation_method VARCHAR(20) DEFAULT 'avg', -- 'avg', 'sum', 'min', 'max', 'last'
    display_precision INTEGER DEFAULT 1,
    min_value DECIMAL(15,4),
    max_value DECIMAL(15,4),
    is_cumulative BOOLEAN DEFAULT FALSE,
    icon VARCHAR(50),
    color VARCHAR(20),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default metric definitions
INSERT INTO metric_definitions (metric_key, display_name, description, category, unit, data_type, aggregation_method, display_precision, min_value, max_value, icon, color, sort_order) VALUES
-- Vitals
('heart_rate', 'Heart Rate', 'Instantaneous heart rate', 'vitals', 'bpm', 'numeric', 'avg', 0, 30, 250, 'heart', 'red', 1),
('resting_heart_rate', 'Resting Heart Rate', 'Resting heart rate measurement', 'vitals', 'bpm', 'numeric', 'avg', 0, 30, 150, 'heart-pulse', 'red', 2),
('heart_rate_variability', 'Heart Rate Variability (HRV)', 'SDNN heart rate variability', 'vitals', 'ms', 'numeric', 'avg', 1, 0, 300, 'activity', 'blue', 3),
('blood_pressure_systolic', 'Blood Pressure (Systolic)', 'Systolic blood pressure', 'vitals', 'mmHg', 'numeric', 'avg', 0, 70, 250, 'gauge', 'orange', 4),
('blood_pressure_diastolic', 'Blood Pressure (Diastolic)', 'Diastolic blood pressure', 'vitals', 'mmHg', 'numeric', 'avg', 0, 40, 150, 'gauge', 'orange', 5),
('blood_oxygen', 'Blood Oxygen (SpO2)', 'Blood oxygen saturation', 'vitals', '%', 'percentage', 'avg', 1, 70, 100, 'droplet', 'blue', 6),
('respiratory_rate', 'Respiratory Rate', 'Breaths per minute', 'vitals', 'brpm', 'numeric', 'avg', 1, 5, 60, 'wind', 'teal', 7),
('body_temperature', 'Body Temperature', 'Body temperature measurement', 'vitals', '°C', 'numeric', 'avg', 1, 34, 42, 'thermometer', 'red', 8),

-- Activity
('steps', 'Steps', 'Daily step count', 'activity', 'steps', 'numeric', 'sum', 0, 0, NULL, 'footprints', 'green', 10),
('distance_walking', 'Walking Distance', 'Distance walked', 'activity', 'km', 'numeric', 'sum', 2, 0, NULL, 'map-pin', 'green', 11),
('distance_running', 'Running Distance', 'Distance ran', 'activity', 'km', 'numeric', 'sum', 2, 0, NULL, 'zap', 'green', 12),
('flights_climbed', 'Flights Climbed', 'Floors/flights climbed', 'activity', 'flights', 'numeric', 'sum', 0, 0, NULL, 'arrow-up', 'green', 13),
('active_energy', 'Active Calories', 'Calories burned through activity', 'activity', 'kcal', 'numeric', 'sum', 0, 0, NULL, 'flame', 'orange', 14),
('basal_energy', 'Basal Calories', 'Resting metabolic calories', 'activity', 'kcal', 'numeric', 'sum', 0, 0, NULL, 'battery', 'gray', 15),
('exercise_minutes', 'Exercise Minutes', 'Minutes of exercise', 'activity', 'min', 'duration', 'sum', 0, 0, NULL, 'timer', 'green', 16),
('stand_hours', 'Stand Hours', 'Hours with standing activity', 'activity', 'hours', 'numeric', 'sum', 0, 0, 24, 'user', 'blue', 17),
('vo2_max', 'VO2 Max', 'Cardio fitness level', 'activity', 'mL/kg/min', 'numeric', 'avg', 1, 10, 90, 'trending-up', 'blue', 18),

-- Sleep
('sleep_duration', 'Sleep Duration', 'Total time asleep', 'sleep', 'hours', 'duration', 'sum', 2, 0, 24, 'moon', 'indigo', 20),
('sleep_deep', 'Deep Sleep', 'Time in deep sleep', 'sleep', 'hours', 'duration', 'sum', 2, 0, 24, 'moon', 'indigo', 21),
('sleep_rem', 'REM Sleep', 'Time in REM sleep', 'sleep', 'hours', 'duration', 'sum', 2, 0, 24, 'eye', 'indigo', 22),
('sleep_light', 'Light Sleep', 'Time in light sleep', 'sleep', 'hours', 'duration', 'sum', 2, 0, 24, 'sun', 'indigo', 23),
('sleep_awake', 'Time Awake', 'Time awake during sleep', 'sleep', 'hours', 'duration', 'sum', 2, 0, 24, 'sun', 'gray', 24),
('sleep_efficiency', 'Sleep Efficiency', 'Percentage of time asleep in bed', 'sleep', '%', 'percentage', 'avg', 1, 0, 100, 'percent', 'indigo', 25),

-- Body
('weight', 'Weight', 'Body weight', 'body', 'kg', 'numeric', 'last', 1, 20, 500, 'scale', 'teal', 30),
('body_fat', 'Body Fat', 'Body fat percentage', 'body', '%', 'percentage', 'last', 1, 2, 70, 'percent', 'teal', 31),
('lean_body_mass', 'Lean Body Mass', 'Non-fat body mass', 'body', 'kg', 'numeric', 'last', 1, 10, 200, 'dumbbell', 'teal', 32),
('bmi', 'BMI', 'Body Mass Index', 'body', 'kg/m²', 'numeric', 'last', 1, 10, 60, 'calculator', 'teal', 33),
('waist_circumference', 'Waist Circumference', 'Waist measurement', 'body', 'cm', 'numeric', 'last', 1, 40, 200, 'ruler', 'teal', 34),

-- Nutrition
('water_intake', 'Water Intake', 'Water consumed', 'nutrition', 'L', 'numeric', 'sum', 2, 0, 20, 'droplet', 'blue', 40),
('caffeine', 'Caffeine', 'Caffeine consumed', 'nutrition', 'mg', 'numeric', 'sum', 0, 0, NULL, 'coffee', 'brown', 41),
('dietary_calories', 'Dietary Calories', 'Calories consumed', 'nutrition', 'kcal', 'numeric', 'sum', 0, 0, NULL, 'utensils', 'orange', 42),
('dietary_protein', 'Protein', 'Protein consumed', 'nutrition', 'g', 'numeric', 'sum', 1, 0, NULL, 'beef', 'red', 43),
('dietary_carbs', 'Carbohydrates', 'Carbohydrates consumed', 'nutrition', 'g', 'numeric', 'sum', 1, 0, NULL, 'wheat', 'amber', 44),
('dietary_fat', 'Fat', 'Fat consumed', 'nutrition', 'g', 'numeric', 'sum', 1, 0, NULL, 'egg', 'amber', 45),
('dietary_fiber', 'Fiber', 'Fiber consumed', 'nutrition', 'g', 'numeric', 'sum', 1, 0, NULL, 'leaf', 'green', 46),
('dietary_sugar', 'Sugar', 'Sugar consumed', 'nutrition', 'g', 'numeric', 'sum', 1, 0, NULL, 'candy', 'red', 47),
('alcohol', 'Alcohol', 'Alcohol consumed', 'nutrition', 'g', 'numeric', 'sum', 1, 0, NULL, 'wine', 'red', 48),

-- Mindfulness
('mindful_minutes', 'Mindful Minutes', 'Time spent in mindfulness', 'mindfulness', 'min', 'duration', 'sum', 0, 0, NULL, 'brain', 'teal', 50)
ON CONFLICT (metric_key) DO NOTHING;

-- ==============================================
-- MEASUREMENTS TABLE (Time Series - Hypertable)
-- ==============================================
CREATE TABLE IF NOT EXISTS measurements (
    id UUID DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_key VARCHAR(100) NOT NULL,
    source_id UUID REFERENCES data_sources(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    value DECIMAL(15,4) NOT NULL,
    unit VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (id, timestamp)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('measurements', 'timestamp', 
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Create indexes
CREATE INDEX idx_measurements_user_metric ON measurements(user_id, metric_key, timestamp DESC);
CREATE INDEX idx_measurements_timestamp ON measurements(timestamp DESC);
CREATE INDEX idx_measurements_source ON measurements(source_id);

-- ==============================================
-- WORKOUTS/ACTIVITIES TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS workouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_id UUID REFERENCES data_sources(id) ON DELETE SET NULL,
    workout_type VARCHAR(100) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds INTEGER NOT NULL,
    distance_meters DECIMAL(12,2),
    active_calories DECIMAL(10,2),
    total_calories DECIMAL(10,2),
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    elevation_gain_meters DECIMAL(10,2),
    avg_pace_seconds_per_km INTEGER,
    avg_speed_kmh DECIMAL(6,2),
    metadata JSONB DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_workouts_user ON workouts(user_id, start_time DESC);
CREATE INDEX idx_workouts_type ON workouts(workout_type);

-- ==============================================
-- SLEEP SESSIONS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS sleep_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_id UUID REFERENCES data_sources(id) ON DELETE SET NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    in_bed_start TIMESTAMP WITH TIME ZONE,
    in_bed_end TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER NOT NULL,
    time_asleep_seconds INTEGER,
    time_awake_seconds INTEGER,
    time_deep_seconds INTEGER,
    time_light_seconds INTEGER,
    time_rem_seconds INTEGER,
    sleep_efficiency DECIMAL(5,2),
    sleep_latency_seconds INTEGER,
    wake_count INTEGER,
    avg_heart_rate INTEGER,
    min_heart_rate INTEGER,
    avg_hrv DECIMAL(6,2),
    avg_respiratory_rate DECIMAL(5,2),
    avg_spo2 DECIMAL(5,2),
    metadata JSONB DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sleep_user ON sleep_sessions(user_id, start_time DESC);

-- ==============================================
-- DAILY SUMMARIES TABLE (Materialized for fast queries)
-- ==============================================
CREATE TABLE IF NOT EXISTS daily_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Activity
    steps INTEGER,
    distance_km DECIMAL(8,2),
    active_calories INTEGER,
    basal_calories INTEGER,
    total_calories INTEGER,
    exercise_minutes INTEGER,
    stand_hours INTEGER,
    flights_climbed INTEGER,
    
    -- Vitals
    resting_heart_rate INTEGER,
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    hrv_avg DECIMAL(6,2),
    blood_oxygen_avg DECIMAL(5,2),
    respiratory_rate_avg DECIMAL(5,2),
    
    -- Sleep (from previous night)
    sleep_duration_hours DECIMAL(5,2),
    sleep_efficiency DECIMAL(5,2),
    sleep_deep_hours DECIMAL(5,2),
    sleep_rem_hours DECIMAL(5,2),
    sleep_light_hours DECIMAL(5,2),
    
    -- Body
    weight_kg DECIMAL(5,2),
    body_fat_percent DECIMAL(5,2),
    
    -- Nutrition
    water_liters DECIMAL(5,2),
    caffeine_mg INTEGER,
    dietary_calories INTEGER,
    
    -- Goals progress
    steps_goal_percent DECIMAL(5,2),
    calories_goal_percent DECIMAL(5,2),
    exercise_goal_percent DECIMAL(5,2),
    sleep_goal_percent DECIMAL(5,2),
    
    -- Scores (computed)
    activity_score INTEGER,
    sleep_score INTEGER,
    recovery_score INTEGER,
    overall_score INTEGER,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, date)
);

CREATE INDEX idx_daily_summaries_user_date ON daily_summaries(user_id, date DESC);

-- ==============================================
-- HEALTH INSIGHTS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS health_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL, -- 'trend', 'anomaly', 'correlation', 'achievement', 'recommendation'
    category VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info', -- 'info', 'positive', 'warning', 'alert'
    metric_keys TEXT[], -- Array of related metrics
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_insights_user ON health_insights(user_id, created_at DESC);
CREATE INDEX idx_insights_type ON health_insights(insight_type);

-- ==============================================
-- ALERTS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL, -- 'threshold', 'anomaly', 'goal', 'reminder'
    metric_key VARCHAR(100),
    condition VARCHAR(50) NOT NULL, -- 'above', 'below', 'equals', 'change_percent'
    threshold_value DECIMAL(15,4),
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    cooldown_minutes INTEGER DEFAULT 60,
    notification_channels TEXT[] DEFAULT ARRAY['app'],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alerts_user ON alerts(user_id);

-- ==============================================
-- IMPORT HISTORY TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS import_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_id UUID REFERENCES data_sources(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    records_total INTEGER DEFAULT 0,
    records_imported INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_import_history_user ON import_history(user_id, created_at DESC);

-- ==============================================
-- CORRELATIONS TABLE (Pre-computed)
-- ==============================================
CREATE TABLE IF NOT EXISTS metric_correlations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_a VARCHAR(100) NOT NULL,
    metric_b VARCHAR(100) NOT NULL,
    correlation_coefficient DECIMAL(6,4) NOT NULL,
    p_value DECIMAL(10,8),
    sample_size INTEGER NOT NULL,
    lag_days INTEGER DEFAULT 0,
    date_range_start DATE NOT NULL,
    date_range_end DATE NOT NULL,
    is_significant BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, metric_a, metric_b, lag_days, date_range_start, date_range_end)
);

CREATE INDEX idx_correlations_user ON metric_correlations(user_id);

-- ==============================================
-- CUSTOM METRICS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS custom_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_key VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'custom',
    unit VARCHAR(50) NOT NULL,
    data_type VARCHAR(20) DEFAULT 'numeric',
    aggregation_method VARCHAR(20) DEFAULT 'avg',
    display_precision INTEGER DEFAULT 1,
    min_value DECIMAL(15,4),
    max_value DECIMAL(15,4),
    icon VARCHAR(50) DEFAULT 'chart-bar',
    color VARCHAR(20) DEFAULT 'gray',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, metric_key)
);

CREATE INDEX idx_custom_metrics_user ON custom_metrics(user_id);

-- ==============================================
-- FUNCTIONS & TRIGGERS
-- ==============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to relevant tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_sources_updated_at
    BEFORE UPDATE ON data_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_summaries_updated_at
    BEFORE UPDATE ON daily_summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alerts_updated_at
    BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================
-- CONTINUOUS AGGREGATES (TimescaleDB)
-- ==============================================

-- Hourly aggregates for heart rate
CREATE MATERIALIZED VIEW IF NOT EXISTS heart_rate_hourly
WITH (timescaledb.continuous) AS
SELECT
    user_id,
    time_bucket('1 hour', timestamp) AS bucket,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS sample_count
FROM measurements
WHERE metric_key = 'heart_rate'
GROUP BY user_id, bucket
WITH NO DATA;

-- Daily aggregates for all metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_daily
WITH (timescaledb.continuous) AS
SELECT
    user_id,
    metric_key,
    time_bucket('1 day', timestamp) AS bucket,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    SUM(value) AS sum_value,
    COUNT(*) AS sample_count
FROM measurements
GROUP BY user_id, metric_key, bucket
WITH NO DATA;

-- Refresh policies for continuous aggregates
SELECT add_continuous_aggregate_policy('heart_rate_hourly',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

SELECT add_continuous_aggregate_policy('metrics_daily',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ==============================================
-- DATA RETENTION POLICIES
-- ==============================================

-- Keep raw measurements for 2 years, then drop
SELECT add_retention_policy('measurements', INTERVAL '2 years', if_not_exists => TRUE);

-- ==============================================
-- HELPER VIEWS
-- ==============================================

-- View for latest measurements per metric
CREATE OR REPLACE VIEW latest_measurements AS
SELECT DISTINCT ON (user_id, metric_key)
    user_id,
    metric_key,
    timestamp,
    value,
    unit
FROM measurements
ORDER BY user_id, metric_key, timestamp DESC;

-- View for active alerts with metric details
CREATE OR REPLACE VIEW alerts_with_metrics AS
SELECT 
    a.*,
    md.display_name AS metric_display_name,
    md.unit AS metric_unit,
    md.category AS metric_category
FROM alerts a
LEFT JOIN metric_definitions md ON a.metric_key = md.metric_key;

-- ==============================================
-- INITIAL SETUP COMPLETE
-- ==============================================

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO healthuser;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO healthuser;

COMMENT ON DATABASE healthdashboard IS 'Personal Health Dashboard - Aggregate health data from multiple sources';
