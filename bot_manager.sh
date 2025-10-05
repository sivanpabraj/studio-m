#!/bin/bash
# 🤖 اسکریپت مدیریت ربات استودیو مندانی

case "$1" in
    start)
        echo "🚀 شروع ربات..."
        cd /Users/mandanistudio/Documents/mandanibot
        nohup python main.py > bot.log 2>&1 &
        echo "✅ ربات در پس‌زمینه شروع شد"
        echo "📝 لاگ: tail -f bot.log"
        ;;
    stop)
        echo "⏹️ متوقف کردن ربات..."
        pkill -f "python main.py"
        echo "✅ ربات متوقف شد"
        ;;
    status)
        echo "📊 وضعیت ربات:"
        ps aux | grep "python main.py" | grep -v grep
        ;;
    log)
        echo "📝 آخرین لاگ‌ها:"
        tail -20 /Users/mandanistudio/Documents/mandanibot/bot.log
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "استفاده: $0 {start|stop|status|log|restart}"
        exit 1
        ;;
esac
