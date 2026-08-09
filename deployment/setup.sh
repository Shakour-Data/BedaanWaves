#!/usr/bin/env bash
# deployment/setup.sh - Comprehensive deployment script for BedaanWaves

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Log function
log() {
    echo -e "${GREEN}[SETUP]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if a command exists
check_command() {
    command -v "$1" >/dev/null 2>&1 || {
        error "Command '$1' not found. Please install it first."
        exit 1
    }
}

# Check if a port is available
check_port() {
    local port=$1
    if lsof -i :"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        error "Port $port is already in use. Please stop the service using it and try again."
        return 1
    fi
    return 0
}

# Initialize deployment
init_deployment() {
    log "Initializing BedaanWaves deployment setup"
}

# Create required directories
setup_directories() {
    log "Creating required directories"
    mkdir -p data/archive logs models temp/uploads
    chmod 755 data/archive logs models temp/uploads
}

# Setup Python environment
setup_python() {
    log "Setting up Python environment"
    python -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -e . --upgrade
    log "Python environment setup complete"
}

# Setup Node.js environment
setup_node() {
    log "Setting up Node.js environment"
    check_command node
    check_command npm
    cd frontend
    npm install
    log "Node.js environment setup complete"
}

# Setup database
setup_database() {
    log "Setting up database"
    check_command psql
    createdb bedaanwaves --username=postgres --host=localhost || echo "Database might already exist"
    log "Database setup complete"
}

# Run migrations
run_migrations() {
    log "Running database migrations"
    cd backend
    alembic upgrade head
    log "Migrations completed successfully"
}

# Start development servers
start_dev_servers() {
    log "Starting development servers"
    cd backend
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    
    cd ../frontend
    npm run dev -- --port 3005 &
    
    log "Development servers started"
    log "Backend: http://localhost:8000"
    log "Frontend: http://localhost:3005"
}

# Setup production services
setup_production_services() {
    log "Setting up production services configuration"
    
    # Create systemd service files
    cat > /tmp/backend.service << 'EOF'
[Unit]
Description=BedaanWaves Backend Service
After=network.target

[Service]
User=<%= username %>
Group=<%= group %>
WorkingDirectory=/opt/bedaanwaves/backend
Environment=PATH=/opt/bedaanwaves/venv/bin:/opt/bedaanwaves/node_modules
ExecStart=/opt/bedaanwaves/venv/bin/uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    cat > /tmp/frontend.service << 'EOF'
[Unit]
Description=BedaanWaves Frontend Service
After=network.target

[Service]
User=<%= username %>
Group=<%= group %>
WorkingDirectory=/opt/bedaanwaves/frontend
ExecStart=/opt/bedaanwaves/node_modules/next/dist/bin/next start -p 3005
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    log "Systemd service files created in /tmp/"
    log "To install services: sudo cp *.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now backend.service frontend.service"
}

# Setup Docker (for any server deployment)
setup_docker() {
    log "Setting up Docker configuration"
    
    # Create Dockerfile
    cat > Dockerfile.backend << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start app
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000"]
EOF

    # Create Dockerfile for frontend
    cat > Dockerfile.frontend << 'EOF'
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy and build application
COPY . .
RUN npm run build

# Production image
FROM nginx:alpine
COPY --from=builder /app/.next/standalone /usr/share/nginx/html
COPY --from=builder /app/.next/static /usr/share/nginx/html/static

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
EOF

    # Create docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/bedaanwaves
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    depends_on:
      - db
      - redis

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:13
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=bedaanwaves
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  pgadmin:
    image: dpage/pgadmin4
    ports:
      - "5050:80"
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@bedaanwaves.com
      - PGADMIN_DEFAULT_PASSWORD=admin
    volumes:
      - pgadmin:/var/lib/pgadmin

volumes:
  pgdata:
  pgadmin:
EOF

    log "Docker configuration files created"
    log "To use Docker: docker-compose up --build -d"
}

# Setup Kubernetes (for deployment on any server)
setup_kubernetes() {
    log "Setting up Kubernetes deployment configuration"
    
    cat > bedaanwaves-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bedaanwaves-backend
  labels:
    app: bedaanwaves
    tier: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: bedaanwaves
      tier: backend
  template:
    metadata:
      labels:
        app: bedaanwaves
        tier: backend
    spec:
      containers:
      - name: backend
        image: bedaanwaves/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          value: "postgresql://postgres:password@postgres/bedaanwaves"
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        resources:
          limits:
            memory: "{{ .Values.resources.limits.memory }}"
            cpu: "{{ .Values.resources.limits.cpu }}"
          requests:
            memory: "{{ .Values.resources.requests.memory }}"
            cpu: "{{ .Values.resources.requests.cpu }}"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bedaanwaves-frontend
  labels:
    app: bedaanwaves
    tier: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: bedaanwaves
      tier: frontend
  template:
    metadata:
      labels:
        app: bedaanwaves
        tier: frontend
    spec:
      containers:
      - name: frontend
        image: bedaanwaves/frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: NEXT_PUBLIC_API_URL
          value: "http://backend:8000"
        env:
        - name: NEXT_PUBLIC_GRAPHQL_ENDPOINT
          value: "https://api.example.com/graphql"
---
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  type: ClusterIP
  ports:
    - port: 8000
      targetPort: 8000
  selector:
    app: bedaanwaves
    tier: backend
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  ports:
    - port: 80
      targetPort: 80
  selector:
    app: bedaanwaves
    tier: frontend
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  ports:
    - port: 8000
      targetPort: 8000
      protocol: TCP
  selector:
    app: bedaanwaves
    tier: backend
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
  spec:
    containers:
    - name: postgres
      image: postgres:13
      ports:
      - containerPort: 5432
      env:
      - name: POSTGRES_DB
        value: bedaanwaves
      - name: POSTGRES_USER
        value: postgres
      - name: POSTGRES_PASSWORD
        value: password
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  ports:
    - port: 5432
      targetPort: 5432
  selector:
    app: postgres
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
  spec:
    containers:
    - name: redis
      image: redis:7
      ports:
      - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  ports:
    - port: 6379
      targetPort: 6379
  selector:
    app: redis
EOF
    log "Kubernetes deployment files created"
    log "To deploy: kubectl apply -f bedaanwaves-deployment.yaml"
}

# Setup monitoring and logging
setup_monitoring() {
    log "Setting up monitoring and logging configuration"
    
    # Create Prometheus config
    cat > prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job: 'bedaanwaves'
    static_configs:
      - targets: ['localhost:9090']
  - job: 'node'
    static_configs:
      - targets: ['localhost:9100']
EOF

    # Create Grafana dashboard JSON
    cat > grafana-dashboard.json << 'EOF'
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "iteration": 1695345600000,
  "links": [],
  "panels": [
    {
      "datasource": "Prometheus",
      "description": "CPU Usage",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "legend": {
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "rate(process_cpu_seconds_total{mode=\"system\"}[1m]) * 100",
          "refId": "A"
        }
      ],
      "title": "CPU Usage",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "description": "Memory Usage",
      "fieldConfig": {
        "defaults": {
          "unit": "bytes"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "id": 2,
      "options": {
        "legend": {
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "1 - (machine_memory_Active_bytes{mode=\"available\"} / machine_memory_Active_bytes)",
          "refId": "A"
        }
      ],
      "title": "Memory Usage",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "description": "Request Latency",
      "fieldConfig": {
        "defaults": {
          "unit": "seconds"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 8
      },
      "id": 3,
      "options": {
        "legend": {
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{app=\"backend\"}[5m])) by (le))",
          "refId": "A"
        }
      ],
      "title": "95th Percentile Request Latency",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "description": "Error Rate",
      "fieldConfig": {
        "defaults": {
          "unit": "errors"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 8
      },
      "id": 4,
      "options": {
        "legend": {
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "sum(rate(http_requests_total{app=\"backend\",status_code=~\"5..\"}[1m]))",
          "refId": "A"
        }
      ],
      "title": "5xx Error Rate",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "description": "Active Connections",
      "fieldConfig": {
        "defaults": {
          "unit": "connections"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 24,
        "x": 0,
        "y": 16
      },
      "id": 5,
      "options": {
        "legend": {
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "sum(connection_count)",
          "refId": "A"
        }
      ],
      "title": "Active Connections",
      "type": "timeseries"
    }
  ],
  "schemaVersion": 38,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timezone": "browser",
  "title": "BedaanWaves Monitoring",
  "uid": "bedaanwaves-monitoring",
  "version": 1,
  "weekStart": ""
}
EOF
    log "Monitoring configurations created"
    log "Grafana dashboard: Import grafana-dashboard.json in Grafana"
}

# Checks for required tools
check_prerequisites() {
    log "Checking prerequisites"
    check_command docker
    check_command docker-compose
    check_command kubectl
    check_command helm
    check_command prometheus
    check_command grafana
    log "All prerequisites checked"
}

# Main setup function
main_setup() {
    init_deployment
    setup_directories
    setup_python
    setup_node
    setup_database
    run_migrations
    # setup_production_services
    setup_docker
    setup_kubernetes
    setup_monitoring
    log "All setup steps completed successfully"
    log "Check the README for deployment instructions"
    echo ""
    echo "==========================================="
    echo "DEPLOYMENT INSTRUCTIONS:"
    echo "1. For local development: ./venv/bin/uvicorn app.main:app --reload"
    echo "2. For production with Docker: docker-compose up --build -d"
    echo "3. For server deployment: Use the generated systemd services or Kubernetes manifests"
    echo "==========================================="
}

# Parse command line arguments
case "$1" in
    setup)
        main_setup
        ;;
    docker)
        setup_docker
        ;;
    kubernetes)
        setup_kubernetes
        ;;
    monitoring)
        setup_monitoring
        ;;
    *)
        warn "Usage: $0 {setup|docker|kubernetes|monitoring}"
        warn "For detailed setup guide, check README.md"
        ;;
esac