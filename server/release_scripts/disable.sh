echo "Stopping Project..."
echo "Stopping API service... [Step 1/2]"
systemctl disable release_api.service
systemctl stop release_api.service
systemctl status release_api.service | grep Loaded
systemctl status release_api.service | grep Active
echo "Stopping Telegram bot service... [Step 2/2]"
systemctl disable release_bot.service
systemctl stop release_bot.service
systemctl status release_bot.service | grep Loaded
systemctl status release_bot.service | grep Active
