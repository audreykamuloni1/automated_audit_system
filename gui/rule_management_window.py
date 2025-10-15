from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableView, QHeaderView, QMessageBox
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

from db.database import get_all_rules, add_rule, update_rule, delete_rule
from gui.rule_editor_dialog import RuleEditorDialog

class RuleManagementWindow(QMainWindow):
    """A window for viewing, adding, editing, and deleting compliance rules."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rule Management")
        self.setMinimumSize(800, 600)

        # --- Central Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Rules Table ---
        self.rules_table = QTableView()
        self.rules_model = QStandardItemModel()
        self.rules_table.setModel(self.rules_model)
        self.rules_table.setEditTriggers(QTableView.NoEditTriggers)
        self.rules_table.setSelectionBehavior(QTableView.SelectRows)
        self.rules_table.setSortingEnabled(True)
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        main_layout.addWidget(self.rules_table)

        # --- Control Buttons ---
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Rule")
        self.edit_button = QPushButton("Edit Selected Rule")
        self.delete_button = QPushButton("Delete Selected Rule")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        main_layout.addLayout(button_layout)

        # --- Connections ---
        self.add_button.clicked.connect(self.add_new_rule)
        self.edit_button.clicked.connect(self.edit_selected_rule)
        self.delete_button.clicked.connect(self.delete_selected_rule)

        self.load_rules()

    def load_rules(self):
        """Fetches rules from the database and populates the table."""
        self.rules_model.clear()
        headers = ["ID", "Name", "Description", "Target Field", "Operator", "Value", "Active"]
        self.rules_model.setHorizontalHeaderLabels(headers)

        rules_data = get_all_rules()
        for row_data in rules_data:
            items = [QStandardItem(str(field)) for field in row_data]
            # Make the 'Active' status checkable
            items[-1].setCheckable(True)
            items[-1].setCheckState(Qt.Checked if row_data[-1] else Qt.Unchecked)
            self.rules_model.appendRow(items)

        print(f"Loaded {len(rules_data)} rules into the management window.")

    def add_new_rule(self):
        """Opens the rule editor to create a new rule."""
        dialog = RuleEditorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_rule = dialog.get_rule_data()
            success = add_rule(
                name=new_rule['name'],
                description=new_rule['description'],
                target_field=new_rule['target_field'],
                operator=new_rule['operator'],
                value=new_rule['value'],
                is_active=new_rule['is_active']
            )
            if success:
                QMessageBox.information(self, "Success", "New rule added successfully.")
                self.load_rules()
            else:
                QMessageBox.critical(self, "Database Error", "Failed to add the new rule. Check logs for details.")

    def edit_selected_rule(self):
        """Opens the rule editor to modify the selected rule."""
        selected_indexes = self.rules_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "No Selection", "Please select a rule to edit.")
            return

        # Get data for the selected row
        selected_row = selected_indexes[0].row()
        rule_id = int(self.rules_model.item(selected_row, 0).text())

        rule_data = {
            'id': rule_id,
            'name': self.rules_model.item(selected_row, 1).text(),
            'description': self.rules_model.item(selected_row, 2).text(),
            'target_field': self.rules_model.item(selected_row, 3).text(),
            'operator': self.rules_model.item(selected_row, 4).text(),
            'value': self.rules_model.item(selected_row, 5).text(),
            'is_active': self.rules_model.item(selected_row, 6).checkState() == Qt.Checked
        }

        dialog = RuleEditorDialog(self, rule_data=rule_data)
        if dialog.exec_() == QDialog.Accepted:
            updated_rule = dialog.get_rule_data()
            success = update_rule(
                rule_id=updated_rule['id'],
                name=updated_rule['name'],
                description=updated_rule['description'],
                target_field=updated_rule['target_field'],
                operator=updated_rule['operator'],
                value=updated_rule['value'],
                is_active=updated_rule['is_active']
            )
            if success:
                QMessageBox.information(self, "Success", "Rule updated successfully.")
                self.load_rules()
            else:
                QMessageBox.critical(self, "Database Error", "Failed to update the rule.")

    def delete_selected_rule(self):
        """Deletes the selected rule from the database."""
        selected_indexes = self.rules_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "No Selection", "Please select a rule to delete.")
            return

        selected_row = selected_indexes[0].row()
        rule_id = int(self.rules_model.item(selected_row, 0).text())
        rule_name = self.rules_model.item(selected_row, 1).text()

        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f"Are you sure you want to delete the rule '{rule_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if delete_rule(rule_id):
                QMessageBox.information(self, "Success", f"Rule '{rule_name}' deleted successfully.")
                self.load_rules()
            else:
                QMessageBox.critical(self, "Database Error", "Failed to delete the rule.")