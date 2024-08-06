echo "Starting Project..."

echo "Starting API service... [Step 1/4]"
systemctl enable release_api.service
systemctl restart release_api.service &
sleep 3
systemctl status release_api.service | grep Loaded
systemctl status release_api.service | grep Active

echo "Starting Telegram bot service... [Step 2/4]"
systemctl enable release_bot.service
systemctl restart release_bot.service &
sleep 3
systemctl status release_bot.service | grep Loaded
systemctl status release_bot.service | grep Active

echo "Starting MultiBot service... [Step 3/4]"
systemctl enable release_multibot.service
systemctl restart release_multibot.service &
sleep 3
systemctl status release_multibot.service | grep Loaded
systemctl status release_multibot.service | grep Active

echo "Building webapp frontend... [Step 4/4]"
cd webapp/frontend
npm install
npm run build
