from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView,
    QProgressBar, QLabel, QHeaderView
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

class AnomalyPanel(QWidget):
    """
    A widget for the anomaly detection part of the application.
    Contains controls to run the ML model and a table to display results.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Layouts ---
        main_layout = QVBoxLayout(self)
        controls_layout = QHBoxLayout()

        # --- Widgets ---
        self.run_button = QPushButton("Train Model & Detect Anomalies")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False) # Hidden by default
        self.status_label = QLabel("Ready")

        self.results_table = QTableView()
        self.results_model = QStandardItemModel()
        self.results_table.setModel(self.results_model)
        self.results_table.setEditTriggers(QTableView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableView.SelectRows)
        self.results_table.setSortingEnabled(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # --- Layout Setup ---
        controls_layout.addWidget(self.run_button)
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch()

        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(QLabel("Detected Anomalies:"))
        main_layout.addWidget(self.results_table)

        self.setup_table_headers()

    def setup_table_headers(self):
        """Initializes the headers for the results table."""
        headers = ["ID", "Timestamp", "User ID", "Action", "Resource", "Score", "Details"]
        self.results_model.setHorizontalHeaderLabels(headers)

    def clear_results(self):
        """Clears the results table."""
        self.results_model.removeRows(0, self.results_model.rowCount())

    def populate_results(self, anomalies_data):
        """
        Fills the results table with anomaly data.

        Args:
            anomalies_data (list): A list of tuples, where each tuple is an anomaly record.
        """
        self.clear_results()
        for row_data in anomalies_data:
            items = [QStandardItem(str(field)) for field in row_data]
            self.results_model.appendRow(items)
        print(f"GUI: Displayed {len(anomalies_data)} anomalies.")

    def set_status(self, message, is_busy=False):
        """
        Updates the status label and progress bar visibility.

        Args:
            message (str): The text to display in the status label.
            is_busy (bool): If True, shows the progress bar in busy mode.
        """
        self.status_label.setText(message)
        self.progress_bar.setVisible(is_busy)
        if is_busy:
            self.progress_bar.setRange(0, 0) # Indeterminate progress bar
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)

        self.run_button.setEnabled(not is_busy)