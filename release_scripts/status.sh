echo "Getting services status..."
echo "API service [1/2]"
systemctl status release_api.service | grep Loaded
systemctl status release_api.service | grep Active
echo "Telegram bot service [2/2]"
systemctl status release_bot.service | grep Loaded
systemctl status release_bot.service | grep Active
