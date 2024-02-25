echo "Starting Project..."
echo "Starting API service... [Step 1/2]"
systemctl enable release_api.service
systemctl restart release_api.service &
sleep 3
systemctl status release_api.service | grep Loaded
systemctl status release_api.service | grep Active
echo "Starting Telegram bot service... [Step 2/2]"
systemctl enable release_bot.service
systemctl restart release_bot.service &
sleep 3
systemctl status release_bot.service | grep Loaded
systemctl status release_bot.service | grep Active
