from .yamp import Yamp
from PyQt5 import QtWidgets
import sys


def main():
    app = QtWidgets.QApplication(sys.argv)
    yamp = Yamp()
    yamp.show()
    yamp.auth()
    yamp.make_tracklist()
    yamp.fill_tracklist_table()
    yamp.create_cache_dir()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
