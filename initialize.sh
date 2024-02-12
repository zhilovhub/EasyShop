if [ ! -d "venv" ]; then
  echo "venv does not exist creating..."
  python -m venv venv
else echo "venv directory found."
fi
source venv/bin/activate
echo "Installing python requirements..."
pip install -r api/requirements.txt
pip install -r bot/requirements.txt
echo "Complete."
echo "Creating systemd services..."
cp services/api.service /etc/systemd/system/api.service
cp services/bot.service /etc/systemd/system/bot.service
cp services/webapp.service /etc/systemd/system/webapp.service
echo "Services created."
echo "Trying upgrade migrations..."
alembic upgrade head
echo "Setup complete."
