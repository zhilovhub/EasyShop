if [ ! -d "/root/EasyShop/venv" ]; then
  echo "venv does not exist creating..."
  python -m venv /root/EasyShop/venv
else echo "venv directory found."
fi
source /root/EasyShop/venv/bin/activate
echo "Installing python requirements..."
pip install -r /root/EasyShop/api/requirements.txt
pip install -r /root/EasyShop/bot/requirements.txt
echo "Complete."
echo "Creating systemd services..."
cp /root/EasyShop/release_services/release_api.service /etc/systemd/system/release_api.service
cp /root/EasyShop/release_services/release_bot.service /etc/systemd/system/release_bot.service
echo "Restarting systemd daemon..."
systemctl daemon-reload
echo "Services created."
echo "Trying upgrade migrations..."
alembic upgrade head
echo "Setup complete."
