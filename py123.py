import sys
import configparser
import subprocess
import time
import psutil
import os
import signal
import logging
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                             QFileDialog, QVBoxLayout, QTextEdit, QHBoxLayout)
from PyQt5.QtCore import Qt

# 配置日志记录
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 创建文件处理器，设置 GBK 编码
file_handler = logging.FileHandler('service_manager.log', encoding='gbk')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

# 配置日志输出到控制台
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

# 添加处理器到 logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# 自定义的日志处理器，用于在GUI中显示日志
class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)
        self.text_edit.ensureCursorVisible()


# 脚本主类
class ServiceManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.service_name = ""
        self.wait_time = 0
        self.wait_after_time = 0
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()

    def initUI(self):
        self.setWindowTitle('Service Manager V1.0')

        layout = QVBoxLayout()

        self.service_label = QLabel('服务名称:')
        self.service_input = QLineEdit(self)

        self.wait_label = QLabel('等待时间 (秒):')
        self.wait_input = QLineEdit(self)

        self.wait_after_label = QLabel('关闭后等待时间 (秒):')
        self.wait_after_input = QLineEdit(self)

        self.start_button = QPushButton('启动脚本', self)
        self.start_button.clicked.connect(self.start_script)

        self.stop_button = QPushButton('停止脚本', self)
        self.stop_button.clicked.connect(self.stop_script)
        self.stop_button.setEnabled(False)

        self.status_label = QLabel('状态: 未运行')
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)

        # 添加自定义日志处理器
        text_edit_logger = QTextEditLogger(self.log_output)
        logger.addHandler(text_edit_logger)

        layout.addWidget(self.service_label)
        layout.addWidget(self.service_input)
        layout.addWidget(self.wait_label)
        layout.addWidget(self.wait_input)
        layout.addWidget(self.wait_after_label)
        layout.addWidget(self.wait_after_input)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_output)

        self.setLayout(layout)
        self.show()

    def start_script(self):
        self.service_name = self.service_input.text()
        try:
            self.wait_time = int(self.wait_input.text())
            self.wait_after_time = int(self.wait_after_input.text())
        except ValueError:
            self.wait_time = 0
            self.wait_after_time = 0

        if not self.service_name or self.wait_time <= 0 or self.wait_after_time < 0:
            logger.error("无效的服务名称或等待时间")
            return

        self.running = True
        self.stop_event.clear()
        self.status_label.setText('状态: 运行中')
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.thread = threading.Thread(target=self.run_script)
        self.thread.start()

    def stop_script(self):
        self.running = False
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join()
        self.status_label.setText('状态: 已停止')
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def run_script(self):
        while not self.stop_event.is_set():
            logger.info(f"启动服务: {self.service_name}")
            self.start_service(self.service_name)

            logger.info(f"等待 {self.wait_time} 秒")
            for _ in range(self.wait_time):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

            logger.info(f"停止服务: {self.service_name}")
            self.stop_service(self.service_name)

            logger.info(f"关闭服务后等待 {self.wait_after_time} 秒")
            for _ in range(self.wait_after_time):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

            logger.info("循环结束，准备开始下一次循环")

    def start_service(self, service_name):
        try:
            subprocess.run(['sc', 'start', service_name], check=True,shell=True)
            logger.info(f"服务 {service_name} 已成功启动")
        except subprocess.CalledProcessError as e:
            logger.error(f"启动服务 {service_name} 时出错: {e}")

    def stop_service(self, service_name):
        try:
            subprocess.run(['sc', 'stop', service_name], check=True,shell=True)
            logger.info(f"服务 {service_name} 已成功停止")
        except subprocess.CalledProcessError as e:
            logger.error(f"停止服务 {service_name} 时出错: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ServiceManager()
    sys.exit(app.exec_())
