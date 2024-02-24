echo "[DEBUG] Getting services status..."
echo "[DEBUG] API service [1/2]"
systemctl status debug_api.service | grep Loaded
systemctl status debug_api.service | grep Active
echo "[DEBUG] Telegram bot service [2/2]"
systemctl status debug_bot.service | grep Loaded
systemctl status debug_bot.service | grep Active

