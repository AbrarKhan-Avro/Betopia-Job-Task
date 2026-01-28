import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog,
    QTextEdit, QLabel, QHBoxLayout, QProgressBar, QTableWidget,
    QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QColor
from excel_utils import load_excel, save_excel
from bot import FormBot


# Background Worker Thread

class BotWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int, int)
    finished_signal = Signal()

    def __init__(self, df, file_path):
        super().__init__()
        self.df = df
        self.file_path = file_path
        self._paused = False
        self._stopped = False

        # TRACKER: count already-success rows
        self.completed = int((df["Status"].str.lower() == "success").sum())

    def run(self):
        bot = FormBot(log_callback=self.log_signal.emit)
        total = len(self.df)

        for i, row in self.df.iterrows():
            if self._stopped:
                self.log_signal.emit("🛑 Batch stopped by user")
                break

            # TRACKER: skip already successful rows
            if str(row.get("Status", "")).strip().lower() == "success":
                self.progress_signal.emit(self.completed, total)
                continue

            while self._paused:
                self.msleep(300)

            try:
                self.log_signal.emit(f"➡ Processing record {i+1}")
                bot.open_form()
                bot.fill_form(row)
                bot.wait_for_captcha_and_submit()

                self.df.at[i, "Status"] = "Success"
                self.completed += 1
                save_excel(self.df, self.file_path)

                self.log_signal.emit(f"✅ Record {i+1} completed")

            except Exception as e:
                self.df.at[i, "Status"] = "Failed"
                self.df.at[i, "ErrorMessage"] = str(e)
                save_excel(self.df, self.file_path)

                self.log_signal.emit(f"❌ Record {i+1} failed: {e}")

            self.progress_signal.emit(self.completed, total)

        bot.close()
        self.finished_signal.emit()

    def pause(self):
        self._paused = True
        self.log_signal.emit("⏸ Bot paused")

    def resume(self):
        self._paused = False
        self.log_signal.emit("▶ Bot resumed")

    def stop(self):
        self._stopped = True


# Main UI Application

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Batch Automation Bot PRO")
        self.resize(900, 600)

        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        control_layout = QHBoxLayout()

        self.label = QLabel("No file selected")

        self.btn_load = QPushButton("📂 Select Excel File")
        self.btn_start = QPushButton("🚀 Start Batch")
        self.btn_pause = QPushButton("⏸ Pause / Resume")
        self.btn_stop = QPushButton("🛑 Stop")

        self.progress = QProgressBar()
        self.progress_label = QLabel("0 / 0 completed")

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        self.table = QTableWidget()

        top_layout.addWidget(self.label)
        top_layout.addWidget(self.btn_load)

        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_pause)
        control_layout.addWidget(self.btn_stop)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table)
        main_layout.addWidget(self.progress)
        main_layout.addWidget(self.progress_label)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.log)

        self.setLayout(main_layout)

        self.btn_load.clicked.connect(self.load_file)
        self.btn_start.clicked.connect(self.start_bot)
        self.btn_pause.clicked.connect(self.pause_bot)
        self.btn_stop.clicked.connect(self.stop_bot)

        self.worker = None

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel", "", "Excel Files (*.xlsx)")
        if path:
            self.file_path = path
            self.df = load_excel(path)

            if "Status" not in self.df.columns:
                self.df["Status"] = "Pending"
            if "ErrorMessage" not in self.df.columns:
                self.df["ErrorMessage"] = ""

            self.label.setText(f"Loaded: {path}")
            self.populate_table()
            self.log.append("✅ Excel file loaded")

    def populate_table(self):
        self.table.setRowCount(len(self.df))
        self.table.setColumnCount(len(self.df.columns))
        self.table.setHorizontalHeaderLabels(self.df.columns)

        for row_idx, row in self.df.iterrows():
            status = row.get("Status", "")
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                if status == "Success":
                    item.setBackground(QColor(200, 255, 200))
                elif status == "Failed":
                    item.setBackground(QColor(255, 200, 200))
                self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()

    def start_bot(self):
        if not hasattr(self, "df"):
            QMessageBox.warning(self, "No File", "Please load an Excel file first")
            return

        self.progress.setValue(0)
        self.log.append("🚀 Starting automation...")

        self.worker = BotWorker(self.df, self.file_path)
        self.worker.log_signal.connect(self.log.append)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.bot_finished)
        self.worker.start()

    def update_progress(self, completed, total):
        percent = int((completed / total) * 100)
        self.progress.setValue(percent)
        self.progress_label.setText(f"{completed} / {total} completed")
        self.populate_table()

    def bot_finished(self):
        self.log.append("🎉 Batch processing finished")
        self.populate_table()

    def pause_bot(self):
        if self.worker:
            if self.worker._paused:
                self.worker.resume()
            else:
                self.worker.pause()

    def stop_bot(self):
        if self.worker:
            self.worker.stop()
            self.log.append("🛑 Stop command sent")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
