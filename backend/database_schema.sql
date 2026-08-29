
CREATE TABLE IF NOT EXISTS assets (
	id UUID NOT NULL, 
	symbol VARCHAR(50) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	asset_class VARCHAR(20) NOT NULL, 
	market VARCHAR(20) NOT NULL, 
	sector VARCHAR(100), 
	sub_sector VARCHAR(100), 
	industry VARCHAR(100), 
	country_code VARCHAR(2), 
	currency VARCHAR(3), 
	isin_code VARCHAR(12), 
	cusip_code VARCHAR(9), 
	active BOOLEAN, 
	listing_date TIMESTAMP WITHOUT TIME ZONE, 
	delisting_date TIMESTAMP WITHOUT TIME ZONE, 
	metadata JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS intl_price_candles (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	timeframe VARCHAR(10) NOT NULL, 
	open NUMERIC(20, 8) NOT NULL, 
	high NUMERIC(20, 8) NOT NULL, 
	low NUMERIC(20, 8) NOT NULL, 
	close NUMERIC(20, 8) NOT NULL, 
	volume BIGINT NOT NULL, 
	turnover NUMERIC(25, 2), 
	transactions INTEGER, 
	adjusted_close NUMERIC(20, 8), 
	split_ratio NUMERIC(10, 4), 
	source VARCHAR(20) NOT NULL, 
	data_quality VARCHAR(10), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_intl_price_candles_asset_ts_tf UNIQUE (asset_id, timestamp, timeframe), 
	CONSTRAINT chk_intl_price_candles_high CHECK (high >= open AND high >= close AND high >= low), 
	CONSTRAINT chk_intl_price_candles_low CHECK (low <= open AND low <= close AND low <= high), 
	CONSTRAINT chk_intl_price_candles_volume_non_negative CHECK (volume >= 0), 
	CONSTRAINT chk_intl_price_candles_price_non_negative CHECK (open >= 0 AND close >= 0), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS crypto_price_candles (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	timeframe VARCHAR(10) NOT NULL, 
	open NUMERIC(20, 8) NOT NULL, 
	high NUMERIC(20, 8) NOT NULL, 
	low NUMERIC(20, 8) NOT NULL, 
	close NUMERIC(20, 8) NOT NULL, 
	volume BIGINT NOT NULL, 
	turnover NUMERIC(25, 2), 
	transactions INTEGER, 
	adjusted_close NUMERIC(20, 8), 
	split_ratio NUMERIC(10, 4), 
	source VARCHAR(20) NOT NULL, 
	data_quality VARCHAR(10), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_crypto_price_candles_asset_ts_tf UNIQUE (asset_id, timestamp, timeframe), 
	CONSTRAINT chk_crypto_price_candles_high CHECK (high >= open AND high >= close AND high >= low), 
	CONSTRAINT chk_crypto_price_candles_low CHECK (low <= open AND low <= close AND low <= high), 
	CONSTRAINT chk_crypto_price_candles_volume_non_negative CHECK (volume >= 0), 
	CONSTRAINT chk_crypto_price_candles_price_non_negative CHECK (open >= 0 AND close >= 0), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS intl_order_book (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	snapshot_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	rank INTEGER NOT NULL, 
	bid_price NUMERIC(20, 8), 
	bid_volume BIGINT, 
	ask_price NUMERIC(20, 8), 
	ask_volume BIGINT, 
	source VARCHAR(20), 
	PRIMARY KEY (id), 
	CONSTRAINT uix_intl_order_book_snap_rank UNIQUE (asset_id, snapshot_time, rank), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS crypto_order_book (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	snapshot_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	rank INTEGER NOT NULL, 
	bid_price NUMERIC(20, 8), 
	bid_volume BIGINT, 
	ask_price NUMERIC(20, 8), 
	ask_volume BIGINT, 
	source VARCHAR(20), 
	PRIMARY KEY (id), 
	CONSTRAINT uix_crypto_order_book_snap_rank UNIQUE (asset_id, snapshot_time, rank), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS ml_signals (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	signal_type VARCHAR(20) NOT NULL, 
	confidence NUMERIC(5, 2) NOT NULL, 
	expected_return NUMERIC(8, 2), 
	expected_volatility NUMERIC(8, 2), 
	risk_score NUMERIC(5, 2), 
	reasoning TEXT, 
	technical_factors JSONB, 
	fundamental_factors JSONB, 
	sentiment_factors JSONB, 
	ml_model_version VARCHAR(50) NOT NULL, 
	model_name VARCHAR(100), 
	model_confidence NUMERIC(5, 2), 
	generated_at TIMESTAMP WITHOUT TIME ZONE, 
	valid_from TIMESTAMP WITHOUT TIME ZONE, 
	valid_until TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	is_active BOOLEAN, 
	actual_return NUMERIC(8, 2), 
	win_rate NUMERIC(5, 2), 
	PRIMARY KEY (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS portfolios (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	portfolio_type VARCHAR(20), 
	base_currency VARCHAR(3), 
	rebalance_frequency VARCHAR(20), 
	target_allocation JSONB, 
	is_public BOOLEAN, 
	public_token VARCHAR(50), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_portfolio_user_name UNIQUE (user_id, name)
)

;


CREATE TABLE IF NOT EXISTS positions (
	id UUID NOT NULL, 
	portfolio_id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	quantity NUMERIC(20, 8) NOT NULL, 
	entry_price NUMERIC(20, 8) NOT NULL, 
	entry_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	current_price NUMERIC(20, 8), 
	current_value NUMERIC(25, 2), 
	unrealized_pnl NUMERIC(25, 2), 
	unrealized_pnl_pct NUMERIC(8, 2), 
	stop_loss NUMERIC(20, 8), 
	take_profit NUMERIC(20, 8), 
	notes TEXT, 
	tags JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_portfolio_asset UNIQUE (portfolio_id, asset_id), 
	CONSTRAINT chk_positive_quantity CHECK (quantity > 0), 
	FOREIGN KEY(portfolio_id) REFERENCES portfolios (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS users (
	id UUID NOT NULL, 
	username VARCHAR(100) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	hashed_password VARCHAR(255) NOT NULL, 
	full_name VARCHAR(255), 
	is_active BOOLEAN, 
	is_admin BOOLEAN, 
	preferred_language VARCHAR(10), 
	theme VARCHAR(20), 
	notifications_enabled BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	last_login TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS refresh_tokens (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	token_hash VARCHAR(255) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	revoked BOOLEAN, 
	user_agent VARCHAR(512), 
	ip_address VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (token_hash)
)

;


CREATE TABLE IF NOT EXISTS audit_logs (
	id UUID NOT NULL, 
	user_id UUID, 
	action VARCHAR(100) NOT NULL, 
	entity VARCHAR(100), 
	entity_id VARCHAR(100), 
	details JSONB, 
	ip_address VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE IF NOT EXISTS alerts (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	asset_id UUID, 
	alert_type VARCHAR(20) NOT NULL, 
	condition JSONB NOT NULL, 
	threshold_value NUMERIC(20, 8), 
	threshold_direction VARCHAR(10), 
	notification_channel VARCHAR(20), 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	triggered_at TIMESTAMP WITHOUT TIME ZONE, 
	triggered_count INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS api_logs (
	id UUID NOT NULL, 
	user_id UUID, 
	endpoint VARCHAR(255) NOT NULL, 
	method VARCHAR(10) NOT NULL, 
	status_code INTEGER, 
	response_time_ms INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS watchlists (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	is_default BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS watchlist_items (
	id UUID NOT NULL, 
	watchlist_id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	note TEXT, 
	alert_threshold_pct NUMERIC(8, 4), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_watchlist_asset UNIQUE (watchlist_id, asset_id), 
	FOREIGN KEY(watchlist_id) REFERENCES watchlists (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS notifications (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	type VARCHAR(30) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	message TEXT NOT NULL, 
	channel VARCHAR(20), 
	priority VARCHAR(10), 
	read BOOLEAN, 
	metadata JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	read_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS user_preferences (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	key VARCHAR(100) NOT NULL, 
	value JSONB, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_user_pref UNIQUE (user_id, key)
)

;


CREATE TABLE IF NOT EXISTS market_sessions (
	id UUID NOT NULL, 
	market VARCHAR(20) NOT NULL, 
	session_date DATE NOT NULL, 
	is_open BOOLEAN, 
	open_time TIME WITHOUT TIME ZONE, 
	close_time TIME WITHOUT TIME ZONE, 
	note TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_market_session UNIQUE (market, session_date)
)

;


CREATE TABLE IF NOT EXISTS corporate_events (
	id UUID NOT NULL, 
	asset_id UUID, 
	event_type VARCHAR(30) NOT NULL, 
	event_date DATE NOT NULL, 
	details JSONB, 
	description TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS sectors (
	id UUID NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	parent_id UUID, 
	level INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (code), 
	FOREIGN KEY(parent_id) REFERENCES sectors (id)
)

;


CREATE TABLE IF NOT EXISTS currency_rates (
	id UUID NOT NULL, 
	base_currency VARCHAR(3) NOT NULL, 
	quote_currency VARCHAR(3) NOT NULL, 
	rate NUMERIC(20, 8) NOT NULL, 
	rate_date DATE NOT NULL, 
	source VARCHAR(20), 
	PRIMARY KEY (id), 
	CONSTRAINT uix_currency_rate UNIQUE (base_currency, quote_currency, rate_date)
)

;


CREATE TABLE IF NOT EXISTS macro_indicators (
	id UUID NOT NULL, 
	indicator_code VARCHAR(50) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	value NUMERIC(20, 6), 
	period VARCHAR(20), 
	unit VARCHAR(20), 
	source VARCHAR(50), 
	as_of DATE, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS financial_statements (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	market VARCHAR(20) NOT NULL, 
	period VARCHAR(20) NOT NULL, 
	statement_type VARCHAR(20) NOT NULL, 
	fiscal_year INTEGER, 
	data JSONB, 
	as_of DATE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_fin_stmt UNIQUE (asset_id, period, statement_type, market), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS fundamental_ratios (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	market VARCHAR(20) NOT NULL, 
	period VARCHAR(20) NOT NULL, 
	eps NUMERIC(20, 4), 
	pe NUMERIC(12, 2), 
	pb NUMERIC(12, 2), 
	dps NUMERIC(20, 4), 
	roe NUMERIC(8, 4), 
	profit_margin NUMERIC(8, 4), 
	market_cap NUMERIC(25, 2), 
	book_value NUMERIC(20, 4), 
	as_of DATE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_fund_ratio UNIQUE (asset_id, period, market), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS company_leadership (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	leadership_type VARCHAR(50) NOT NULL, 
	start_date DATE, 
	end_date DATE, 
	source VARCHAR(50), 
	fetched_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS news (
	id UUID NOT NULL, 
	source VARCHAR(100) NOT NULL, 
	title VARCHAR(512) NOT NULL, 
	body TEXT, 
	url VARCHAR(1024), 
	published_at TIMESTAMP WITHOUT TIME ZONE, 
	asset_id UUID, 
	language VARCHAR(5), 
	fetched_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS news_sentiment (
	id UUID NOT NULL, 
	news_id UUID NOT NULL, 
	asset_id UUID, 
	sentiment_label VARCHAR(20), 
	sentiment_score NUMERIC(5, 2), 
	model_version VARCHAR(50), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(news_id) REFERENCES news (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS news_summaries (
	id UUID NOT NULL, 
	news_id UUID NOT NULL, 
	summary_text TEXT, 
	model_version VARCHAR(50), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(news_id) REFERENCES news (id)
)

;


CREATE TABLE IF NOT EXISTS ml_models (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	version VARCHAR(50) NOT NULL, 
	model_type VARCHAR(50), 
	trained_at TIMESTAMP WITHOUT TIME ZONE, 
	metrics JSONB, 
	is_active BOOLEAN, 
	description TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_ml_model UNIQUE (name, version)
)

;


CREATE TABLE IF NOT EXISTS ml_predictions (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	model_id UUID, 
	model_version VARCHAR(50) NOT NULL, 
	horizon VARCHAR(20) NOT NULL, 
	predicted_value NUMERIC(20, 8), 
	lower_bound NUMERIC(20, 8), 
	upper_bound NUMERIC(20, 8), 
	confidence NUMERIC(5, 2), 
	as_of TIMESTAMP WITHOUT TIME ZONE, 
	target_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id), 
	FOREIGN KEY(model_id) REFERENCES ml_models (id)
)

;


CREATE TABLE IF NOT EXISTS anomalies (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	detected_at TIMESTAMP WITHOUT TIME ZONE, 
	score NUMERIC(10, 4), 
	anomaly_type VARCHAR(50), 
	description TEXT, 
	severity VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS screening_results (
	id UUID NOT NULL, 
	user_id UUID, 
	name VARCHAR(255) NOT NULL, 
	criteria JSONB, 
	universe JSONB, 
	result_count INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE IF NOT EXISTS raw_market_data (
	id UUID NOT NULL, 
	asset_id UUID, 
	raw_symbol VARCHAR(50) NOT NULL, 
	market VARCHAR(20) NOT NULL, 
	exchange VARCHAR(50), 
	data_type VARCHAR(30) NOT NULL, 
	raw_payload JSONB NOT NULL, 
	price NUMERIC(20, 8), 
	volume NUMERIC(25, 2), 
	quote_volume NUMERIC(25, 2), 
	source_timestamp TIMESTAMP WITH TIME ZONE NOT NULL, 
	ingested_at TIMESTAMP WITH TIME ZONE, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	ingestion_id VARCHAR(100), 
	data_quality VARCHAR(10), 
	PRIMARY KEY (id), 
	CONSTRAINT uix_raw_market UNIQUE (raw_symbol, market, exchange, data_type, source_timestamp), 
	CONSTRAINT chk_raw_data_quality CHECK (data_quality IN ('RAW', 'VALIDATED')), 
	CONSTRAINT chk_raw_market_type CHECK (market IN ('CRYPTO', 'INTL', 'TSE')), 
	CONSTRAINT chk_raw_volume_non_negative CHECK (volume >= 0), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS market_data_snapshots (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	snapshot_time TIMESTAMP WITH TIME ZONE NOT NULL, 
	interval VARCHAR(10) NOT NULL, 
	open NUMERIC(20, 8), 
	high NUMERIC(20, 8), 
	low NUMERIC(20, 8), 
	close NUMERIC(20, 8), 
	volume NUMERIC(25, 2), 
	turnover NUMERIC(25, 2), 
	rsi NUMERIC(8, 4), 
	macd NUMERIC(20, 8), 
	macd_signal NUMERIC(20, 8), 
	macd_histogram NUMERIC(20, 8), 
	bb_upper NUMERIC(20, 8), 
	bb_middle NUMERIC(20, 8), 
	bb_lower NUMERIC(20, 8), 
	atr NUMERIC(20, 8), 
	ma_7 NUMERIC(20, 8), 
	ma_14 NUMERIC(20, 8), 
	ma_30 NUMERIC(20, 8), 
	volatility NUMERIC(20, 8), 
	volume_ma_7 NUMERIC(25, 2), 
	volume_ratio NUMERIC(8, 4), 
	features JSONB DEFAULT '{}'::jsonb, 
	source VARCHAR(20), 
	is_fresh BOOLEAN, 
	freshness_score NUMERIC(5, 2), 
	created_at TIMESTAMP WITH TIME ZONE, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_snapshot UNIQUE (asset_id, snapshot_time, interval), 
	CONSTRAINT chk_freshness_score_range CHECK (freshness_score >= 0 AND freshness_score <= 100), 
	CONSTRAINT chk_snapshot_high_low CHECK (high >= low), 
	CONSTRAINT chk_snapshot_volume_non_negative CHECK (volume >= 0), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS crypto_ml_signals (
	id UUID NOT NULL, 
	asset_id UUID NOT NULL, 
	snapshot_id UUID, 
	signal_type VARCHAR(20) NOT NULL, 
	confidence NUMERIC(5, 2) NOT NULL, 
	expected_return NUMERIC(8, 2), 
	expected_volatility NUMERIC(8, 2), 
	risk_score NUMERIC(5, 2), 
	model_name VARCHAR(100), 
	model_version VARCHAR(50), 
	features_used JSONB, 
	technical_indicators JSONB, 
	generated_at TIMESTAMP WITH TIME ZONE, 
	valid_from TIMESTAMP WITH TIME ZONE, 
	valid_until TIMESTAMP WITH TIME ZONE NOT NULL, 
	is_active BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id), 
	FOREIGN KEY(snapshot_id) REFERENCES market_data_snapshots (id)
)

;


CREATE TABLE IF NOT EXISTS raw_performance_scores (
	id UUID NOT NULL, 
	captured_at TIMESTAMP WITH TIME ZONE, 
	asset_id UUID, 
	market VARCHAR(20) NOT NULL, 
	exchange VARCHAR(50) NOT NULL, 
	context JSONB, 
	dimension_scores JSONB NOT NULL, 
	sub_dimension_scores JSONB NOT NULL, 
	aspect_scores JSONB NOT NULL, 
	sub_aspect_scores JSONB NOT NULL, 
	target_return NUMERIC(20, 8), 
	target_volatility NUMERIC(10, 6), 
	target_sharpe NUMERIC(8, 4), 
	target_price_change NUMERIC(10, 6), 
	target_volume_change NUMERIC(10, 4), 
	target_bitcoin_correlation NUMERIC(8, 6), 
	target_market_sentiment NUMERIC(5, 2), 
	data_quality VARCHAR(20), 
	validation_status VARCHAR(20), 
	validation_notes TEXT, 
	is_processed BOOLEAN, 
	processing_errors JSONB, 
	ingestion_id VARCHAR(100), 
	source_system VARCHAR(50), 
	PRIMARY KEY (id), 
	CONSTRAINT uix_raw_perf_unique UNIQUE (asset_id, captured_at, market) DEFERRABLE, 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS processed_feature_data (
	id UUID NOT NULL, 
	raw_data_id UUID NOT NULL, 
	asset_id UUID, 
	processed_at TIMESTAMP WITH TIME ZONE, 
	market VARCHAR(20) NOT NULL, 
	exchange VARCHAR(50) NOT NULL, 
	feature_vector NUMERIC(20, 8)[] NOT NULL, 
	dimension_features JSONB NOT NULL, 
	sub_dimension_features JSONB NOT NULL, 
	aspect_features JSONB NOT NULL, 
	sub_aspect_features JSONB NOT NULL, 
	target_values JSONB NOT NULL, 
	features_used JSONB, 
	preprocessing_steps JSONB, 
	normalization_params JSONB, 
	is_valid BOOLEAN, 
	quality_score NUMERIC(5, 2), 
	validation_errors JSONB, 
	model_version VARCHAR(50), 
	feature_schema_version VARCHAR(20), 
	PRIMARY KEY (id), 
	CONSTRAINT uix_processed_unique UNIQUE (raw_data_id, processed_at), 
	FOREIGN KEY(raw_data_id) REFERENCES raw_performance_scores (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS coefficient_adjustments (
	id UUID NOT NULL, 
	adjustment_cycle TIMESTAMP WITH TIME ZONE, 
	asset_id UUID, 
	level VARCHAR(20) NOT NULL, 
	feature_key VARCHAR(100) NOT NULL, 
	old_weight NUMERIC(8, 6) NOT NULL, 
	new_weight NUMERIC(8, 6) NOT NULL, 
	weight_change NUMERIC(8, 6), 
	adjustment_code VARCHAR(50) NOT NULL, 
	adjustment_reason TEXT, 
	confidence_score NUMERIC(5, 2), 
	model_version VARCHAR(50), 
	training_samples INTEGER, 
	performance_improvement NUMERIC(8, 6), 
	created_by VARCHAR(50), 
	implementation_version VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS coefficient_history (
	id UUID NOT NULL, 
	effective_at TIMESTAMP WITH TIME ZONE, 
	asset_id UUID, 
	market VARCHAR(20) NOT NULL, 
	exchange VARCHAR(50) NOT NULL, 
	coefficients JSONB NOT NULL, 
	source VARCHAR(50), 
	model_version VARCHAR(50), 
	is_valid BOOLEAN, 
	validation_notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE IF NOT EXISTS user_market_settings (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	countries JSONB, 
	indices JSONB, 
	industries JSONB, 
	regions JSONB, 
	exchanges JSONB, 
	currencies JSONB, 
	last_validated TIMESTAMP WITHOUT TIME ZONE, 
	validation_hash VARCHAR(64), 
	is_default BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_user_market_settings UNIQUE (user_id)
)

;


CREATE TABLE IF NOT EXISTS user_market_configs (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	config_name VARCHAR(100) NOT NULL, 
	country VARCHAR(50), 
	country_indices JSONB, 
	selected_industries JSONB, 
	included_symbols JSONB, 
	price_range JSONB, 
	volume_range JSONB, 
	change_filter JSONB, 
	market_cap_filter JSONB, 
	last_calc TIMESTAMP WITHOUT TIME ZONE, 
	is_default BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_user_market_config UNIQUE (user_id, config_name)
)

;


CREATE TABLE IF NOT EXISTS user_crypto_settings (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	selected_cryptos JSONB, 
	excluded_cryptos JSONB, 
	custom_watchlist JSONB, 
	exchange_source VARCHAR(50), 
	min_volume_24h NUMERIC(20, 8), 
	min_market_cap NUMERIC(20, 8), 
	price_change_filter VARCHAR(20), 
	last_validated TIMESTAMP WITHOUT TIME ZONE, 
	validation_hash VARCHAR(64), 
	is_default BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_user_crypto_settings UNIQUE (user_id)
)

;


CREATE TABLE IF NOT EXISTS user_crypto_configs (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	config_name VARCHAR(100) NOT NULL, 
	included_symbols JSONB, 
	excluded_symbols JSONB, 
	exchange_source VARCHAR(50), 
	min_volume_24h NUMERIC(20, 8), 
	min_market_cap NUMERIC(20, 8), 
	price_range JSONB, 
	change_filter JSONB, 
	last_calc TIMESTAMP WITHOUT TIME ZONE, 
	is_default BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_user_crypto_config UNIQUE (user_id, config_name)
)

;


CREATE TABLE IF NOT EXISTS user_scoring_results (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	source VARCHAR(100) NOT NULL, 
	symbol VARCHAR(50) NOT NULL, 
	country VARCHAR(50), 
	industry VARCHAR(50), 
	exchange VARCHAR(50), 
	score NUMERIC(10, 6), 
	rank INTEGER, 
	data_date DATE NOT NULL, 
	criteria_scores JSONB, 
	user_preferences JSONB, 
	recommendations JSONB, 
	description JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_user_scoring UNIQUE (user_id, symbol, data_date)
)

;


CREATE TABLE IF NOT EXISTS validation_records (
	id UUID NOT NULL, 
	source_id VARCHAR(100) NOT NULL, 
	validation_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	validation_type VARCHAR(50) NOT NULL, 
	is_valid BOOLEAN NOT NULL, 
	details JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS source_authenticity (
	id UUID NOT NULL, 
	source_name VARCHAR(100) NOT NULL, 
	authenticity_score NUMERIC(5, 2) NOT NULL, 
	verification_status VARCHAR(50) NOT NULL, 
	verification_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS cross_source_consistency (
	id UUID NOT NULL, 
	source_a_id VARCHAR(100) NOT NULL, 
	source_b_id VARCHAR(100) NOT NULL, 
	data_type VARCHAR(50) NOT NULL, 
	consistency_metric NUMERIC(5, 2) NOT NULL, 
	validation_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS data_sources (
	id UUID NOT NULL, 
	source_name VARCHAR(100) NOT NULL, 
	source_type VARCHAR(50) NOT NULL, 
	base_url VARCHAR(500), 
	api_key_required BOOLEAN, 
	auth_token VARCHAR(500), 
	data_format VARCHAR(50), 
	last_verification TIMESTAMP WITHOUT TIME ZONE, 
	verification_count INTEGER, 
	is_active BOOLEAN, 
	info JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (source_name)
)

;


CREATE TABLE IF NOT EXISTS historical_data_import_log (
	id UUID NOT NULL, 
	import_batch_id VARCHAR(100) NOT NULL, 
	source_id UUID, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	records_imported INTEGER, 
	records_updated INTEGER, 
	validation_results JSONB, 
	import_status VARCHAR(50), 
	error_message TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_id) REFERENCES data_sources (id)
)

;


CREATE TABLE IF NOT EXISTS cryptocurrencies (
	id UUID NOT NULL, 
	symbol VARCHAR(20) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	exchange VARCHAR(50), 
	market_cap NUMERIC(20, 8), 
	volume_24h NUMERIC(20, 8), 
	price_usd NUMERIC(20, 8), 
	price_change_24h NUMERIC(10, 6), 
	price_change_7d NUMERIC(10, 6), 
	market_cap_rank INTEGER, 
	circulating_supply NUMERIC(20, 8), 
	max_supply NUMERIC(20, 8), 
	last_updated TIMESTAMP WITHOUT TIME ZONE, 
	extra_data JSONB, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS countries (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	iso_code VARCHAR(10) NOT NULL, 
	stock_exchange VARCHAR(100), 
	currency_code VARCHAR(10), 
	timezone VARCHAR(50), 
	is_active BOOLEAN, 
	extra_data JSONB, 
	last_verified TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (iso_code)
)

;


CREATE TABLE IF NOT EXISTS industries (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	sector VARCHAR(100), 
	etf_ticker VARCHAR(20), 
	is_active BOOLEAN, 
	extra_data JSONB, 
	last_verified TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;


CREATE TABLE IF NOT EXISTS market_indices (
	id UUID NOT NULL, 
	symbol VARCHAR(50) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	exchange VARCHAR(100), 
	country VARCHAR(50), 
	base_value NUMERIC(20, 8), 
	current_value NUMERIC(20, 8), 
	change_percent NUMERIC(10, 6), 
	volume NUMERIC(18, 8), 
	last_updated TIMESTAMP WITHOUT TIME ZONE, 
	extra_data JSONB, 
	is_active BOOLEAN, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS user_favorites (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	source VARCHAR(100) NOT NULL, 
	symbol VARCHAR(50) NOT NULL, 
	category VARCHAR(50), 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_user_favorite UNIQUE (user_id, source, symbol)
)

;


CREATE TABLE IF NOT EXISTS user_alerts (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	symbol VARCHAR(50) NOT NULL, 
	alert_type VARCHAR(50) NOT NULL, 
	alert_condition JSONB NOT NULL, 
	is_active BOOLEAN, 
	notify_method JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	last_triggered TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS symbol_data (
	symbol_id SERIAL NOT NULL, 
	symbol VARCHAR(10) NOT NULL, 
	security_name TEXT NOT NULL, 
	exchange VARCHAR(50) NOT NULL, 
	country_code VARCHAR(2) NOT NULL, 
	index_code VARCHAR(20), 
	industry_code VARCHAR(100), 
	market_type VARCHAR(20) NOT NULL, 
	active_status BOOLEAN, 
	status_reason VARCHAR(200), 
	listing_date DATE, 
	delisting_date DATE, 
	round_lot_size VARCHAR(50), 
	market_category VARCHAR(1), 
	financial_status VARCHAR(50), 
	etf_flag BOOLEAN, 
	next_shares BOOLEAN, 
	is_test_issue BOOLEAN, 
	security_type VARCHAR(50), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (symbol_id)
)

;