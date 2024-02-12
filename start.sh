echo "Starting Project..."
echo "Starting API service... [Step 1/3]"
systemctl enable api.service
systemctl restart api.service &
sleep 3
systemctl status api.service | grep Loaded
systemctl status api.service | grep Active
echo "Starting Telegram bot service... [Step 2/3]"
systemctl enable bot.service
systemctl restart bot.service &
sleep 3
systemctl status bot.service | grep Loaded
systemctl status bot.service | grep Active
echo "Starting WebApp service... [Step 3/3]"
systemctl enable webapp.service 
systemctl restart webapp.service &
sleep 3
systemctl status webapp.service | grep Loaded
systemctl status webapp.service | grep Active