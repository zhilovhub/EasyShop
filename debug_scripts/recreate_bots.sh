for d in $(find bot/bots -maxdepth 1 -type d)
do
  if [ $d = "bot/bots" ]
    then
    continue
  fi
  echo "copying from template to $d"
  cp -T -r bot/template/ $d/
  work_dir=/root/DebugEasyShop/$d
  echo changing working dir in service to $work_dir
  python -c "file = open('$d/bot.service', 'r'); file_text = file.read().strip().replace('{working_directory}', '$work_dir'); file.close(); file = open('$d/bot.service', 'w'); file.write(file_text)"
  echo copying service to /etc/systemd/system/
  bot_name=$(echo $d | sed 's#bot/bots/##g')
  cp $d/bot.service /etc/systemd/system/$bot_name
done
  echo restarting systemd daemon
  systemctl daemon-reload
  sleep 3
for d in $(find bot/bots -maxdepth 1 -type d)
do
  if [ $d = "bot/bots" ]
    then
      continue
  fi
  bot_name=$(echo $d | sed 's#bot/bots/##g')
  echo restarting bot $bot_name
  systemctl restart $bot_name
  systemctl status $bot_name | grep Active
done
