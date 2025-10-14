import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def start_app():
    """
    Initializes and runs the PyQt5 application.
    """
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    start_app()