#!/usr/bin/python3

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from os import path
from os import chmod
from os import remove
from os import mkdir
from time import strftime
from time import gmtime
from pathlib import Path
from tempfile import gettempdir
from yandex_music import Client
from yandex_music.exceptions import Unauthorized
from yandex_music.exceptions import BadRequest
import sys
import vlc


class Yamp(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle('yamp')
        self.resize(450, 600)
        self.setMinimumSize(QtCore.QSize(450, 600))
        self.yamp_auth_token_path = path.join(f'{Path.home()}', '.yamp.token')
        self.yamp_cache_dir = path.join(f'{Path.home()}', '.cache/yamp')
        self.auth_email = ''
        self.auth_password = ''
        self.vlc_instance = vlc.Instance()
        self.vlc_media_player = self.vlc_instance.media_player_new()
        self.vlc_media = None
        self.vlc_is_paused = False
        self.cur_track_duration = 0
        self.cur_track_id = None
        self.cur_track_name = None
        self.cur_track_artist = None
        self.tracklist = []
        self.change_volume(50)
        self.create_ui()

    def create_ui(self):
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)
        self.app_style = QtWidgets.QApplication.style()

        # Buttons box
        self.btn_box = QtWidgets.QHBoxLayout()
        self.btn_play = QtWidgets.QPushButton()
        self.btn_play.setIcon(self.app_style.standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.btn_play.clicked.connect(self.play_track_handler)
        self.btn_box.addWidget(self.btn_play)
        self.btn_prev = QtWidgets.QPushButton()
        self.btn_prev.setIcon(self.app_style.standardIcon(QtWidgets.QStyle.SP_MediaSeekBackward))
        self.btn_box.addWidget(self.btn_prev)
        self.btn_pause = QtWidgets.QPushButton()
        self.btn_pause.setIcon(self.app_style.standardIcon(QtWidgets.QStyle.SP_MediaPause))
        self.btn_pause.clicked.connect(self.pause_track)
        self.btn_box.addWidget(self.btn_pause)
        self.btn_next = QtWidgets.QPushButton()
        self.btn_next.setIcon(self.app_style.standardIcon(QtWidgets.QStyle.SP_MediaSeekForward))
        self.btn_box.addWidget(self.btn_next)
        self.btn_stop = QtWidgets.QPushButton()
        self.btn_stop.setIcon(self.app_style.standardIcon(QtWidgets.QStyle.SP_MediaStop))
        self.btn_stop.clicked.connect(self.stop_track)
        self.btn_box.addWidget(self.btn_stop)

        # Slider volume
        self.slider_volume = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_volume.setMaximum(100)
        self.slider_volume.setMaximumWidth(150)
        self.slider_volume.setValue(self.vlc_media_player.audio_get_volume())
        self.slider_volume.setToolTip('Volume')
        self.slider_volume.valueChanged.connect(self.change_volume)
        self.btn_box.addWidget(self.slider_volume)

        # Track info labels
        self.track_info_box = QtWidgets.QGridLayout()
        self.label_track_name = QtWidgets.QLabel('Track:')
        self.track_info_box.addWidget(self.label_track_name)
        self.label_track_artists = QtWidgets.QLabel('Artist:')
        self.track_info_box.addWidget(self.label_track_artists)

        # Slider position
        self.slider_position_box = QtWidgets.QHBoxLayout()
        self.label_track_elapsed_time = QtWidgets.QLabel('00:00')
        self.slider_position_box.addWidget(self.label_track_elapsed_time)
        self.slider_position = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_position.setToolTip('Position')
        self.slider_position.sliderMoved.connect(self.change_track_positon)
        self.slider_position.sliderPressed.connect(self.change_track_positon)
        self.slider_position_box.addWidget(self.slider_position)
        self.label_track_duration = QtWidgets.QLabel('00:00')
        self.slider_position_box.addWidget(self.label_track_duration)

        # TableWidget for tracklist
        self.tracklist_table_widget = QtWidgets.QTableWidget()
        self.tracklist_table_widget.setObjectName('tracklist_table_widget')
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
        self.layout_box.addLayout(self.track_info_box)
        self.layout_box.addLayout(self.slider_position_box)
        self.widget.setLayout(self.layout_box)

        # Menu
        menubar = self.menuBar()
        menu_file = menubar.addMenu('File')
        action_close = QtWidgets.QAction('Logout', self)
        menu_file.addAction(action_close)
        action_close.triggered.connect(self.logout)

        # Timer for update track position slider
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_slider_position)

    # Play track on double click on track
    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.MouseButtonDblClick and
            event.buttons() == QtCore.Qt.LeftButton and
            source is self.tracklist_table_widget.viewport()):
            item = self.tracklist_table_widget.itemAt(event.pos())
            if item is not None:
                self.play_track_handler()
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
            t_duration = track['duration_ms']
            if t_artists:
                t_artists_list = []
                for item in t_artists:
                    t_artists_list.append(item['name'])
                t_artists_names = ' & '.join(t_artists_list)
                t_full_name = f'{t_artists_names} - {t_name}'
            else:
                t_artists_names = ''
                t_full_name = t_name
            self.tracklist.append({'id': t_id, 'name': t_name, 'artist': t_artists_names, 'duration': t_duration})

    def fill_tracklist_table(self):
        row = 0
        for track in self.tracklist:
            if track['artist']:
                col_1 = QtWidgets.QTableWidgetItem(f"{track['artist']} - {track['name']}")
            else:
                col_1 = QtWidgets.QTableWidgetItem(f"{track['name']}")
            col_2 = QtWidgets.QTableWidgetItem(f"{track['id']}")
            col_1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.tracklist_table_widget.setItem(row, 0, col_1)
            self.tracklist_table_widget.setItem(row, 1, col_2)
            row += 1

    def get_track_info_by_id(self, track_id):
        track_info = list(filter(lambda track: track['id'] == track_id, self.tracklist))
        if len(track_info) == 1:
            return track_id, track_info[0]['name'], track_info[0]['artist'], int(track_info[0]['duration'])
        else:
            raise RuntimeError

    # Get track info of current selected row
    def get_selected_track_info(self):
        selected_row = self.tracklist_table_widget.currentRow()
        track_id = self.tracklist_table_widget.item(selected_row, 1).text()
        return self.get_track_info_by_id(track_id)

    def logout(self):
        try:
            remove(self.yamp_auth_token_path)
            self.show_popup_info('Logout successful', 'You need restart application for finish logout')
        except Exception as ex:
            self.show_popup_error('Logout error', f'{ex}', 0)

    def create_cache_dir(self):
        if not path.isdir(self.yamp_cache_dir):
            try:
                mkdir(self.yamp_cache_dir)
            except Exception as ex:
                self.show_popup_error('Error', f'Some error occured while creating cache directory: {ex}', 0)

    def cache_track(self, track_id):
        track = self.client.tracks(track_id)[0]
        track_info = track.get_download_info()
        best_quality = sorted(track_info, key=lambda t_type: t_type['bitrate_in_kbps'], reverse=True)[0]
        codec = best_quality['codec']
        bitrate = best_quality['bitrate_in_kbps']
        track_cache_name = f'{path.join(self.yamp_cache_dir, track_id)}'
        if path.isfile(track_cache_name):
            return track_cache_name
        else:
            try:
                track.download(track_cache_name, codec=codec, bitrate_in_kbps=bitrate)
                return track_cache_name
            except YandexMusicError as ex:
                self.show_popup_error('Error', f'Some error occured while download track {ex}', 0)

    def play_track(self):
        try:
            track_cache_name = self.cache_track(self.cur_track_id)
            self.vlc_media = self.vlc_instance.media_new(track_cache_name)
            self.vlc_media_player.set_media(self.vlc_media)
            self.vlc_media_player.play()
            self.slider_position.setMaximum(self.cur_track_duration)
            track_duration_text = strftime('%M:%S'.format(self.cur_track_duration%1000), gmtime(self.cur_track_duration/1000.0))
            self.set_track_time_lables(duration=track_duration_text)
            self.set_track_info_lables(self.cur_track_name, self.cur_track_artist)
            self.timer.start()
        except RuntimeError:
            self.show_popup_error('Error', 'Some error occured!', 0)

    def pause_track(self):
        if self.vlc_media_player.is_playing() and not self.vlc_is_paused:
            self.vlc_media_player.pause()
            self.vlc_is_paused = True
            self.timer.stop()

    def stop_track(self):
        if self.vlc_media_player.is_playing():
            self.vlc_media_player.stop()
            self.timer.stop()
            self.slider_position.setValue(0)
            self.set_track_time_lables()
            self.set_track_info_lables()

    def change_volume(self, volume):
        self.vlc_media_player.audio_set_volume(volume)

    def change_track_positon(self):
        self.timer.stop()
        self.vlc_media_player.set_position(self.slider_position.value() / self.cur_track_duration)
        self.timer.start()

    def update_slider_position(self):
        track_position_percent = self.vlc_media_player.get_position() * 100
        track_position_time = int(self.cur_track_duration * track_position_percent / 100)
        self.slider_position.setValue(track_position_time)
        track_elapsed_time = strftime('%M:%S'.format(track_position_time%1000), gmtime(track_position_time/1000.0))
        self.label_track_elapsed_time.setText(track_elapsed_time)

    def set_track_info_lables(self, name='', artist=''):
        self.label_track_name.setText(f'Track: {name}')
        self.label_track_artists.setText(f'Artist: {artist}')

    def set_track_time_lables(self, elapsed='00:00', duration='00:00'):
        self.label_track_elapsed_time.setText(f'{elapsed}')
        self.label_track_duration.setText(f'{duration}')

    def play_track_handler(self):
        if self.vlc_is_paused:
            self.vlc_media_player.play()
            self.vlc_is_paused = False
            self.timer.start()
        else:
            try:
                self.cur_track_id, self.cur_track_name, self.cur_track_artist, self.cur_track_duration = self.get_selected_track_info()
                self.play_track()
            except RuntimeError:
                self.show_popup_error('Error', 'Some error occured!', 0)
