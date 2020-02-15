from PyQt5 import QtWidgets
from PyQt5 import QtCore
import sys


class Yamp(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle("yamp")
        self.resize(450, 600)
        self.setMinimumSize(QtCore.QSize(450, 600))
        self.create_ui()

    def create_ui(self):
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        # Buttons box
        self.btn_box = QtWidgets.QHBoxLayout()
        self.btn_play = QtWidgets.QPushButton("play")
        self.btn_box.addWidget(self.btn_play)
        self.btn_prev = QtWidgets.QPushButton("prev")
        self.btn_box.addWidget(self.btn_prev)
        self.btn_pause = QtWidgets.QPushButton("pause")
        self.btn_box.addWidget(self.btn_pause)
        self.btn_next = QtWidgets.QPushButton("next")
        self.btn_box.addWidget(self.btn_next)
        self.btn_stop = QtWidgets.QPushButton("stop")
        self.btn_box.addWidget(self.btn_stop)

        # Sliders box
        self.slider_box = QtWidgets.QHBoxLayout()
        self.slider_volume = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_volume.setMaximum(100)
        self.slider_volume.setToolTip("Volume")
        self.slider_box.addWidget(self.slider_volume)
        self.slider_position = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_position.setToolTip("Position")
        self.slider_position.setMaximum(1000)
        self.slider_box.addWidget(self.slider_position)

        # TableWidget for tracklist
        self.tracklist_table_widget = QtWidgets.QTableWidget()
        self.tracklist_table_widget.setObjectName("tracklist_table_widget")
        self.tracklist_table_widget.setColumnCount(2)
        self.tracklist_table_widget.setRowCount(0)
        self.tracklist_table_widget.setColumnHidden(1, True)
        self.tracklist_table_widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tracklist_table_widget.viewport().installEventFilter(self)
        self.tracklist_table_header = self.tracklist_table_widget.horizontalHeader()
        self.tracklist_table_header.hide()
        self.tracklist_table_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        # Set layout
        self.layout_box = QtWidgets.QVBoxLayout()
        self.layout_box.addLayout(self.btn_box)
        self.layout_box.addWidget(self.tracklist_table_widget)
        self.layout_box.addLayout(self.slider_box)
        self.widget.setLayout(self.layout_box)

        menubar = self.menuBar()
        menu_file = menubar.addMenu("File")
        action_settings = QtWidgets.QAction("Settings", self)
        menu_file.addAction(action_settings)
        action_close = QtWidgets.QAction("Exit", self)
        menu_file.addAction(action_close)
        action_close.triggered.connect(sys.exit)

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.MouseButtonDblClick and event.buttons() == QtCore.Qt.LeftButton and source is self.tracklist_table_widget.viewport()):
            item = self.tracklist_table_widget.itemAt(event.pos())
            if item is not None:
                print(get_current_track_id(self.tracklist_table_widget))
        return super(QtWidgets.QMainWindow, self).eventFilter(source, event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    yamp = Yamp()
    yamp.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
