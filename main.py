# Dev: Vaka (https://t.me/Vakaefy)

import sys
import subprocess
import psutil
import time
import a2s
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QGridLayout, QFrame, QProgressBar
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

tries = 0
wait_time = 0

cfg_path = 'config.json'
try:
    with open(cfg_path, 'r') as f:
        cfg = json.load(f)
except Exception as e:
    print(f"CfgErr: {e}")
    sys.exit(1)

ip = cfg.get('server_ip', '127.0.0.1')
port = cfg.get('server_port', 27015)
bin_path = cfg.get('srcds_path', '')
args = cfg.get('srcds_args', [])
interval = cfg.get('check_interval', 30)
fail_cap = cfg.get('max_fails', 3)
reset_hour = cfg.get('auto_restart_hour', 3)

debug_mode = '--test' in sys.argv

def log_debug(x):
    if debug_mode:
        print(f"[dbg] {x}")

def ping_server():
    try:
        return a2s.info((ip, port))
    except:
        return None

def grab_pid():
    for proc in psutil.process_iter(['pid','name']):
        if proc.info['name'] == 'srcds.exe':
            return proc.pid
    return None

def end_proc():
    pid = grab_pid()
    if pid:
        psutil.Process(pid).kill()

def boot_proc():
    if not debug_mode:
        subprocess.Popen([bin_path] + args)

def time_left():
    now = datetime.now()
    tgt = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
    if tgt <= now:
        tgt += timedelta(days=1)
    return tgt

class InitSplash(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(480, 280)
        geom = QApplication.primaryScreen().geometry()
        self.move((geom.width() - self.width()) // 2, (geom.height() - self.height()) // 2)
        self.setStyleSheet("background-color: #1F1B24; border-radius: 20px;")
        self.label = QLabel("GPanel - Starting up...", self)
        self.label.setStyleSheet("color: #ECEFF1;")
        self.label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status = QLabel("Initializing...", self)
        self.status.setStyleSheet("color: #ECEFF1;")
        self.status.setFont(QFont("Segoe UI", 13))
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar(self)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setStyleSheet(
            "QProgressBar{background-color:#2c2c2c;border-radius:10px;height:14px;}"
            "QProgressBar::chunk{background-color:#BB86FC;border-radius:10px;}"
        )
        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.label)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addStretch()
        self.show()

    def update_status(self, txt, val):
        self.status.setText(txt)
        self.progress.setValue(val)
        QApplication.processEvents()

class MainBox(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPanel - by Vaka")
        self.setFixedSize(860, 540)
        geom = QApplication.primaryScreen().geometry()
        self.move((geom.width() - self.width()) // 2, (geom.height() - self.height()) // 2)
        self.setStyleSheet("background-color: #121212;")

        self.title = QLabel("GPanel", self)
        self.title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.title.setStyleSheet("color: #BB86FC; text-decoration: none;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dev = QLabel("Developer: Vaka", self)
        dev.setFont(QFont("Segoe UI", 10))
        dev.setStyleSheet("color: rgba(255,255,255,0.12); text-decoration: none;")
        dev.setAlignment(Qt.AlignmentFlag.AlignCenter)

        panel = QFrame(self)
        panel.setStyleSheet("background-color: rgba(255,255,255,0.05); border-radius: 12px;")
        grid = QGridLayout(panel)
        grid.setContentsMargins(20,20,20,20)
        grid.setHorizontalSpacing(40)
        grid.setVerticalSpacing(15)
        lbls = ["Status:", "Server Name:", "Map:", "Players:", "Ping:"]
        self.vals = []
        for i, t in enumerate(lbls):
            lbl = QLabel(t)
            lbl.setFont(QFont("Segoe UI",14))
            lbl.setStyleSheet("color: #ECEFF1; text-decoration: none; background: transparent; border: none;")
            grid.addWidget(lbl, i, 0, alignment=Qt.AlignmentFlag.AlignRight)

            val = QLabel("---")
            val.setFont(QFont("Segoe UI",14,QFont.Weight.DemiBold))
            val.setStyleSheet("color: #FFFFFF; text-decoration: none; background: transparent; border: none;")
            grid.addWidget(val, i, 1)
            self.vals.append(val)

        self.status_label, self.name_label, self.map_label, self.players_label, self.ping_label = self.vals

        self.restart_btn = QPushButton("Restart Server", self)
        self.restart_btn.setFont(QFont("Segoe UI",12,QFont.Weight.Bold))
        self.restart_btn.setStyleSheet(
            "QPushButton{background-color:#BB86FC;color:#121212;padding:12px;border-radius:8px; margin-top: 20px;}"
            "QPushButton:hover{background-color:#9A67EA;}"
        )
        self.restart_btn.clicked.connect(self.manual_restart)

        self.retry_note = QLabel("", self)
        self.retry_note.setStyleSheet("color: #FFB74D; text-decoration: none; background: transparent; border: none;")
        self.clock_now = QLabel("", self)
        self.clock_now.setFont(QFont("Segoe UI",10))
        self.clock_now.setStyleSheet("color: #ECEFF1; text-decoration: none; background: transparent; border: none;")
        self.clock_now.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.restart_timer = QLabel("", self)
        self.restart_timer.setFont(QFont("Segoe UI",10))
        self.restart_timer.setStyleSheet("color: #ECEFF1; text-decoration: none; background: transparent; border: none;")
        self.restart_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(dev)
        layout.addWidget(panel)
        layout.addWidget(self.restart_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.retry_note, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.clock_now)
        layout.addWidget(self.restart_timer)
        layout.setSpacing(10)


        self.worker = FeedWatch()
        self.worker.status_signal.connect(self.status_recv)
        self.worker.name_signal.connect(lambda s: self.name_label.setText(s))
        self.worker.map_signal.connect(lambda m: self.map_label.setText(m))
        self.worker.players_signal.connect(lambda p: self.players_label.setText(p))
        self.worker.ping_signal.connect(lambda p: self.ping_label.setText(p))
        self.worker.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def status_recv(self, txt, col):
        global tries, wait_time
        if txt == "NO RESPONSE":
            tries += 1
            wait_time = interval
            col = QColor("#CF6679")
        else:
            tries = 0
            self.retry_note.setText("")
            col = QColor("#03DAC6")
        self.status_label.setText(txt)
        self.status_label.setStyleSheet(f"color: {col.name()}; font-weight:bold; font-size:16px; background: transparent; border: none; text-decoration: none;")

    def tick(self):
        global wait_time
        now = datetime.now().strftime('%H:%M:%S')
        self.clock_now.setText(f"Current Time: {now}")
        rest = time_left() - datetime.now()
        self.restart_timer.setText(f"Auto-restart in: {str(rest).split('.')[0]}")
        if wait_time > 0:
            wait_time -= 1
            self.retry_note.setText(f"Attempts: {tries} | Next in {wait_time}s")

    def manual_restart(self):
        end_proc()
        boot_proc()
        log_debug("Manual restart")

class FeedWatch(QThread):
    status_signal = pyqtSignal(str, QColor)
    name_signal = pyqtSignal(str)
    map_signal = pyqtSignal(str)
    players_signal = pyqtSignal(str)
    ping_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.err_count = 0

    def run(self):
        while True:
            result = ping_server()
            if result:
                self.err_count = 0
                self.status_signal.emit("ONLINE", QColor("#03DAC6"))
                self.name_signal.emit(result.server_name)
                self.map_signal.emit(result.map_name)
                self.players_signal.emit(f"{result.player_count}/{result.max_players}")
                self.ping_signal.emit(f"{result.ping*1000:.0f} ms")
            else:
                self.err_count += 1
                self.status_signal.emit("NO RESPONSE", QColor("#CF6679"))
                if self.err_count >= fail_cap:
                    end_proc()
                    boot_proc()
                    self.err_count = 0
            time.sleep(interval)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = InitSplash()
    steps = ["Checking server...", "Starting server...", "Waiting service...", "Launching UI..."]
    for i, msg in enumerate(steps):
        splash.update_status(msg, int((i + 1) / len(steps) * 100))
        time.sleep(0.6)
    if not grab_pid() and not debug_mode:
        boot_proc()
        time.sleep(2)
    splash.close()
    ui = MainBox()
    ui.show()
    sys.exit(app.exec())
