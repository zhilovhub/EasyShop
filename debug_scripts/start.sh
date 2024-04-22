echo "[DEBUG] Starting Project..."
echo "[Channel] Starting MultiBot service... [Step 1/1]"
systemctl --user enable channel_multibot.service
systemctl --user restart channel_multibot.service &
sleep 3
systemctl --user status channel_multibot.service | grep Loaded
systemctl --user status channel_multibot.service | grep Active
