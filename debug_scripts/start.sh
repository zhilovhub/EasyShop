echo "[DEBUG] Starting Project..."
echo "[DEBUG] Starting API service... [Step 1/2]"
systemctl enable debug_api.service
systemctl restart debug_api.service &
sleep 3
systemctl status debug_api.service | grep Loaded
systemctl status debug_api.service | grep Active
echo "[DEBUG] Starting Telegram bot service... [Step 2/2]"
systemctl enable debug_bot.service
systemctl restart debug_bot.service &
sleep 3
systemctl status debug_bot.service | grep Loaded
systemctl status debug_bot.service | grep Active