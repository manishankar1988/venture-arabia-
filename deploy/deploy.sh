#!/usr/bin/env bash
# Update a plain-server deployment from git and restart the app.
#   ssh venture@server 'bash /srv/venture/deploy/deploy.sh'
set -euo pipefail
cd /srv/venture

echo "== pulling latest code"
git pull --ff-only origin main

echo "== installing dependencies"
.venv/bin/pip install -q -r requirements.txt

echo "== migrating database and collecting static files"
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py check --deploy

echo "== restarting"
sudo systemctl restart venture
sudo systemctl --no-pager --lines=3 status venture
echo "== done"
