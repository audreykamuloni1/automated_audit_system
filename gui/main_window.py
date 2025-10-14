import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout,
    QWidget, QPushButton, QHeaderView, QDialog, QLabel
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

from rules.rule_engine import get_alerts, run_rules

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Intelligent Audit System - Dashboard")
        self.setGeometry(100, 100, 1200, 800)

        # --- Central Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- Control Buttons ---
        controls_layout = QVBoxLayout()

        self.run_rules_button = QPushButton("1. Run Compliance Checks")
        self.run_rules_button.clicked.connect(self.run_compliance_checks)

        self.refresh_button = QPushButton("2. Refresh Alerts View")
        self.refresh_button.clicked.connect(self.load_alerts)

        controls_layout.addWidget(self.run_rules_button)
        controls_layout.addWidget(self.refresh_button)

        layout.addLayout(controls_layout)

        # --- Alerts Table View ---
        self.alerts_table = QTableView()
        self.alerts_model = QStandardItemModel()
        self.alerts_table.setModel(self.alerts_model)

        # Set table headers
        headers = ["ID", "Timestamp", "Rule ID", "Description", "User ID", "Action", "Resource"]
        self.alerts_model.setHorizontalHeaderLabels(headers)

        # Style the table
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alerts_table.setEditTriggers(QTableView.NoEditTriggers) # Make table read-only
        self.alerts_table.setSelectionBehavior(QTableView.SelectRows)
        self.alerts_table.setSortingEnabled(True)

        layout.addWidget(self.alerts_table)

        # Initial load of alerts
        self.load_alerts()

    def show_message_dialog(self, title, message):
        """Helper function to show a simple message box."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(message))
        dialog.setLayout(layout)
        dialog.exec_()

    def run_compliance_checks(self):
        """Handler for the 'Run Compliance Checks' button."""
        print("Running compliance checks from GUI...")
        run_rules()
        self.show_message_dialog("Rule Engine", "Compliance checks are complete. Refresh the view to see new alerts.")
        self.load_alerts() # Automatically refresh after running

    def load_alerts(self):
        """Fetches alerts from the database and populates the table."""
        print("Loading alerts into GUI...")
        self.alerts_model.removeRows(0, self.alerts_model.rowCount()) # Clear existing data

        alerts_data = get_alerts()

        if not alerts_data:
            print("No alerts found.")
            return

        for row_data in alerts_data:
            items = [QStandardItem(str(field)) for field in row_data]
            self.alerts_model.appendRow(items)

        print(f"Loaded {len(alerts_data)} alerts into the table.")

def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()