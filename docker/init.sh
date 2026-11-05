#!/bin/bash
set -e

echo "=== Frappe CRM Container Initialization ==="

# 1. Ensure MariaDB client does not enforce TLS over TCP when connecting to MariaDB 10.8 server
if [ ! -f ~/.my.cnf ]; then
    printf '[client]\nssl=0\nskip-ssl\n' > ~/.my.cnf 2>/dev/null || true
fi

# 2. Wait for MariaDB & Redis services
echo "Waiting for MariaDB service (mariadb:3306)..."
while ! python3 -c "import socket; s = socket.socket(); s.connect(('mariadb', 3306)); s.close()" 2>/dev/null; do
    sleep 2
done
echo "MariaDB is ready."

echo "Waiting for Redis service (redis:6379)..."
while ! python3 -c "import socket; s = socket.socket(); s.connect(('redis', 6379)); s.close()" 2>/dev/null; do
    sleep 2
done
echo "Redis is ready."

# 3. Create Frappe Bench if it does not exist (must be Frappe develop / v16 for frappe.automation_engine)
BENCH_DIR="/home/frappe/frappe-bench"
if [ -d "$BENCH_DIR/apps/frappe" ] && [ ! -d "$BENCH_DIR/apps/frappe/frappe/automation_engine" ]; then
    echo "Existing bench lacks frappe.automation_engine (was v15). Re-initializing with Frappe develop (v16)..."
    rm -rf "$BENCH_DIR"
fi

if [ ! -f "$BENCH_DIR/env/bin/frappe" ]; then
    echo "Creating new Frappe bench (develop) at $BENCH_DIR..."
    cd /home/frappe
    bench init --skip-redis-config-generation frappe-bench --version develop
fi

cd "$BENCH_DIR"

# 4. Configure bench container hosts
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Configure Procfile:
# - Remove redis processes (handled by dedicated redis container)
# - Remove watch processes
# - Ensure web server binds to 0.0.0.0:8000 so it is accessible from host machine
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile
sed -i 's/bench serve --port 8000/bench serve --port 8000 --host 0.0.0.0/' ./Procfile
if ! grep -q "0.0.0.0" ./Procfile; then
    sed -i 's/bench serve/bench serve --host 0.0.0.0/' ./Procfile
fi

# 5. Install required dependency app: WhatsApp
if [ ! -d "apps/whatsapp" ]; then
    echo "Getting WhatsApp app..."
    bench get-app whatsapp
fi

# 6. Install the local CRM app from /workspace
if [ ! -e "apps/crm" ]; then
    echo "Linking local CRM repository from /workspace into apps/crm..."
    ln -sfn /workspace apps/crm
fi

echo "Installing local CRM app in editable mode..."
./env/bin/pip install -e apps/crm

# Ensure apps.txt has valid line breaks and no merged names like whatsappcrm
if [ -f "sites/apps.txt" ]; then
    sed -i 's/whatsappcrm/whatsapp\ncrm/' sites/apps.txt
    sed -i 's/frappecrm/frappe\ncrm/' sites/apps.txt
fi
if ! grep -qx "crm" sites/apps.txt 2>/dev/null; then
    printf "\ncrm\n" >> sites/apps.txt
fi
# Clean up empty lines and duplicates
awk '!seen[$0]++' sites/apps.txt > sites/apps.tmp && mv sites/apps.tmp sites/apps.txt
sed -i '/^$/d' sites/apps.txt

# Setup app links in /workspace for frontend relative imports
ln -sfn "$BENCH_DIR/apps/frappe" /workspace/frappe 2>/dev/null || true
ln -sfn "$BENCH_DIR/apps/whatsapp" /workspace/whatsapp 2>/dev/null || true

# 7. Check if site crm.localhost exists and is initialized
SITE_READY=0
if [ -f "sites/crm.localhost/site_config.json" ]; then
    echo "Checking existing site crm.localhost..."
    if ./env/bin/python -c "import frappe; frappe.init('crm.localhost'); frappe.connect(); assert 'crm' in frappe.get_installed_apps()" 2>/dev/null; then
        echo "Site crm.localhost and CRM app are already initialized."
        SITE_READY=1
    fi
fi

if [ "$SITE_READY" -eq 0 ]; then
    echo "Setting up new site crm.localhost..."
    bench new-site crm.localhost \
        --force \
        --mariadb-root-password 123 \
        --admin-password admin \
        --no-mariadb-socket

    echo "Installing CRM app on crm.localhost..."
    bench --site crm.localhost install-app crm
fi

# 8. Configure development settings & site defaults
echo "Configuring site settings..."
bench --site crm.localhost set-config developer_mode 1
bench --site crm.localhost set-config mute_emails 1
bench --site crm.localhost set-config server_script_enabled 1
bench --site crm.localhost set-config home_page crm
bench set-config -g default_site crm.localhost
bench use crm.localhost

# Create localhost alias for the site so http://localhost:8000 routes properly
if [ ! -e "sites/localhost" ]; then
    ln -s crm.localhost sites/localhost 2>/dev/null || true
fi

# 9. Run migrations and clear cache
echo "Running migrations on crm.localhost..."
bench --site crm.localhost migrate
bench --site crm.localhost clear-cache

# 10. Register custom Lead List Script if present
if [ -f /workspace/docker/register_lead_script.py ]; then
    echo "Registering custom Lead List Script..."
    /home/frappe/frappe-bench/env/bin/python /workspace/docker/register_lead_script.py || echo "Note: CRM Form Script registration skipped."
fi

# 11. Build frontend assets if needed
if [ ! -f "/workspace/crm/www/crm.html" ]; then
    echo "Building CRM frontend assets..."
    cd /workspace/frontend
    if [ ! -d "node_modules" ]; then
        yarn install --check-files
    fi
    yarn build
    cd "$BENCH_DIR"
fi

echo "Building bench assets..."
bench build --app frappe
bench build --app crm

# 12. Verification check
echo "Verifying installed apps on crm.localhost:"
bench --site crm.localhost list-apps

echo "=== Frappe CRM Setup Complete. Starting bench... ==="
exec bench start