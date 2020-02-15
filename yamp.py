#!/usr/bin/python3

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from os import path
from os import chmod
from os import remove
from pathlib import Path
from yandex_music import Client
from yandex_music.exceptions import Unauthorized
from yandex_music.exceptions import BadRequest
import sys


class Yamp(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle("yamp")
        self.resize(450, 600)
        self.setMinimumSize(QtCore.QSize(450, 600))
        self.create_ui()
        self.home_dir = f'{Path.home()}'
        self.yamp_auth_token_path = path.join(self.home_dir, '.yamp.token')
        self.auth_email = ''
        self.auth_password = ''

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
        action_close = QtWidgets.QAction("Logout", self)
        menu_file.addAction(action_close)
        action_close.triggered.connect(self.logout)

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
        popup_error = QtWidgets.QMessageBox()
        popup_error.setIcon(QtWidgets.QMessageBox.Critical)
        popup_error.setWindowTitle(message_header)
        popup_error.setText(message)
        popup_error.exec()
        if exit_flag:
            sys.exit(1)

    def show_popup_info(self, message_header, message):
        popup_error = QtWidgets.QMessageBox()
        popup_error.setIcon(QtWidgets.QMessageBox.Information)
        popup_error.setWindowTitle(message_header)
        popup_error.setText(message)
        popup_error.exec()

    def show_auth_dialog(self):
        while self.auth_email == '':
            self.auth_email = QtWidgets.QInputDialog.getText(self, 'Authorisation', 'Input your email', QtWidgets.QLineEdit.Normal, '')[0]
            print(self.auth_email)
        while self.auth_password == '':
            self.auth_password = QtWidgets.QInputDialog.getText(self, 'Authorisation', f'Input password for {self.auth_email}', QtWidgets.QLineEdit.Password, '')[0]

    def read_auth_token_from_file(self):
        if path.isfile(self.yamp_auth_token_path):
            with open(self.yamp_auth_token_path, 'r') as auth_token_file:
                self.auth_token = auth_token_file.read().strip()
                return 1
        else:
            return 0

    # Authorise by credentials or token
    def auth(self):
        if self.read_auth_token_from_file():
            try:
                self.client = Client(self.auth_token)
            except Unauthorized as auth_exception:
                self.show_popup_error('Authorisation error', f'{auth_exception}', 1)
        else:
            self.show_auth_dialog()
            try:
                self.client = Client.from_credentials(self.auth_email, self.auth_password)
                self.save_auth_token_in_file()
            except BadRequest as auth_exception:
                self.show_popup_error('Auth by credentials error', f'{auth_exception}', 1)

    def save_auth_token_in_file(self):
        self.auth_token = self.client['token']
        with open(self.yamp_auth_token_path, 'w') as auth_token_file:
            auth_token_file.write(self.auth_token)
        if path.isfile(self.yamp_auth_token_path):
            chmod(self.yamp_auth_token_path, 0o600)
        else:
            self.show_popup_error('Save token error', 'File with auth token not found', 1)

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

    def logout(self):
        try:
            remove(self.yamp_auth_token_path)
            self.show_popup_info('Logout successful', 'You need restart application for finish logout')
        except Exception as ex:
            self.show_popup_error('Logout error', f'{ex}', 0)


def main():
    app = QtWidgets.QApplication(sys.argv)
    yamp = Yamp()
    yamp.show()
    yamp.auth()
    yamp.make_tracklist()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
