from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QDialogButtonBox, QMessageBox
)

class RuleEditorDialog(QDialog):
    """A dialog for creating and editing compliance rules."""

    def __init__(self, parent=None, rule_data=None):
        super().__init__(parent)
        self.setWindowTitle("Rule Editor")
        self.setMinimumWidth(400)

        self.rule_data = rule_data

        # --- Layouts and Widgets ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(80)
        self.target_field_input = QLineEdit()
        self.operator_input = QComboBox()
        self.operator_input.addItems(['=', '!=', '>', '<', 'LIKE', 'IN'])
        self.value_input = QLineEdit()
        self.is_active_checkbox = QCheckBox("Rule is Active")

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Description:", self.description_input)
        form_layout.addRow("Target Field (e.g., 'status'):", self.target_field_input)
        form_layout.addRow("Operator:", self.operator_input)
        form_layout.addRow("Value:", self.value_input)
        form_layout.addRow(self.is_active_checkbox)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

        # If editing, populate fields with existing data
        if self.rule_data:
            self.populate_data()

    def populate_data(self):
        """Fills the form with data from an existing rule."""
        self.name_input.setText(self.rule_data['name'])
        self.description_input.setPlainText(self.rule_data['description'])
        self.target_field_input.setText(self.rule_data['target_field'])
        self.operator_input.setCurrentText(self.rule_data['operator'])
        self.value_input.setText(self.rule_data['value'])
        self.is_active_checkbox.setChecked(self.rule_data['is_active'])

    def get_rule_data(self):
        """Returns the data entered in the form as a dictionary."""
        return {
            'id': self.rule_data.get('id') if self.rule_data else None,
            'name': self.name_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'target_field': self.target_field_input.text().strip(),
            'operator': self.operator_input.currentText(),
            'value': self.value_input.text().strip(),
            'is_active': self.is_active_checkbox.isChecked()
        }

    def accept(self):
        """Overrides the accept method to perform validation before closing."""
        rule_data = self.get_rule_data()
        # Basic validation
        if not all([rule_data['name'], rule_data['target_field'], rule_data['value']]):
            QMessageBox.warning(self, "Validation Error", "Name, Target Field, and Value cannot be empty.")
            return  # Prevent dialog from closing

        super().accept()