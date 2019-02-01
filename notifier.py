#!/usr/bin/env python3
# coding: utf-8

import sys
import pika

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QBoxLayout
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QWaitCondition
from PyQt5.QtCore import QMutex
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot

# TODO: сделать сворачивание в трей
#  (см.: http://qaru.site/questions/3192733/pyqt5-qobject-cannot-create-children-for-a-parent-that-is-in-a-different-thread)
#       использовать QtDesigner для создания формы (см.: http://pyobject.ru/blog/2008/05/07/pyqt-unpythonic-gui)

__author__ = "Sergey Maksimov <m6v@mail.com>"


class Worker(QObject):
    # сигнал, генерируемый при приеме очередного файла
    recieve_file = pyqtSignal(str)

    def __init__(self):
        super(Worker, self).__init__()

        self.condition = QWaitCondition()
        self.mutex = QMutex()

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='hello')
        self.channel.basic_consume('hello', self.callback, auto_ack=True)

    @pyqtSlot()
    def slot_run(self):
        # уточнить нужны ли мьютексы в данном случае или нет?
        self.mutex.lock()
        self.channel.start_consuming()
        self.mutex.unlock()

    def callback(self, ch, method, properties, body):
        print("[x] Received %r" % (body,))

        # генерируем сигнал recieve_file
        self.recieve_file.emit(body.decode('utf-8'))


class Form(QWidget):
    def __init__(self):
        QWidget.__init__(self, flags=Qt.Widget)

        # создали поток
        self.thread = QThread()

        # создали воркер и поместили его в поток
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        # связываем сигнал thread.started
        # со слотом        worker.slot_run
        self.thread.started.connect(self.worker.slot_run)
        # связываем сигнал worker.recieve_file
        # со слотом        self.slot_recieve_file
        self.worker.recieve_file.connect(self.slot_recieve_file)

        # запускаем поток
        self.thread.start()

        self.table = QTableWidget()  # Ссоздаём таблицу
        self.table.setColumnCount(2)  # устанавливаем две колонки
        self.table.setHorizontalHeaderLabels(["Дата", "Файл"])
        # self.table.setRowCount(1)  # добавляем одну строку

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 100)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        self.pushbutton = QPushButton("Close")
        # связываем сигнал pushbutton.clicked
        # со слотом        self.slot_clicked_button
        self.pushbutton.clicked.connect(self.slot_clicked_button)

        self.setWindowTitle("UnidirectionalFileChange Notifier")
        boxlayout = QBoxLayout(QBoxLayout.TopToBottom, parent=self)
        self.setLayout(boxlayout)

        boxlayout.addWidget(self.table)
        boxlayout.addWidget(self.pushbutton)

    @pyqtSlot()
    def slot_clicked_button(self):
        self.close()

    @pyqtSlot(str)
    def slot_recieve_file(self, body):
        date_time = body.partition(" ")[0]
        file_name = body.partition(" ")[2]

        currentRowCount = self.table.rowCount()
        self.table.insertRow(currentRowCount)
        self.table.setItem(currentRowCount, 0, QTableWidgetItem(date_time))
        self.table.setItem(currentRowCount, 1, QTableWidgetItem(file_name))

        # делаем ресайз колонок по содержимому
        self.table.resizeColumnsToContents()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    sys.exit(app.exec_())
