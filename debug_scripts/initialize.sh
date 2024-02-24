if [ ! -d "/root/DebugEasyShop/venv" ]; then
  echo "venv does not exist creating..."
  python -m venv /root/DebugEasyShop/venv
else echo "venv directory found."
fi
source root/DebugEasyShop/venv/bin/activate
echo "Installing python requirements..."
pip install -r /root/DebugEasyShop/api/requirements.txt
pip install -r /root/DebugEasyShop/bot/requirements.txt
echo "Complete."
echo "Creating systemd services..."
cp /root/DebugEasyShop/debug_services/debug_api.service /etc/systemd/system/debug_api.service
cp /root/DebugEasyShop/debug_services/debug_bot.service /etc/systemd/system/debug_bot.service
echo "Restarting systemd daemon..."
systemctl daemon-reload
echo "Services created."
echo "Trying upgrade migrations..."
alembic upgrade head
echo "Setup complete."
