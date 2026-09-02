# BedaanWaves Database Documentation

## 1. Database Schema Overview

This document details the complete database schema for the BedaanWaves platform, including all tables, fields, relationships, and data flow mechanisms.

## 2. Core Entity Relationship Diagram

```
┌─────────────┐    ┌───────────────┐    ┌──────────────┐    ┌─────────────┐
│   USER      │    │ PREFERENCE    │    │ MARKET_DATA  │    │HISTORICAL_PRICES│
├─────────────┤    ├───────────────┤    ├──────────────┤    ├─────────────┤
│ user_id PK  │◄───┤ pref_id PK    │    │ data_id PK   │◄───┤ hp_id PK    │
│ email       │    │ user_id FK    │    │ symbol FK    │    │ symbol FK   │
│ name        │    │ market_settings│    │ timestamp    │    │ date        │
│ created_at  │    │ notification_settings││ close_price│    │ close_price │
│ last_login  │    │ theme         │    │ open_price   │    │             │
└─────────────┘    └───────────────┘    │ volume       │    └─────────────┘
                                         └──────────────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │  INDICE      │
                                        ├──────────────┤
                                        │ index_id PK  │
                                        │ symbol       │
                                        │ name         │
                                        │ market       │
                                        └──────────────┘
```

## 3. Detailed Table Specifications

### 3.1 USER Table
**Purpose**: Stores all registered user accounts with authentication and profile information

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| user_id | INT | PK, AI, NOT NULL | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email for login |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hashed password |
| first_name | VARCHAR(100) | NOT NULL | User's first name |
| last_name | VARCHAR(100) | NOT NULL | User's last name |
| phone | VARCHAR(20) | NULLABLE | Contact phone number |
| date_of_birth | DATE | NULLABLE | Date of birth |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | Last profile update |
| last_login | DATETIME | NULLABLE | Last successful login |
| is_active | BOOLEAN | DEFAULT TRUE | Account activation status |
| is_verified | BOOLEAN | DEFAULT FALSE | Email verification status |
| preferred_language | VARCHAR(10) | DEFAULT 'en' | UI language preference |
| timezone | VARCHAR(50) | DEFAULT 'America/New_York' | User timezone |

**Indexes**:
- Primary: user_id
- Unique: email
- Index: is_active, created_at

### 3.2 PREFERENCE Table
**Purpose**: Stores user-specific settings and preferences

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| pref_id | INT | PK, AI, NOT NULL | Preference record ID |
| user_id | INT | FK, NOT NULL | References USER.user_id |
| market_settings | JSON | NULLABLE | Country/indices selections |
| notification_settings | JSON | NULLABLE | Channel preferences |
| theme | VARCHAR(20) | DEFAULT 'dark' | UI theme setting |
| language | VARCHAR(10) | DEFAULT 'en' | Interface language |
| dashboard_layout | JSON | NULLABLE | Custom dashboard configuration |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Preference creation |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | Last preference update |

**Relationships**:
- Foreign Key: user_id → USER.user_id (CASCADE DELETE)

### 3.3 MARKET_DATA Table
**Purpose**: Real-time market data feed with timestamped price information

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| data_id | BIGINT | PK, AI, NOT NULL | Unique data point ID |
| symbol | VARCHAR(20) | FK, NOT NULL | Stock/crypto symbol |
| timestamp | DATETIME | NOT NULL | Data capture timestamp |
| open_price | DECIMAL(18,8) | NOT NULL | Opening price |
| high_price | DECIMAL(18,8) | NOT NULL | High price |
| low_price | DECIMAL(18,8) | NOT NULL | Low price |
| close_price | DECIMAL(18,8) | NOT NULL | Closing price |
| volume | BIGINT | NOT NULL | Trading volume |
| change_amount | DECIMAL(18,8) | NOT NULL | Price change from previous |
| change_percent | DECIMAL(8,4) | NOT NULL | Percentage change |
| market_cap | DECIMAL(20,2) | NULLABLE | Market capitalization |
| pe_ratio | DECIMAL(8,2) | NULLABLE | Price-to-earnings ratio |

**Relationships**:
- Foreign Key: symbol → STOCK.symbol (RESTRICT)
- Foreign Key: symbol → INDICE.symbol (for indices)

**Indexes**:
- Primary: data_id
- Composite: (symbol, timestamp DESC)
- Index: timestamp

### 3.4 HISTORICAL_PRICES Table
**Purpose**: Historical price data for technical analysis and backtesting

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| hp_id | BIGINT | PK, AI, NOT NULL | Historical price record ID |
| symbol | VARCHAR(20) | FK, NOT NULL | Security symbol |
| date | DATE | NOT NULL | Trading date |
| open_price | DECIMAL(18,8) | NOT NULL | Opening price |
| high_price | DECIMAL(18,8) | NOT NULL | High price |
| low_price | DECIMAL(18,8) | NOT NULL | Low price |
| close_price | DECIMAL(18,8) | NOT NULL | Closing price |
| adjusted_close | DECIMAL(18,8) | NULLABLE | Adjusted for splits/dividends |
| volume | BIGINT | NOT NULL | Trading volume |
| dividend_amount | DECIMAL(10,2) | DEFAULT 0 | Dividend paid (if any) |
| split_coefficient | DECIMAL(5,4) | DEFAULT 1.0 | Stock split multiplier |

**Relationships**:
- Foreign Key: symbol → STOCK.symbol (CASCADE DELETE)

**Indexes**:
- Primary: hp_id
- Composite: (symbol, date DESC)
- Unique: (symbol, date)

### 3.5 STOCK Table
**Purpose**: Master list of all tradable securities

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| symbol | VARCHAR(20) | PK, NOT NULL | Stock/crypto ticker symbol |
| name | VARCHAR(255) | NOT NULL | Full security name |
| security_type | ENUM('STOCK','ETF','CRYPTO','INDEX') | NOT NULL | Type of security |
| exchange | VARCHAR(50) | NOT NULL | Primary exchange |
| currency | VARCHAR(10) | NOT NULL | Trading currency |
| sector | VARCHAR(100) | NULLABLE | Industry sector |
| industry | VARCHAR(100) | NULLABLE | Industry sub-sector |
| market_cap | DECIMAL(20,2) | NULLABLE | Market capitalization |
| shares_outstanding | BIGINT | NULLABLE | Number of shares |
| is_active | BOOLEAN | DEFAULT TRUE | Trading status |
| listed_date | DATE | NULLABLE | Initial listing date |
| delisted_date | DATE | NULLABLE | Delisting date (if applicable) |
| description | TEXT | NULLABLE | Company/project description |
| website | VARCHAR(255) | NULLABLE | Official website |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Record creation |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | Last update |

**Indexes**:
- Primary: symbol
- Index: security_type, exchange
- Index: sector, industry

### 3.6 INDICE Table
**Purpose**: Market indices and benchmark tracking

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| symbol | VARCHAR(20) | PK, NOT NULL | Index symbol (e.g., SPX, VIX) |
| name | VARCHAR(255) | NOT NULL | Full index name |
| description | TEXT | NULLABLE | Index methodology description |
| calculation_method | VARCHAR(50) | NOT NULL | Price-weighted, market-cap weighted, etc. |
| base_date | DATE | NOT NULL | Index base date |
| base_value | DECIMAL(20,2) | NOT NULL | Index base value |
| divisor | DECIMAL(20,10) | NOT NULL | Current divisor |
| is_active | BOOLEAN | DEFAULT TRUE | Active calculation status |
| last_calculation | DATETIME | NULLABLE | Last calculation timestamp |
| components_count | INT | NULLABLE | Number of constituent securities |
| rebalance_frequency | VARCHAR(20) | DEFAULT 'Quarterly' | Rebalancing schedule |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Record creation |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | Last update |

**Indexes**:
- Primary: symbol
- Index: is_active

### 3.7 INDUSTRY Table
**Purpose**: Industry classification with performance metrics

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| industry_id | INT | PK, AI, NOT NULL | Unique industry identifier |
| name | VARCHAR(100) | NOT NULL | Industry name |
| sector | VARCHAR(100) | NOT NULL | Parent sector |
| description | TEXT | NULLABLE | Industry description |
| avg_pe_ratio | DECIMAL(8,2) | NULLABLE | Average P/E for industry |
| avg_dividend_yield | DECIMAL(6,4) | NULLABLE | Average dividend yield |
| growth_rate_1y | DECIMAL(6,4) | NULLABLE | 1-year growth rate |
| growth_rate_3y | DECIMAL(6,4) | NULLABLE | 3-year growth rate |
| volatility | DECIMAL(6,4) | NULLABLE | Historical volatility |
| market_cap_weight | DECIMAL(8,6) | NULLABLE | Weight in total market |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Record creation |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | Last update |

**Indexes**:
- Primary: industry_id
- Index: sector
- Index: is_active

### 3.8 SIGNAL Table
**Purpose**: Machine learning generated trading signals

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| signal_id | BIGINT | PK, AI, NOT NULL | Unique signal identifier |
| symbol | VARCHAR(20) | FK, NOT NULL | Related security symbol |
| signal_type | ENUM('BUY','SELL','HOLD','STRONG_BUY','STRONG_SELL') | NOT NULL | Signal recommendation |
| confidence_score | DECIMAL(5,4) | NOT NULL | Confidence level (0-1) |
| signal_strength | DECIMAL(5,4) | NOT NULL | Strength magnitude |
| model_name | VARCHAR(100) | NOT NULL | ML model that generated signal |
| model_version | VARCHAR(20) | NOT NULL | Version of the model |
| features_used | JSON | NULLABLE | Input features for prediction |
| timestamp | DATETIME | NOT NULL | Signal generation time |
| expiry_time | DATETIME | NULLABLE | When signal becomes invalid |
| price_at_signal | DECIMAL(18,8) | NOT NULL | Security price at signal time |
| target_price | DECIMAL(18,8) | NULLABLE | Suggested target price |
| stop_loss | DECIMAL(18,8) | NULLABLE | Suggested stop loss |
| expected_return | DECIMAL(8,4) | NULLABLE | Expected return percentage |
| risk_reward_ratio | DECIMAL(6,4) | NULLABLE | Risk/reward assessment |

**Relationships**:
- Foreign Key: symbol → STOCK.symbol (CASCADE DELETE)

**Indexes**:
- Primary: signal_id
- Composite: (symbol, timestamp DESC)
- Index: signal_type, confidence_score
- Index: model_name

### 3.9 ALERT Table
**Purpose**: User-triggered notifications based on signals or conditions

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| alert_id | BIGINT | PK, AI, NOT NULL | Unique alert identifier |
| user_id | INT | FK, NOT NULL | Associated user |
| alert_type | ENUM('PRICE','SIGNAL','VOLUME','TECHNICAL','NEWS') | NOT NULL | Type of alert |
| trigger_condition | JSON | NOT NULL | Conditions that trigger alert |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Alert creation |
| triggered_at | DATETIME | NULLABLE | Last time triggered |
| trigger_count | INT | DEFAULT 0 | Number of times triggered |
| notification_channels | JSON | NOT NULL | How to notify user |
| message_template | TEXT | NOT NULL | Notification message format |
| expires_at | DATETIME | NULLABLE | When alert expires |

**Relationships**:
- Foreign Key: user_id → USER.user_id (CASCADE DELETE)

**Indexes**:
- Primary: alert_id
- Index: user_id, is_active
- Index: triggered_at

### 3.10 FAVORITE Table
**Purpose**: User bookmarked securities for quick access

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| favorite_id | BIGINT | PK, AI, NOT NULL | Favorite record ID |
| user_id | INT | FK, NOT NULL | User who favorited |
| symbol | VARCHAR(20) | FK, NOT NULL | Favorited security |
| added_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | When favorited |
| notes | TEXT | NULLABLE | User notes about favorite |
| alert_enabled | BOOLEAN | DEFAULT FALSE | Enable alerts for favorite |

**Relationships**:
- Foreign Key: user_id → USER.user_id (CASCADE DELETE)
- Foreign Key: symbol → STOCK.symbol (CASCADE DELETE)

**Constraints**:
- UNIQUE: (user_id, symbol) - Prevent duplicate favorites

**Indexes**:
- Primary: favorite_id
- Unique: (user_id, symbol)
- Index: user_id

### 3.11 TRANSACTION_LOG Table
**Purpose**: Audit trail of all system activities

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| log_id | BIGINT | PK, AI, NOT NULL | Log entry ID |
| user_id | INT | FK, NULLABLE | Associated user (if applicable) |
| action_type | ENUM('LOGIN','LOGOUT','TRADE','SETTING_UPDATE','ALERT_CREATE') | NOT NULL | Type of action |
| resource_type | VARCHAR(50) | NOT NULL | Entity affected |
| resource_id | VARCHAR(100) | NULLABLE | Specific resource ID |
| description | TEXT | NULLABLE | Human-readable description |
| ip_address | VARCHAR(45) | NULLABLE | Source IP address |
| user_agent | TEXT | NULLABLE | Browser/client information |
| request_method | VARCHAR(10) | NULLABLE | HTTP method used |
| endpoint | VARCHAR(255) | NULLABLE | API endpoint accessed |
| status_code | INT | NULLABLE | HTTP status code |
| response_time_ms | INT | NULLABLE | Response time in milliseconds |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | When action occurred |

**Relationships**:
- Foreign Key: user_id → USER.user_id (SET NULL)

**Indexes**:
- Primary: log_id
- Index: user_id, created_at DESC
- Index: action_type, created_at DESC
- Index: created_at DESC

## 4. Relationship Summary

### 4.1 One-to-Many Relationships
- **USER → PREFERENCE**: One user can have one preference record (1:1 optional)
- **USER → ALERT**: One user can have many alerts
- **USER → FAVORITE**: One user can have many favorites
- **USER → TRANSACTION_LOG**: One user can have many log entries
- **STOCK → MARKET_DATA**: One stock can have many price data points
- **STOCK → HISTORICAL_PRICES**: One stock can have many historical prices
- **STOCK → SIGNAL**: One stock can have many signals
- **INDICE → MARKET_DATA**: One index can have many data points
- **INDUSTRY → STOCK**: One industry can have many stocks

### 4.2 Many-to-Many Relationships (Implicit via Junction Tables)
While most relationships are direct, some many-to-many associations exist through intermediary concepts:
- Users ↔ Industries: Via PREFERENCE.market_settings (JSON)
- Users ↔ Sectors: Via PREFERENCE.market_settings (JSON)
- Signals ↔ Indicators: Implicit through model features (JSON)

## 5. Data Flow Through System

### 5.1 Data Ingestion Pipeline
```
External Data Sources
        ↓
Data Ingestion Workers
        ↓
Validation & Cleaning Layer
        ↓
Market Data Processing Service
        ↓
Database Storage (MARKET_DATA table)
        ↓
Historical Archival Process (to HISTORICAL_PRICES)
```

### 5.2 Signal Generation Workflow
```
Market Data Ingestion
        ↓
Feature Engineering Service
        ↓
Model Inference Engine (ML Services)
        ↓
Signal Validation & Formatting
        ↓
Database Storage (SIGNAL table)
        ↓
Alert Trigger Evaluation
        ↓
User Notification Dispatch
```

### 5.3 User Interaction Flow
```
User Action (UI)
        ↓
Frontend State Update
        ↓
API Request to Backend
        ↓
Authentication & Authorization
        ↓
Business Logic Processing
        ↓
Database Query/Update
        ↓
Response Formatting
        ↓
API Response to Frontend
        ↓
UI State Update & Rendering
```

## 6. Indexing Strategy for Performance

### 6.1 Critical Query Patterns Optimized
1. **Latest Price Lookup**: `SELECT * FROM MARKET_DATA WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1`
   - Index: `(symbol, timestamp DESC)`

2. **Historical Data Range**: `SELECT * FROM HISTORICAL_PRICES WHERE symbol = ? AND date BETWEEN ? AND ? ORDER BY date`
   - Index: `(symbol, date)`

3. **User Preferences**: `SELECT * FROM PREFERENCE WHERE user_id = ?`
   - Index: `user_id`

4. **Active Signals**: `SELECT * FROM SIGNAL WHERE symbol = ? AND timestamp > ? ORDER BY timestamp DESC LIMIT 10`
   - Index: `(symbol, timestamp DESC)`

5. **User Alerts**: `SELECT * FROM ALERT WHERE user_id = ? AND is_active = TRUE ORDER BY created_at DESC`
   - Index: `(user_id, is_active)`

## 7. Constraints and Validation Rules

### 7.1 Data Integrity Constraints
- **Referential Integrity**: All foreign keys enforce relationships
- **Check Constraints**: Price values must be positive, percentages within valid ranges
- **Not Null Constraints**: Essential fields cannot be empty
- **Unique Constraints**: Prevent duplicate entries where inappropriate

### 7.2 Business Logic Validation
- **Price Validation**: High ≥ Low, Close between High/Low
- **Volume Validation**: Non-negative values
- **Percentage Validation**: Within [-100, +∞] range for changes
- **Timestamp Logic**: Newer records have later timestamps

## 8. Backup and Recovery Procedures

### 8.1 Backup Strategy
- **Full Backups**: Weekly complete database dump
- **Incremental Backups**: Daily transaction log backups
- **Point-in-Time Recovery**: Enabled for last 30 days
- **Geographic Replication**: Secondary region standby

### 8.2 Recovery Procedures
1. **Point-in-Time Recovery**: Restore to specific timestamp
2. **Table-Level Recovery**: Restore individual tables if needed
3. **Disaster Recovery**: Failover to secondary site within RTO/RPO

## 9. Maintenance Operations

### 9.1 Routine Tasks
- **Index Rebuilds**: Monthly during low-traffic periods
- **Statistics Update**: Weekly for query optimizer
- **Partition Maintenance**: Monthly for time-series tables
- **Archive Old Data**: Quarterly for data beyond retention period

### 9.2 Monitoring Metrics
- Query performance (slow query log)
- Connection pool utilization
- Disk space usage
- Replication lag
- Backup success rates

This comprehensive database documentation provides complete details for understanding, maintaining, and extending the data layer of the BedaanWaves platform. All tables, relationships, constraints, and data flows are thoroughly documented to ensure proper system operation and future development.