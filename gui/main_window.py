import sys
import os
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QHeaderView, QDialog, QLabel, QFileDialog, QTabWidget
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QThread

from rules.rule_engine import get_alerts, run_rules
from gui.rule_management_window import RuleManagementWindow
from gui.anomaly_panel import AnomalyPanel
from ml.ml_worker import MLWorker
from ml.anomaly_detector import get_anomalies


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Intelligent Audit System")
        self.setGeometry(100, 100, 1200, 800)

        # --- Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Tab Widget for different sections ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Tab 1: Rule-Based Alerts ---
        self.alerts_tab = QWidget()
        alerts_layout = QVBoxLayout(self.alerts_tab)
        self.tabs.addTab(self.alerts_tab, "Rule-Based Alerts")

        # Controls for Alerts Tab
        alerts_controls_layout = QHBoxLayout()
        self.manage_rules_button = QPushButton("Manage Rules")
        self.run_rules_button = QPushButton("Run Compliance Checks")
        self.refresh_alerts_button = QPushButton("Refresh Alerts View")
        self.export_alerts_button = QPushButton("Export Alerts to CSV")
        alerts_controls_layout.addWidget(self.manage_rules_button)
        alerts_controls_layout.addWidget(self.run_rules_button)
        alerts_controls_layout.addWidget(self.refresh_alerts_button)
        alerts_controls_layout.addWidget(self.export_alerts_button)
        alerts_layout.addLayout(alerts_controls_layout)

        # Table for Alerts
        self.alerts_table = QTableView()
        self.alerts_model = QStandardItemModel()
        self.alerts_table.setModel(self.alerts_model)
        self.style_table(self.alerts_table)
        alerts_layout.addWidget(self.alerts_table)

        # --- Tab 2: Anomaly Detection ---
        self.anomaly_tab = AnomalyPanel()
        self.tabs.addTab(self.anomaly_tab, "ML Anomaly Detection")

        # --- Initial Load and Connections ---
        self.load_alerts()
        self.load_anomalies() # Load existing anomalies on startup
        self.connect_signals()

    def style_table(self, table):
        """Applies common styling to a QTableView."""
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableView.NoEditTriggers)
        table.setSelectionBehavior(QTableView.SelectRows)
        table.setSortingEnabled(True)

    def connect_signals(self):
        """Connects all the application's signals to their slots."""
        # Rule-based alert signals
        self.manage_rules_button.clicked.connect(self.open_rule_manager)
        self.run_rules_button.clicked.connect(self.run_compliance_checks)
        self.refresh_alerts_button.clicked.connect(self.load_alerts)
        self.export_alerts_button.clicked.connect(self.export_alerts_to_csv)

        # Anomaly detection signals
        self.anomaly_tab.run_button.clicked.connect(self.start_ml_worker)

    def start_ml_worker(self):
        """
        Initializes and starts the MLWorker in a new thread.
        """
        self.thread = QThread()
        self.worker = MLWorker()
        self.worker.moveToThread(self.thread)

        # Connect worker signals to GUI slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.progress.connect(lambda msg: self.anomaly_tab.set_status(msg, is_busy=True))
        self.worker.results_ready.connect(self.on_ml_results_ready)

        # Start the thread
        self.thread.start()

        # Update GUI to show it's busy
        self.anomaly_tab.set_status("Starting ML pipeline...", is_busy=True)

    def on_ml_results_ready(self, results):
        """
        Slot to handle the results from the ML worker.

        Args:
            results (list): The list of anomalies detected by the model.
        """
        self.anomaly_tab.populate_results(results)
        self.anomaly_tab.set_status(f"Analysis complete. Found {len(results)} anomalies.", is_busy=False)

    def open_rule_manager(self):
        """Opens the rule management window."""
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
        self.load_alerts()

    def load_alerts(self):
        """Fetches alerts from the database and populates the table."""
        print("Loading alerts into GUI...")
        self.alerts_model.clear()
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

    def load_anomalies(self):
        """Fetches anomalies from the database and populates the anomaly table."""
        print("Loading anomalies into GUI...")
        anomalies_data = get_anomalies()
        self.anomaly_tab.populate_results(anomalies_data)

    def export_alerts_to_csv(self):
        """Exports the data from the alerts table to a CSV file."""
        if self.alerts_model.rowCount() == 0:
            self.show_message_dialog("Export Error", "There are no alerts to export.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")

        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                headers = [self.alerts_model.horizontalHeaderItem(i).text() for i in range(self.alerts_model.columnCount())]
                writer.writerow(headers)
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