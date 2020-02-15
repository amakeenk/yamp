#!/usr/bin/python3

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from configobj import ConfigObj
from os import path
from pathlib import Path
from yandex_music import Client
import sys


class Yamp(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle("yamp")
        self.resize(450, 600)
        self.setMinimumSize(QtCore.QSize(450, 600))
        self.create_ui()
        self.home_dir = f'{Path.home()}'
        self.yamp_home_dir = path.join(self.home_dir, '.yamp')
        self.yamp_auth_config_path = path.join(self.yamp_home_dir, 'auth.cfg')
        self.yamp_auth_token_path = path.join(self.yamp_home_dir, 'auth.token')

    def create_ui(self):
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        # Buttons box
        self.btn_box = QtWidgets.QHBoxLayout()
        self.btn_play = QtWidgets.QPushButton("play")
        self.btn_play.clicked.connect(self.handler_btn_play)
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

        # Menu
        menubar = self.menuBar()
        menu_file = menubar.addMenu("File")
        action_settings = QtWidgets.QAction("Settings", self)
        menu_file.addAction(action_settings)
        action_close = QtWidgets.QAction("Exit", self)
        menu_file.addAction(action_close)
        action_close.triggered.connect(sys.exit)

    # get_current_track_id on double click on track
    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.MouseButtonDblClick and
            event.buttons() == QtCore.Qt.LeftButton and
            source is self.tracklist_table_widget.viewport()):
            item = self.tracklist_table_widget.itemAt(event.pos())
            if item is not None:
                print(self.get_current_track_id())
        return super(QtWidgets.QMainWindow, self).eventFilter(source, event)

    def show_popup_error(self, message_header, message, exit_flag):
        reply = QtWidgets.QMessageBox.critical(self, message_header, message)
        if reply and exit_flag:
            sys.exit(1)

    def check_auth_credentials(self):
        if path.isfile(self.yamp_auth_config_path):
            self.yamp_auth_config = ConfigObj(self.yamp_auth_config_path)
            try:
                self.auth_email = self.yamp_auth_config['email']
                self.auth_password = self.yamp_auth_config['password']
                return 1
            except KeyError:
                self.show_popup_error('Auth error', 'Authorisation credentials is invalid!', 1)
        else:
            self.show_popup_error('Auth error', f'yamp config {self.yamp_auth_config_path} not found', 1)

    def read_auth_token(self):
        if path.isfile(self.yamp_auth_token_path):
            with open(self.yamp_auth_token_path, 'r') as auth_token_file:
                self.auth_token = auth_token_file.read().strip()
                return 1
        else:
            return 0

    # Authorise by credentials or token
    def auth(self):
        if self.check_auth_credentials() and not self.read_auth_token():
            self.client = Client.from_credentials(self.auth_email, self.auth_password)
        elif self.read_auth_token():
            self.client = Client(self.auth_token)

    # Fetch list of like tracks
    def fetch_like_tracks(self,):
        tracks_ids = self.client.users_likes_tracks().tracks_ids
        self.like_tracks = self.client.tracks(tracks_ids)

    # Fill TableWidget by like tracks
    def make_tracklist(self):
        self.fetch_like_tracks()
        self.tracklist_table_widget.setRowCount(len(self.like_tracks))
        row = 0
        for track in self.like_tracks:
            t_id = track['id']
            t_name = track['title']
            t_artists = track['artists']
            if t_artists:
                t_artist = t_artists[0]['name']
                t_full_name = f'{t_artist} - {t_name}'
            else:
                t_full_name = t_name
            col_1 = QtWidgets.QTableWidgetItem(t_full_name)
            col_2 = QtWidgets.QTableWidgetItem(str(t_id))
            col_1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.tracklist_table_widget.setItem(row, 0, col_1)
            self.tracklist_table_widget.setItem(row, 1, col_2)
            row += 1

    # Get track id of current selected row
    def get_current_track_id(self):
        selected_row = self.tracklist_table_widget.currentRow()
        track_id = self.tracklist_table_widget.item(selected_row, 1).text()
        return track_id

    # Action for click on play button
    def handler_btn_play(self):
        track_id = self.get_current_track_id()
        print(track_id)


def main():
    app = QtWidgets.QApplication(sys.argv)
    yamp = Yamp()
    yamp.show()
    yamp.auth()
    yamp.make_tracklist()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
