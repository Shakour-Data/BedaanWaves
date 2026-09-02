# BedaanWaves - Executive Overview

## Project Summary

BedaanWaves is a unified capital market analysis platform that consolidates 4 legacy projects (Bedaan4D-ML, Bedaan6D-project, Bedaan_4D_AI, .kilo) into a single, optimized system. The platform provides comprehensive market analysis covering stocks and ETFs with advanced ML/AI capabilities.

**Status**: Production Ready (100% Implementation Complete)
**Last Updated**: August 12, 2026
**Framework**: FastAPI + SQLAlchemy 2.0 + PostgreSQL
**Deployment**: Direct on local machine (No Docker policy)

## Key Features

- **Unified Platform**: Single codebase replacing 5 legacy systems
- **Multi-Asset Support**: Domestic (TSE) and International markets
- **Advanced Analytics**: 6D scoring system with 305-node hierarchy
- **ML/AI Capabilities**: Price prediction, pattern recognition, anomaly detection
- **NLP Integration**: Persian sentiment analysis, news summarization, document extraction
- **User Management**: Authentication, authorization, profiles, watchlists
- **Real-time Data**: WebSocket support for live market data
- **Comprehensive API**: 50+ endpoints across 16 routers with full documentation
- **Extensible Architecture**: 9-tier service design with dependency injection

## System Architecture

BedaanWaves follows a layered 9-tier architecture:
1. **Tier 1**: Core Services (DI, Config, Logging, Cache, DB, Health)
2. **Tier 2**: Data Services (API Clients, Data Management)
3. **Tier 3**: Analysis Services (Scoring, Technical, Fundamental)
4. **Tier 4**: ML Services (Prediction, Pattern Recognition, etc.)
5. **Tier 5**: NLP Services (Sentiment, Summarization, Chatbot)
6. **Tier 6**: User Services (Auth, Profile, Watchlist)
7. **Tier 7**: Specialized Services (Sector, Screening, Comparison)

9. **Tier 9**: System Services (Scheduler, Metrics, Queue)

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2
- **Database**: PostgreSQL (local, required)
- **Cache**: Redis (optional, with memory fallback)
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Testing**: Pytest with coverage reporting
- **Monitoring**: Built-in metrics collection and health checks
- **Security**: JWT authentication, RBAC authorization, input validation

## Getting Started

1. **Prerequisites**: Python 3.11+, PostgreSQL 14+, Redis (optional)
2. **Setup**: 
   ```bash
   # Clone repository
   git clone <repository-url>
   cd BedaanWaves
   
   # Backend setup
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   pip install -e .
   
   # Environment configuration
   cp .env.example .env
   # Edit .env with your database credentials
   
   # Database initialization
   createdb bedaanwaves
   alembic upgrade head
   
   # Start application
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
3. **Access**: 
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Documentation Structure

This documentation is organized into 20 comprehensive files:
01. Executive Overview (this file)
02. Architecture & Design
03. Technology Stack
04. Service Catalog
05. API Documentation
06. Database Schema
07. Configuration Guide
08-16. Service Tiers (Core through System)
17. Development Setup
18. Deployment Guide
19. Testing & Quality
20. Operations & Maintenance

## Support & Resources

- **API Documentation**: Interactive Swagger UI at `/docs`
- **Source Code**: Well-organized with type hints and docstrings
- **Configuration**: Centralized via ConfigService (100+ settings)
- **Monitoring**: Health endpoints and metrics collection
- **Community**: Issue tracking and contribution guidelines available

---
*Last Updated: 2026-08-17*
*Status: Production Ready*