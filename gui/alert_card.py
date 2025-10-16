from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class AlertCard(QFrame):
    """
    A custom widget to display a single security alert in a card-like format.
    """
    SEVERITY_COLORS = {
        "High": "#e74c3c",    # Red
        "Medium": "#f7b731",  # Yellow
        "Low": "#2ecc71",     # Green
        "Info": "#3498db"     # Blue
    }

    def __init__(self, severity, alert_type, description, timestamp, log_id, parent=None):
        super().__init__(parent)
        self.setObjectName("AlertCard")

        # --- Card Properties ---
        self.severity = severity
        self.alert_type = alert_type
        self.description = description
        self.timestamp = timestamp
        self.log_id = log_id

        self.init_ui()

    def init_ui(self):
        """Initializes the user interface of the card."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # --- Header ---
        header_layout = QHBoxLayout()

        severity_label = QLabel(f"▲ {self.severity} Severity")
        severity_font = QFont()
        severity_font.setBold(True)
        severity_label.setFont(severity_font)

        type_label = QLabel(self.alert_type)
        type_label.setObjectName("AlertTypeLabel")
        type_label.setAlignment(Qt.AlignRight)

        header_layout.addWidget(severity_label)
        header_layout.addWidget(type_label)

        # --- Body ---
        description_label = QLabel(self.description)
        description_label.setWordWrap(True)

        # --- Footer ---
        footer_label = QLabel(f"{self.timestamp} | Log ID: {self.log_id}")
        footer_label.setObjectName("FooterLabel")
        footer_label.setStyleSheet("color: #808080;") # Muted color for footer

        main_layout.addLayout(header_layout)
        main_layout.addWidget(description_label)
        main_layout.addWidget(footer_label)

        self.set_style()

    def set_style(self):
        """Sets the card's style based on its severity."""
        border_color = self.SEVERITY_COLORS.get(self.severity, "#ffffff")

        # This dynamic styling is powerful. The border color changes per card.
        self.setStyleSheet(f"""
            #AlertCard {{
                background-color: #2e2e4f;
                border-radius: 5px;
                border-left: 5px solid {border_color};
            }}
            #AlertTypeLabel {{
                background-color: #1a1a2e;
                color: #f0f0f0;
                padding: 2px 5px;
                border-radius: 3px;
                font-size: 11px;
            }}
        """)

if __name__ == '__main__':
    # Example of how to use the AlertCard
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    main_widget = QWidget()
    layout = QVBoxLayout(main_widget)

    card1 = AlertCard("High", "ML-Based", "Unusually large data export (500MB) by user 'joe' for 'customer_data_Q4_large.zip'.", "10/27/2023, 12:02:48 PM", "5b7c9e1f-2a3c-4d5e-9fb0-1c2a3d4e5f6b")
    card2 = AlertCard("Medium", "Rule-Based", "Guest account attempted to access sensitive system file /etc/shadow.", "10/27/2023, 12:02:25 PM", "3d5e7a9b-8c1f-4e2a-8b5c-9f0e1d2c4b6a")

    layout.addWidget(card1)
    layout.addWidget(card2)

    main_widget.setStyleSheet("background-color: #1a1a2e;")
    main_widget.show()

    sys.exit(app.exec_())