if [ $# -ne 1 ]
then
  "There must be only one argument - label (debug, arsen, vova, ilya, front)"
  exit 1
fi

label=$1

echo "[DEBUG] Starting Project..."

echo "[DEBUG] Starting API service... [Step 1/4]"
systemctl --user enable dev_api@${label}.service
systemctl --user restart dev_api@${label}.service & sleep 3
systemctl --user status --no-pager dev_api@${label}.service | grep Loaded
systemctl --user status --no-pager dev_api@${label}.service | grep Active

echo "[DEBUG] Starting Telegram bot service... [Step 2/4]"
systemctl --user enable dev_bot@${label}.service
systemctl --user restart dev_bot@${label}.service & sleep 3
systemctl --user status --no-pager dev_bot@${label}.service | grep Loaded
systemctl --user status --no-pager dev_bot@${label}.service | grep Active

echo "[DEBUG] Starting MultiBot service... [Step 3/4]"
systemctl --user enable dev_multibot@${label}.service
systemctl --user restart dev_multibot@${label}.service & sleep 3
systemctl --user status --no-pager dev_multibot@${label}.service | grep Loaded
systemctl --user status --no-pager dev_multibot@${label}.service | grep Active

echo "[DEBUG] Building webapp frontend... [Step 4/4]"

cd web_app/ezShop
npm install
npm run build
