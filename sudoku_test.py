from PyQt5.QtWidgets import QApplication
import sys
from sudoku_game import SudokuOyunu

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = SudokuOyunu()
    pencere.show()
    sys.exit(app.exec_())