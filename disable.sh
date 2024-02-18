echo "Stopping Project..."
echo "Stopping API service... [Step 1/3]"
systemctl disable api.service
systemctl stop api.service
systemctl status api.service | grep Loaded
systemctl status api.service | grep Active
echo "Stopping Telegram bot service... [Step 2/3]"
systemctl disable bot.service
systemctl stop bot.service
systemctl status bot.service | grep Loaded
systemctl status bot.service | grep Active
echo "Stopping WebApp service... [Step 3/3]"
systemctl disable webapp.service 
systemctl stop webapp.service
systemctl status webapp.service | grep Loaded
systemctl status webapp.service | grep Active
