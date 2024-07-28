if [ ! -d "/home/debug/EasyShop/venv" ]; then
  echo "venv does not exist creating..."
  python -m venv /home/debug/EasyShop/venv
else echo "venv directory found."
fi
source /home/debug/EasyShop/venv/bin/activate
echo "Installing python requirements..."
pip install -r /home/debug/EasyShop/api/requirements.txt
pip install -r /home/debug/EasyShop/bot/requirements.txt
echo "Complete."
echo "Creating systemd services..."
cp /home/debug/EasyShop/debug_services/debug_api.service ~/.config/systemd/user/debug_api.service
cp /home/debug/EasyShop/debug_services/debug_bot.service ~/.config/systemd/user/debug_bot.service
cp /home/debug/EasyShop/debug_services/debug_multibot.service ~/.config/systemd/user/debug_multibot.service
echo "Restarting systemd daemon..."
systemctl --user daemon-reload
echo "Services created."
echo "Trying upgrade migrations..."
alembic upgrade head
echo "Setup complete."
