#!/usr/bin/env bash

log_file=${LOGS_DIR}/trigger_standup_dialog.log
if [[ ! -f "${log_file}" ]]; then
  touch ${log_file}
fi

# Initialize cron.
echo "Running as $(id)"
if [ "$(id -u)" -eq 0 ] && [ "$(grep -c "$CRON_CMD" "$CRONFILE")" -eq 0 ]; then
  echo "Initializing..."
  cron_time=${CRON_TIME:1:${#CRON_TIME}-2}
  echo "$cron_time $CRON_CMD >> ${log_file} 2>&1" | crontab -
fi

# Start crond if it's not running.
pgrep crond > /dev/null 2>&1
if [ $? -ne 0 ]; then
  /usr/sbin/crond -L ${LOGS_DIR}/cron.log
fi

/usr/bin/python3 /root/bot/endpoint.py
