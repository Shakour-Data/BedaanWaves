#!/bin/bash
set -euo pipefail

DB_ENDPOINT="${db_endpoint}"
DB_PASSWORD="${db_password}"
ENVIRONMENT="${environment}"

export DEBIAN_FRONTEND=noninteractive

# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y python3.11 python3.11-venv python3-pip postgresql-14 postgresql-contrib nodejs npm nginx ufw fail2ban unattended-upgrades curl wget git htop

# Create deployment user
useradd -m -s /bin/bash bedaanwaves || true
mkdir -p /opt/bedaanwaves
chown -R bedaanwaves:bedaanwaves /opt/bedaanwaves

# Configure firewall
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# Configure fail2ban
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
EOF

systemctl enable --now fail2ban

# Setup PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE bedaanwaves_db;" || true
sudo -u postgres psql -c "CREATE USER bedaanwaves WITH PASSWORD '${DB_PASSWORD}';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE bedaanwaves_db TO bedaanwaves;" || true

# Configure nginx
cat > /etc/nginx/sites-available/bedaanwaves << 'EOF'
upstream bedaanwaves_backend {
    server 127.0.0.1:3000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location /api/v1/ {
        proxy_pass http://bedaanwaves_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location / {
        proxy_pass http://127.0.0.1:3005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/bedaanwaves /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Install Node Exporter
useradd --no-create-home --shell /bin/false node_exporter || true
wget -q https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xzf node_exporter-1.7.0.linux-amd64.tar.gz
cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
chown node_exporter:node_exporter /usr/local/bin/node_exporter

cat > /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now node_exporter

# Install Prometheus
useradd --no-create-home --shell /bin/false prometheus || true
mkdir -p /opt/monitoring/prometheus/data
chown -R prometheus:prometheus /opt/monitoring

wget -q https://github.com/prometheus/prometheus/releases/download/v2.48.0/prometheus-2.48.0.linux-amd64.tar.gz
tar xzf prometheus-2.48.0.linux-amd64.tar.gz
cp prometheus-2.48.0.linux-amd64/prometheus /usr/local/bin/
cp prometheus-2.48.0.linux-amd64/promtool /usr/local/bin/

cat > /opt/monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
  - job_name: 'bedaanwaves-api'
    static_configs:
      - targets: ['localhost:3000']
    metrics_path: /metrics
    scrape_interval: 5s
EOF

chown -R prometheus:prometheus /opt/monitoring/prometheus

cat > /etc/systemd/system/prometheus.service << 'EOF'
[Unit]
Description=Prometheus
After=network.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file=/opt/monitoring/prometheus/prometheus.yml \
    --storage.tsdb.path=/opt/monitoring/prometheus/data \
    --storage.tsdb.retention.time=30d

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now prometheus

# Install Alertmanager
useradd --no-create-home --shell /bin/false alertmanager || true
mkdir -p /opt/monitoring/alertmanager/data
chown -R alertmanager:alertmanager /opt/monitoring/alertmanager

wget -q https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xzf alertmanager-0.26.0.linux-amd64.tar.gz
cp alertmanager-0.26.0.linux-amd64/alertmanager /usr/local/bin/
cp alertmanager-0.26.0.linux-amd64/amtool /usr/local/bin/

cat > /opt/monitoring/alertmanager/alertmanager.yml << 'EOF'
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'webhook'

receivers:
  - name: 'webhook'
    webhook_configs:
      - url: 'http://localhost:5001/'
        send_resolved: true
EOF

chown -R alertmanager:alertmanager /opt/monitoring/alertmanager

cat > /etc/systemd/system/alertmanager.service << 'EOF'
[Unit]
Description=Alertmanager
After=network.target

[Service]
User=alertmanager
Group=alertmanager
Type=simple
ExecStart=/usr/local/bin/alertmanager \
    --config.file=/opt/monitoring/alertmanager/alertmanager.yml \
    --storage.path=/opt/monitoring/alertmanager/data

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now alertmanager

# Install Grafana
apt-get install -y software-properties-common
add-apt-repository -y ppa:grafana/grafana
apt-get update
apt-get install -y grafana

systemctl enable --now grafana-server

# Install Filebeat
wget -q https://artifacts.elastic.co/GPG-KEY-elasticsearch
apt-key add GPG-KEY-elasticsearch
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" > /etc/apt/sources.list.d/elastic-8.x.list
apt-get update
apt-get install -y elasticsearch filebeat kibana

cat > /etc/filebeat/filebeat.yml << 'EOF'
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/nginx/*.log
      - /opt/bedaanwaves/*/logs/*.log

output.elasticsearch:
  hosts: ["localhost:9200"]
EOF

systemctl daemon-reload
systemctl enable --now filebeat
systemctl enable --now elasticsearch
systemctl enable --now kibana

echo "Bootstrap completed successfully"
