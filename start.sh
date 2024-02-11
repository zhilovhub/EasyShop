echo "Starting Project..."
echo "Starting API service... [Step 1/3]"
systemctl restart api.service
systemctl status api.service | grep Active
echo "Starting Telegram bot service... [Step 2/3]"
systemctl restart bot.service
systemctl status bot.service | grep Active
echo "Starting WebApp service... [Step 3/3]"
systemctl restart webapp.service
systemctl status webapp.service | grep Active
