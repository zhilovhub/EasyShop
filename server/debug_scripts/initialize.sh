if [ $# -ne 1 ]
then
  "There must be only one argument - label (debug, arsen, vova, ilya, front)"
  exit 1
fi

label=$1
directory_path=/home/debug/${label}EzShop
services_path=${directory_path}/server/debug_services

if [ ! -d "${directory_path}/venv" ]; then
  echo "venv does not exist creating..."
  python -m venv ${directory_path}/venv
else echo "venv directory found."
fi

source ${directory_path}/venv/bin/activate
echo "Installing python requirements..."
pip install -r ${directory_path}/api/requirements.txt
pip install -r ${directory_path}/bot/requirements.txt
echo "Complete."
echo "Creating systemd services..."
cp ${services_path}/dev_api@.service ~/.config/systemd/user/dev_api@.service
cp ${services_path}/dev_bot@.service ~/.config/systemd/user/dev_bot@.service
cp ${services_path}/dev_multibot@.service ~/.config/systemd/user/dev_multibot@.service
cp ${services_path}/dev_supportbot@.service ~/.config/systemd/user/dev_supportbot@.service
echo "Restarting systemd daemon..."

systemctl --user daemon-reload
echo "Services created."
echo "Trying upgrade migrations..."
alembic upgrade head
echo "Setup complete."
