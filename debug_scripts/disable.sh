echo "[DEBUG] Stopping Project..."
echo "[DEBUG] Stopping API service... [Step 1/2]"
systemctl --user disable debug_api.service
systemctl --user stop debug_api.service
systemctl --user status debug_api.service | grep Loaded
systemctl --user status debug_api.service | grep Active
echo "[DEBUG] Stopping Telegram bot service... [Step 2/2]"
systemctl --user disable debug_bot.service
systemctl --user stop debug_bot.service
systemctl --user status debug_bot.service | grep Loaded
systemctl --user status debug_bot.service | grep Active
