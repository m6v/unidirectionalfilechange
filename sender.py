#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from subprocess import Popen, PIPE
import os
import sys
import time
import getopt
import subprocess
import syslog
import json

# TODO: сделать расчет контрольной суммы файла и размещать ее начале концевика
#       научиться дописывать концевик в файлы с пробелами, скобками и др.символами
#       создать конфигурационный файл в котором задавать список addr: port и осуществлять по нему множественную рассылку


def main():
    trailer_size = 256
    timeout = 5
    port = 4500

    if len(sys.argv) < 2:
        print("missing operand")
        sys.exit(1)

    syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:ta:p', ['dir=', 'timeout=', 'addr=', 'port='])  # двоеточие после параметров, требующих дополнительного аргумента
        for opt, value in opts:
            if opt in ('-d', '--dir'):
                dirname = value
            elif opt in ('-t', '--timeout'):
                timeout = int(value)
            elif opt in ('-a', '--addr'):
                addr = value
            elif opt in ('-p', '--port'):
                port = value
    except getopt.error as err:
        print(err)
        syslog.syslog(err)
        exit(2)

    if not os.path.isdir(dirname):
        print("Directory", dirname, "not exist")
        syslog.syslog("Directory", dirname, "not exist")
        sys.exit(3)

    print("Watches directory is", dirname)
    print("Timeout is", timeout, "seconds")

    while True:
        try:
            filename, err = Popen("inotifywait -e close --format %f " + dirname, shell=True, stdout=PIPE).communicate()

            filename = filename.decode("utf-8")

            if len(filename) > 1:  # имя файла = 1 при удалении удалении файла в отслеживаемом каталоге

                # служебная информация
                metadata = {"filename": filename, "md5sum": "1234567890"}
            
                # дополняем справа строку до размера trailer_size байт и сериализуем концевик
                trailer = json.dumps(metadata).ljust(trailer_size)

                fullfilename = os.path.join(dirname, filename.rstrip())  # rstrip() удаляет последний символ переноса строки \n

                # fullfilename = fullfilename.replace(" ", "\\ ")  # далее файл открывается, но начинаются проблемы с трейлером

                print("Filename:", fullfilename)

                fd = open(fullfilename, "a")
                fd.write(trailer)
                fd.close()

                time.sleep(timeout)

                command = "hairgaps -p " + port + " -r 2 -N 30000 " + addr + " < " + fullfilename
                subprocess.call(command, shell=True)
                # ошибка при файлах с пробелами в имени, круглыми скобками

                syslog.syslog("File " + filename.rstrip() + " is sent to " + "127.0.0.1")

                # снятие концевика файла
                fd = os.open(fullfilename, os.O_RDWR | os.O_CREAT)
                file_size = os.path.getsize(fullfilename)
                # обрезаем последние trailer_size байтов файла
                os.ftruncate(fd, file_size - trailer_size)
                os.close(fd)

        except Exception as err:
            print(err)
            syslog.syslog(err)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Killed by user")
        sys.exit(0)
