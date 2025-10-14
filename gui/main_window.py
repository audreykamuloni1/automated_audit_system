import sys
import os
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QHeaderView, QDialog, QLabel, QFileDialog
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

from rules.rule_engine import get_alerts, run_rules
from gui.rule_management_window import RuleManagementWindow


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
        controls_layout = QHBoxLayout()

        self.manage_rules_button = QPushButton("Manage Rules")
        self.manage_rules_button.clicked.connect(self.open_rule_manager)

        self.run_rules_button = QPushButton("Run Compliance Checks")
        self.run_rules_button.clicked.connect(self.run_compliance_checks)

        self.refresh_button = QPushButton("Refresh Alerts View")
        self.refresh_button.clicked.connect(self.load_alerts)

        self.export_button = QPushButton("Export Alerts to CSV")
        self.export_button.clicked.connect(self.export_alerts_to_csv)

        controls_layout.addWidget(self.manage_rules_button)
        controls_layout.addWidget(self.run_rules_button)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(self.export_button)

        layout.addLayout(controls_layout)

        # --- Alerts Table View ---
        self.alerts_table = QTableView()
        self.alerts_model = QStandardItemModel()
        self.alerts_table.setModel(self.alerts_model)

        # Style the table
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alerts_table.setEditTriggers(QTableView.NoEditTriggers) # Make table read-only
        self.alerts_table.setSelectionBehavior(QTableView.SelectRows)
        self.alerts_table.setSortingEnabled(True)

        layout.addWidget(self.alerts_table)

        # Initial load of alerts
        self.load_alerts()

    def open_rule_manager(self):
        """Opens the rule management window."""
        # We store it as an attribute to prevent it from being garbage collected
        self.rule_window = RuleManagementWindow(self)
        self.rule_window.show()

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
        self.alerts_model.clear() # Clear existing data

        # Set table headers
        headers = ["ID", "Timestamp", "Rule Name", "Description", "User ID", "Action", "Resource"]
        self.alerts_model.setHorizontalHeaderLabels(headers)

        alerts_data = get_alerts()

        if not alerts_data:
            print("No alerts found.")
            return

        for row_data in alerts_data:
            items = [QStandardItem(str(field)) for field in row_data]
            self.alerts_model.appendRow(items)

        print(f"Loaded {len(alerts_data)} alerts into the table.")

    def export_alerts_to_csv(self):
        """Exports the data from the alerts table to a CSV file."""
        if self.alerts_model.rowCount() == 0:
            self.show_message_dialog("Export Error", "There are no alerts to export.")
            return

        # Open file dialog to choose where to save the file
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")

        if not path:
            return # User cancelled the dialog

        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                headers = [self.alerts_model.horizontalHeaderItem(i).text() for i in range(self.alerts_model.columnCount())]
                writer.writerow(headers)

                # Write data rows
                for row in range(self.alerts_model.rowCount()):
                    row_data = [self.alerts_model.item(row, col).text() for col in range(self.alerts_model.columnCount())]
                    writer.writerow(row_data)

            self.show_message_dialog("Export Successful", f"Alerts successfully exported to:\n{path}")
        except Exception as e:
            self.show_message_dialog("Export Error", f"An error occurred while exporting the file:\n{e}")

def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()