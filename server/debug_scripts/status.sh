echo "[DEBUG] Getting services status..."
echo "[DEBUG] API service [1/3]"
systemctl --user status debug_api.service | grep Loaded
systemctl --user status debug_api.service | grep Active
echo "[DEBUG] Telegram bot service [2/3]"
systemctl --user status debug_bot.service | grep Loaded
systemctl --user status debug_bot.service | grep Active
echo "MultiBot service [3/3]"
systemctl --user status debug_multibot.service | grep Loaded
systemctl --user status debug_multibot.service | grep Active

