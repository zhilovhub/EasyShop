if [ $# -ne 1 ]
then
  "There must be only one argument - label (debug, arsen, vova, ilya, front)"
  exit 1
fi

label=$1

echo "[DEBUG] Getting services status..."

echo "[DEBUG] API service [1/4]"
systemctl --user status dev_api@${label}.service | grep Loaded
systemctl --user status dev_api@${label}.service | grep Active

echo "[DEBUG] Telegram bot service [2/4]"
systemctl --user status dev_bot@${label}.service | grep Loaded
systemctl --user status dev_bot@${label}.service | grep Active

echo "MultiBot service [3/4]"
systemctl --user status dev_multibot@${label}.service | grep Loaded
systemctl --user status dev_multibot@${label}.service | grep Active

echo "SupportBot service [4/4]"
systemctl --user status dev_supportbot@${label}.service | grep Loaded
systemctl --user status dev_supportbot@${label}.service | grep Active

