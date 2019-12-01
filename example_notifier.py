#!/usr/bin/env python3
import notify2
import sys
import os

# см.: https://bitbucket.org/takluyver/pynotify2/src/default/

# Инициализируем d-bus соединение
notify2.init("Demo application")

# Image URI
uri = "file://" + os.path.abspath(os.path.curdir) + "/applet-critical.png"

# Создаем Notification-объект
n = notify2.Notification("Summary", "Body text goes here", uri)

# Устанавливаем уровень срочности
n.set_urgency(notify2.URGENCY_NORMAL)
        
# Устанавливаем задержку
n.set_timeout(5000)

# Показываем уведомление
n.show()