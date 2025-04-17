import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

class MinimalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Version Diving - Test")
        self.setGeometry(100, 100, 400, 300)
        
        label = QLabel("Version Diving application test successful!", self)
        label.setGeometry(50, 50, 300, 50)

def main():
    app = QApplication(sys.argv)
    window = MinimalWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 