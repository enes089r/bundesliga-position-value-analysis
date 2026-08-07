import sys

from PySide6.QtWidgets import QApplication

from app.database import Database
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    db = Database()
    window = MainWindow(db)
    window.show()
    exit_code = app.exec()
    db.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
