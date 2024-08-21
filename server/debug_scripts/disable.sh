if [ $# -ne 1 ]
then
  "There must be only one argument - label (debug, arsen, vova, ilya, front)"
  exit 1
fi

label=$1

echo "[DEBUG] Stopping Project..."
echo "[DEBUG] Stopping API service... [Step 1/4]"
systemctl --user disable dev_api@${label}.service
systemctl --user stop dev_api@${label}.service
systemctl --user status dev_api@${label}.service | grep Loaded
systemctl --user status dev_api@${label}.service | grep Active

echo "[DEBUG] Stopping Telegram bot service... [Step 2/4]"
systemctl --user disable dev_bot@.service
systemctl --user stop dev_bot@${label}.service
systemctl --user status dev_bot@${label}.service | grep Loaded
systemctl --user status dev_bot@${label}.service | grep Active

echo "[DEBUG] Stopping Multi bot service... [Step 3/4]"
systemctl --user disable dev_multibot@.service
systemctl --user stop dev_multibot@${label}.service
systemctl --user status dev_multibot@${label}.service | grep Loaded
systemctl --user status dev_multibot@${label}.service | grep Active

echo "[DEBUG] Stopping Support bot service... [Step 4/4]"
systemctl --user disable dev_supportbot@.service
systemctl --user stop dev_supportbot@${label}.service
systemctl --user status dev_supportbot@${label}.service | grep Loaded
systemctl --user status dev_supportbot@${label}.service | grep Active

