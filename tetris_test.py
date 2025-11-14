from PyQt5.QtWidgets import QApplication
import sys
from tetris_game import TetrisOyunu 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = TetrisOyunu()
    pencere.show()
    sys.exit(app.exec_())