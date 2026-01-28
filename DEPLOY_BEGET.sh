#!/bin/bash

# Скрипт деплоя Рекламного Инспектора на Beget VPS

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Настройки сервера
SERVER_HOST="root@2.56.240.113"  # IP сервера Beget
SERVER_PATH="/opt/reklamnyi_inspector"
SERVER_PASSWORD="vnJI0T57jxj%"

echo -e "${YELLOW}🚀 Деплой Рекламного Инспектора на Beget...${NC}"

# Проверяем наличие .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo "Скопируйте env.example в .env и заполните настройки"
    exit 1
fi

echo -e "${YELLOW}📦 Копируем файлы на сервер...${NC}"

# Копируем файлы (исключаем .env, data, кэши)
sshpass -p "$SERVER_PASSWORD" rsync -avz \
    --exclude='.env' \
    --exclude='data/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    ./ $SERVER_HOST:$SERVER_PATH/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Файлы загружены на сервер${NC}"
else
    echo -e "${RED}❌ Ошибка при копировании файлов${NC}"
    exit 1
fi

echo -e "${YELLOW}⚙️ Устанавливаем зависимости на сервере...${NC}"

sshpass -p "$SERVER_PASSWORD" ssh $SERVER_HOST << EOF
cd $SERVER_PATH
pip3 install -r requirements.txt
EOF

echo -e "${YELLOW}🔄 Перезапускаем бота...${NC}"

sshpass -p "$SERVER_PASSWORD" ssh $SERVER_HOST << EOF
systemctl restart reklamnyi-inspector
systemctl status reklamnyi-inspector
EOF

echo -e "${GREEN}✅ Деплой завершен!${NC}"
echo ""
echo -e "${YELLOW}📊 Проверьте статус:${NC}"
echo "ssh $SERVER_HOST"
echo "systemctl status reklamnyi-inspector"
echo "journalctl -u reklamnyi-inspector -f"
