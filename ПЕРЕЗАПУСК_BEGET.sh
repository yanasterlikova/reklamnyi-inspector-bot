#!/bin/bash

# Скрипт перезапуска Рекламного Инспектора на Beget

SERVER_HOST="root@2.56.240.113"
SERVER_PASSWORD="vnJI0T57jxj%"

echo "🔄 Перезапуск Рекламного Инспектора..."

sshpass -p "$SERVER_PASSWORD" ssh $SERVER_HOST << 'EOF'
systemctl restart reklamnyi-inspector
sleep 2
systemctl status reklamnyi-inspector --no-pager
EOF

echo ""
echo "✅ Бот перезапущен"
