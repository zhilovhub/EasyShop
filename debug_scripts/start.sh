echo "[DEBUG] Starting Project..."
echo "[DEBUG] Starting API service... [Step 1/3]"
systemctl enable debug_api.service
systemctl restart debug_api.service &
sleep 3
systemctl status debug_api.service | grep Loaded
systemctl status debug_api.service | grep Active
echo "[DEBUG] Starting Telegram bot service... [Step 2/3]"
systemctl enable debug_bot.service
systemctl restart debug_bot.service &
sleep 3
systemctl status debug_bot.service | grep Loaded
systemctl status debug_bot.service | grep Active
echo "[DEBUG] Starting MultiBot service... [Step 3/3]"
systemctl enable debug_multibot.service
systemctl restart debug_multibot.service &
sleep 3
systemctl status debug_multibot.service | grep Loaded
systemctl status debug_multibot.service | grep Active
