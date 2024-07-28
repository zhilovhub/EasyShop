if [ $# -ne 1 ]
then
  "There must be only one argument - label (debug, arsen, vova, ilya, front)"
  exit 1
fi

label=$1

echo "[DEBUG] Stopping Project..."
echo "[DEBUG] Stopping API service... [Step 1/3]"
systemctl --user disable dev_api@${label}.service
systemctl --user stop dev_api@${label}.service
systemctl --user status dev_api@${label}.service | grep Loaded
systemctl --user status dev_api@${label}.service | grep Active
echo "[DEBUG] Stopping Telegram bot service... [Step 2/3]"
systemctl --user disable dev_bot@.service
systemctl --user stop dev_bot@${label}.service
systemctl --user status dev_bot@${label}.service | grep Loaded
systemctl --user status dev_bot@${label}.service | grep Active
echo "[DEBUG] Stopping Multi bot service... [Step 3/3]"
systemctl --user disable dev_multibot@.service
systemctl --user stop dev_multibot@${label}.service
systemctl --user status dev_multibot@${label}.service | grep Loaded
systemctl --user status dev_multibot@${label}.service | grep Active

