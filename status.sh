echo "Getting services status..."
echo "API service [1/3]"
systemctl status api.service | grep Loaded
systemctl status api.service | grep Active
echo "Telegram bot service [2/3]"
systemctl status bot.service | grep Loaded
systemctl status bot.service | grep Active
echo "WebApp service [3/3]"
systemctl status webapp.service | grep Loaded
systemctl status webapp.service | grep Active

