echo "[DEBUG] Stopping Project..."
echo "[DEBUG] Stopping API service... [Step 1/2]"
systemctl disable debug_api.service
systemctl stop debug_api.service
systemctl status debug_api.service | grep Loaded
systemctl status debug_api.service | grep Active
echo "[DEBUG] Stopping Telegram bot service... [Step 2/2]"
systemctl disable debug_bot.service
systemctl stop debug_bot.service
systemctl status debug_bot.service | grep Loaded
systemctl status debug_bot.service | grep Active
