#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
import sys
import subprocess
import datetime
import getopt
import pika
import json

# TODO: отключить сохранение пустых файлов
#       сделать проверку контрольной суммы полученного файла
#       обработка исключения Ctrl + C (см. https://stackoverflow.com/questions/6598053/python-global-exception-handling)
#       перейти на pynotify (см. https://www.linode.com/docs/development/monitor-filesystem-events-with-pyinotify)
#       с учетом замечаний Bryan O'Sullivan's blog.Why you should not use pyinotify
#       (см. http://www.serpentine.com/blog/2008/01/04/why-you-should-not-use-pyinotify)
#       альтернативные варианты pyinotify см. https://bitbucket.org/JanKanis/python-inotify
#                                             https://bitbucket.org/bos/python-inotify
#                                             https://github.com/trendels/gevent_inotifyx
#       запись метаданных в SQLite


def main():
    trailer_size = 256
    port = 4500

    if len(sys.argv) < 2:
        print("missing operand")
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:a:p', ['dir=', 'addr=', 'port='])
        for opt, value in opts:
            if opt in ('-d', '--dir'):
                dirname = value
                print("Download directory is", dirname)
            elif opt in ('-a', '--addr'):
                addr = value
            elif opt in ('-p', '--port'):
                port = value

    except getopt.error as err:
        print(err)
        exit(2)

    if not os.path.isdir(dirname):
        print("Directory", dirname, "not exist")
        sys.exit(3)

    while True:
        try:
            tempfilename = os.path.join(dirname, datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + ".raw")
            command = "hairgapr -p " + port + " " + addr + " > " + tempfilename
            subprocess.call(command, shell=True)

            print("filesize:", os.path.getsize(tempfilename))
            if os.path.getsize(tempfilename) == 0:
                print("Deleting", tempfilename, "...")  # почему-то не печатается в консоли?!
                os.remove(tempfilename)  # почему-то удаляется предыдущий по времени файл, а последний остается?!
                continue

            fd = os.open(tempfilename, os.O_RDWR | os.O_CREAT)
            file_size = os.path.getsize(tempfilename)
            os.lseek(fd, file_size - trailer_size, 0)
            trailer = os.read(fd, trailer_size)

            # десериализуем концевик
            metadata = json.loads(trailer.decode("utf-8"))
            filename = metadata["filename"].rstrip()
            md5sum = metadata["md5sum"].rstrip()
            print(filename, md5sum)

            # обрезаем последние trailer_size байтов файла
            os.ftruncate(fd, file_size - trailer_size)

            os.close(fd)

            # переименовываем файл
            os.rename(tempfilename, dirname + "/" + filename)

            # print("File", dirname + filename, "is downloaded")

            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            # создаем очередь, в которую будут отправляться сообщения
            channel.queue_declare(queue='hello')

            channel.basic_publish(exchange='', routing_key='hello', body=datetime.datetime.today().strftime("%Y-%m-%d-%H:%M:%S") + " " + filename)

            connection.close()

        except Exception as err:
            print(err)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Killed by user")
        sys.exit(0)
