echo "[DEBUG] Starting Project..."
echo "[DEBUG] Starting API service... [Step 1/4]"
systemctl --user enable debug_api.service
systemctl --user restart debug_api.service &
sleep 3
systemctl --user status debug_api.service | grep Loaded
systemctl --user status debug_api.service | grep Active
echo "[DEBUG] Starting Telegram bot service... [Step 2/4]"
systemctl --user enable debug_bot.service
systemctl --user restart debug_bot.service &
sleep 3
systemctl --user status debug_bot.service | grep Loaded
systemctl --user status debug_bot.service | grep Active
echo "[DEBUG] Starting MultiBot service... [Step 3/4]"
systemctl --user enable debug_multibot.service
systemctl --user restart debug_multibot.service &
sleep 3
systemctl --user status debug_multibot.service | grep Loaded
systemctl --user status debug_multibot.service | grep Active
echo "[DEBUG] Building webapp frontend... [Step 4/4]"
cd webapp/frontend
npm run build
