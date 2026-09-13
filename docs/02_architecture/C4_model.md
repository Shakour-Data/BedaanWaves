# BedaanWaves - C4 Model Architecture Documentation

## Level 1: System Context Diagram

```mermaid
C4Context
    title System Context Diagram for BedaanWaves Platform

    Person(user, "User", "Uses the platform for trading and market analysis")
    Person(admin, "Admin", "Manages platform operations")
    Person(mod, "Moderator", "Monitors platform health")

    System_Boundary(bedaanwaves, "BedaanWaves Platform") {
        System(api_gateway, "API Gateway", "Kong", "Central entry point for all API requests")
        System(order_service, "Order Service", "FastAPI", "Manages order lifecycle")
        System(payment_service, "Payment Service", "FastAPI", "Processes payments")
        System(inventory_service, "Inventory Service", "FastAPI", "Manages stock reservations")
        System(market_data_service, "Market Data Service", "Real-time market data ingestion")
        System(notification_service, "Notification Service", "Email, SMS, Push notifications")
        System(analytics_service, "Analytics Service", "Data analysis and reporting")
    }

    System_Ext(payments_gateway, "Payment Gateway", "External payment processor")
    System_Ext(email_service, "Email Service", "SendGrid/AWS SES")
    System_Ext(sms_service, "SMS Service", "Twilio/AWS SNS")
    System_Ext(push_service, "Push Service", "Firebase Cloud Messaging")
    System_Ext(nasdaq_api, "NASDAQ API", "External market data source")

    Rel(user, api_gateway, "Makes API requests", "HTTPS")
    Rel(admin, api_gateway, "Admin operations", "HTTPS")
    Rel(mod, api_gateway, "Moderation requests", "HTTPS")

    Rel(api_gateway, order_service, "Routes to", "REST")
    Rel(api_gateway, payment_service, "Routes to", "REST")
    Rel(api_gateway, inventory_service, "Routes to", "REST")
    Rel(api_gateway, market_data_service, "Routes to", "REST/WebSocket")
    Rel(api_gateway, notification_service, "Routes to", "REST")

    Rel(order_service, payment_service, "Coordinates via", "Kafka Events")
    Rel(order_service, inventory_service, "Coordinates via", "Kafka Events")
    Rel(order_service, notification_service, "Notifies via", "Kafka Events")

    Rel(payment_service, payments_gateway, "Processes via", "HTTPS")
    Rel(notification_service, email_service, "Sends emails", "SMTP/HTTPS")
    Rel(notification_service, sms_service, "Sends SMS", "HTTPS")
    Rel(notification_service, push_service, "Sends push", "HTTPS")
    Rel(market_data_service, nasdaq_api, "Ingests from", "HTTPS")
```

## Level 2: Container Diagram

```mermaid
C4Container
    title Container Diagram for BedaanWaves Platform

    Person(user, "User")

    System_Boundary(bedaanwaves, "BedaanWaves Platform") {
        Container(api_gateway, "API Gateway", "Kong + Lua", "Central API entry point")
        Container(order_api, "Order API", "FastAPI", "Order management")
        Container(payment_api, "Payment API", "FastAPI", "Payment processing")
        Container(inventory_api, "Inventory API", "FastAPI", "Stock management")
        Container(market_api, "Market Data API", "FastAPI", "Real-time market data")
        Container(notif_api, "Notification API", "FastAPI", "Notification dispatch")
        Container(analytics_api, "Analytics API", "FastAPI", "Data analysis")
        Container(bff, "BFF", "Next.js", "Backend for Frontend")
        Container(kafka, "Kafka", "Apache Kafka", "Event bus")
        Container(postgres, "PostgreSQL", "PostgreSQL 14", "Primary database")
        Container(redis, "Redis", "Redis 7", "Cache and session store")
        Container(jaeger, "Jaeger", "Jaeger", "Distributed tracing")
        Container(grafana, "Grafana", "Grafana", "Monitoring dashboards")
    }

    Rel(user, api_gateway, "HTTPS requests")
    Rel(api_gateway, order_api, "Routes to")
    Rel(api_gateway, payment_api, "Routes to")
    Rel(api_gateway, inventory_api, "Routes to")
    Rel(api_gateway, market_api, "Routes to")
    Rel(api_gateway, notif_api, "Routes to")
    Rel(api_gateway, analytics_api, "Routes to")
    Rel(api_gateway, bff, "Routes to")

    Rel(order_api, postgres, "Reads/Writes")
    Rel(payment_api, postgres, "Reads/Writes")
    Rel(inventory_api, postgres, "Reads/Writes")
    Rel(market_api, postgres, "Reads/Writes")
    Rel(notif_api, postgres, "Reads/Writes")
    Rel(analytics_api, postgres, "Reads")

    Rel(order_api, kafka, "Publishes/Consumes")
    Rel(payment_api, kafka, "Publishes/Consumes")
    Rel(inventory_api, kafka, "Publishes/Consumes")
    Rel(market_api, kafka, "Publishes/Consumes")
    Rel(notif_api, kafka, "Publishes/Consumes")

    Rel(order_api, redis, "Caches")
    Rel(market_api, redis, "Caches")

    Rel(api_gateway, jaeger, "Traces")
    Rel(order_api, jaeger, "Traces")
    Rel(payment_api, jaeger, "Traces")
    Rel(inventory_api, jaeger, "Traces")
    Rel(market_api, jaeger, "Traces")

    Rel(grafana, postgres, "Reads metrics")
    Rel(grafana, jaeger, "Reads traces")
```

## Level 3: Component Diagram - Order Service

```mermaid
C4Component
    title Container Diagram for Order Service

    Component(order_controller, "Order Controller", "FastAPI Controller", "Handles HTTP requests")
    Component(saga_orchestrator, "Saga Orchestrator", "Python", "Coordinates distributed transactions")
    Component(order_service, "Order Service", "Service Layer", "Business logic")
    Component(order_repo, "Order Repository", "SQLAlchemy", "Database access")
    Component(event_bus, "Event Bus", "Kafka/InMemory", "Event publishing")
    Component(circuit_breaker, "Circuit Breaker", "Resilience4j", "Fault isolation")
    Component(bulkhead, "Bulkhead", "Asyncio Semaphore", "Resource isolation")
    Component(tracing, "Tracing", "OpenTelemetry", "Distributed tracing")
    Component(cache, "Cache", "Redis", "Response caching")

    Rel(order_controller, order_service, "Calls")
    Rel(order_service, saga_orchestrator, "Initiates")
    Rel(order_service, order_repo, "Reads/Writes")
    Rel(order_service, event_bus, "Publishes events")
    Rel(order_service, circuit_breaker, "Protected by")
    Rel(order_service, bulkhead, "Protected by")
    Rel(order_service, tracing, "Traced by")
    Rel(order_service, cache, "Caches responses")
    Rel(order_repo, tracing, "Traced by")
    Rel(event_bus, tracing, "Traced by")
```

## Key Design Decisions

1. **Saga Pattern**: Orchestration-based saga for order processing
2. **Event-Driven Architecture**: Kafka for inter-service communication
3. **API Gateway**: Kong for centralized routing, auth, rate limiting
4. **Resilience**: Circuit Breaker + Bulkhead + Retry patterns
5. **Observability**: OpenTelemetry + Jaeger + Grafana
6. **Caching**: Redis for frequently accessed data
7. **Database per Service**: Each service owns its data