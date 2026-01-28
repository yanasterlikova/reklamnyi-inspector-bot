#!/bin/bash

# Скрипт проверки статуса Рекламного Инспектора на Beget

SERVER_HOST="root@2.56.240.113"
SERVER_PASSWORD="vnJI0T57jxj%"

echo "🔍 Проверка статуса Рекламного Инспектора..."
echo ""

sshpass -p "$SERVER_PASSWORD" ssh $SERVER_HOST << 'EOF'
echo "📊 Статус сервиса:"
systemctl status reklamnyi-inspector --no-pager

echo ""
echo "📝 Последние 20 строк лога:"
journalctl -u reklamnyi-inspector -n 20 --no-pager

echo ""
echo "💾 Использование диска:"
df -h /opt/reklamnyi_inspector

echo ""
echo "📈 Статистика базы данных:"
if [ -f /opt/reklamnyi_inspector/data/users.db ]; then
    echo "База данных найдена ✅"
    cd /opt/reklamnyi_inspector
    python3 -c "from database import Database; db = Database(); stats = db.get_stats(); print(f'Пользователей: {stats[\"total_users\"]}'); print(f'Проверок: {stats[\"total_checks\"]}'); print(f'Регистраций сегодня: {stats[\"today_registrations\"]}')"
else
    echo "База данных не найдена ❌"
fi
EOF

echo ""
echo "✅ Проверка завершена"
