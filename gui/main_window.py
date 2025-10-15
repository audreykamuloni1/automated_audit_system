import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QTableView, QSplitter, QFrame, QHeaderView, QScrollArea, QPushButton
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

from db import get_all_logs, get_unified_alerts
from gui.alert_card import AlertCard


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Server Anomaly Detection Dashboard")
        self.setGeometry(100, 100, 1600, 900)

        # Load the stylesheet
        try:
            with open("gui/stylesheet.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Stylesheet not found. Using default styles.")

        # --- Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Header ---
        header = QWidget()
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header.setObjectName("Header")

        title = QLabel("Server Anomaly Detection Dashboard")
        title_font = title.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)

        self.refresh_button = QPushButton("⟳ Refresh")
        self.refresh_button.setFixedWidth(120)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_button)
        main_layout.addWidget(header)

        # --- Body (Splitter Layout) ---
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Horizontal)

        # --- Left Pane: Real-Time Access Logs ---
        logs_container = QFrame()
        logs_layout = QVBoxLayout(logs_container)
        logs_layout.addWidget(QLabel("Real-Time Access Logs"))
        self.logs_table = QTableView()
        self.logs_model = QStandardItemModel()
        self.logs_table.setModel(self.logs_model)
        logs_layout.addWidget(self.logs_table)

        # --- Right Pane: Security Alerts ---
        alerts_container = QFrame()
        alerts_container_layout = QVBoxLayout(alerts_container)
        alerts_container_layout.addWidget(QLabel("Security Alerts"))

        # Scroll Area for alert cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.alerts_layout = QVBoxLayout(self.scroll_content)
        self.alerts_layout.setAlignment(Qt.AlignTop)
        self.alerts_layout.setSpacing(10)

        self.scroll_area.setWidget(self.scroll_content)
        alerts_container_layout.addWidget(self.scroll_area)

        splitter.addWidget(logs_container)
        splitter.addWidget(alerts_container)
        splitter.setSizes([1000, 600]) # Initial size ratio

        body_layout.addWidget(splitter)
        main_layout.addWidget(body_widget)

        self.connect_signals()
        self.load_initial_data()

    def connect_signals(self):
        """Connects signals to slots."""
        self.refresh_button.clicked.connect(self.load_initial_data)

    def load_initial_data(self):
        """Loads all necessary data on startup."""
        print("Refreshing all data...")
        self.load_logs_into_table()
        self.load_alerts_into_cards()

    def load_logs_into_table(self):
        """Fetches all logs and populates the left-hand table."""
        self.logs_model.clear()
        headers = ["Status", "Timestamp", "User", "Source IP", "Action"]
        self.logs_model.setHorizontalHeaderLabels(headers)

        logs_data = get_all_logs()
        for row_data in logs_data:
            items = [QStandardItem(str(field)) for field in row_data]
            self.logs_model.appendRow(items)

        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.resizeColumnsToContents()

    def load_alerts_into_cards(self):
        """Fetches unified alerts and populates the right-hand panel with AlertCard widgets."""
        # Clear existing cards
        for i in reversed(range(self.alerts_layout.count())):
            widget = self.alerts_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        unified_alerts = get_unified_alerts()

        if not unified_alerts:
            self.alerts_layout.addWidget(QLabel("No security alerts found."))
            return

        for alert_data in unified_alerts:
            card = AlertCard(
                severity=alert_data['severity'],
                alert_type=alert_data['type'],
                description=alert_data['description'],
                timestamp=str(alert_data['timestamp']),
                log_id=alert_data['id']
            )
            self.alerts_layout.addWidget(card)

def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()