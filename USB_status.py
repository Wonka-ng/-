import time
import psutil
import threading
import win32api
import win32file
import pywintypes
import wmi
import pythoncom
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout)
from PyQt5.QtCore import Qt

# 监听 USB 设备的插入和拔出
class USBMonitor:
    def __init__(self, log_output):
        self.previous_devices = self.get_usb_devices()
        self.running = False
        self.log_output = log_output

    def get_usb_devices(self):
        pythoncom.CoInitialize()  # 初始化 COM 库
        c = wmi.WMI()
        usb_devices = c.Win32_USBHub()
        devices_info = {}
        for device in usb_devices:
            devices_info[device.DeviceID] = {
                'Name': device.Name,
                'Status': device.Status,
                'Description': device.Description,
                'DeviceID': device.DeviceID,
                'PNPDeviceID': device.PNPDeviceID
            }
        return devices_info

    def monitor_usb(self):
        while self.running:
            current_devices = self.get_usb_devices()
            self.detect_changes(current_devices)
            time.sleep(1)

    def detect_changes(self, current_devices):
        # 检查设备是否插入
        for device_id, device_info in current_devices.items():
            if device_id not in self.previous_devices:
                self.log_output.append(f"USB 设备已插入: {device_info['Name']}")
                self.log_output.append("详细信息:")
                for key, value in device_info.items():
                    self.log_output.append(f"  {key}: {value}")

        # 检查设备是否拔出
        for device_id, device_info in self.previous_devices.items():
            if device_id not in current_devices:
                self.log_output.append(f"USB 设备已拔出: {device_info['Name']}")

        self.previous_devices = current_devices

    def start_monitoring(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_usb)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.running = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join()

# 创建 GUI 界面
class USBMonitorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.usb_monitor = USBMonitor(self.log_output)

    def initUI(self):
        self.setWindowTitle('USB 设备监控器')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.start_button = QPushButton('启动监控', self)
        self.start_button.clicked.connect(self.start_monitoring)

        self.stop_button = QPushButton('停止监控', self)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)

        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)

        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.log_output)

        self.setLayout(layout)
        self.show()

    def start_monitoring(self):
        self.usb_monitor.start_monitoring()
        self.log_output.append("USB 设备监控已启动。")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_monitoring(self):
        self.usb_monitor.stop_monitoring()
        self.log_output.append("USB 设备监控已停止。")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ex = USBMonitorApp()
    sys.exit(app.exec_())
