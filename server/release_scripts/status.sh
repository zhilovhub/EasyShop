echo "Getting services status..."
echo "API service [1/3]"
systemctl status release_api.service | grep Loaded
systemctl status release_api.service | grep Active
echo "Telegram bot service [2/3]"
systemctl status release_bot.service | grep Loaded
systemctl status release_bot.service | grep Active
echo "MultiBot service [3/3]"
systemctl status release_multibot.service | grep Loaded
systemctl status release_multibot.service | grep Active
