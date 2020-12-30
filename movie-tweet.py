import tweepy
import config
import time
import requests
import json
import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QWidget, QDockWidget, QLineEdit)

index = 0
page_num = 1
total_pages = 1

base_url = 'https://api.themoviedb.org/3/'
base_image = 'https://image.tmdb.org/t/p/w500'

search_movie = ""
comments = None
movies = []
pages = []

grid = QGridLayout()
WIDTH, HEIGHT = 1000, 900
app = QApplication([])
app.setStyle('Fusion')
win = QMainWindow()
win.setGeometry(500, 100, WIDTH, HEIGHT)
win.setWindowTitle('Movie Tweets')


def send_tweet(choice):  # Takes the given movie and sends a tweet in the form: watching (title) (release date)
    print("sending tweet")
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_secret)

    api = tweepy.API(auth)
    api.update_with_media(choice.poster_path, choice.get_tweet())
    print("tweet sent!")
    delete_posters()
    app.quit()


class Box:

    def __init__(self, poster_path, movie_info):
        self.poster_path = poster_path
        self.movie_info = movie_info
        self.group = QGroupBox()
        self.push_button = QPushButton(f"{self.movie_info['original_title']} ({self.movie_info['release_date'][0:4]})")
        self.init_box()

    def get_tweet(self):
        return f"watching {self.movie_info['original_title']} ({self.movie_info['release_date'][0:4]}) {comments}"

    def init_box(self):
        global grid
        self.push_button.clicked.connect(lambda: send_tweet(self))
        label = QLabel()
        pixmap = QPixmap(self.poster_path)
        pixmap = pixmap.scaled(400, 325)
        label.setPixmap(pixmap)
        label.setMaximumWidth(400)
        self.push_button.setMaximumWidth(400)
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.push_button)

        vbox.addStretch()
        self.group.setLayout(vbox)

    def get_box(self):
        return self.group


def get_movies():  # Calls the API to get movies that match our search query.
    global movies, total_pages
    r = requests.get(base_url + f"search/movie?api_key={config.api_key}&query={search_movie}")
    data = json.loads(r.content)
    for movie in data["results"]:
        if movie["poster_path"] is None:
            continue
        if "release_date" not in movie:
            continue
        movies.append(movie)

    if (len(movies) // 4) == 0:
        total_pages = 1
        return
    if (len(movies) % 4) == 0:
        total_pages = len(movies) // 4
    else:
        total_pages = (len(movies) // 4) + 1


def delete_posters():  # Deletes the posters generated in create_boxes()
    posters = os.listdir(os.getcwd())
    for poster in posters:
        if poster[0:6] != "poster":
            continue
        os.remove(poster)


def clear_grid():  # Clears our grid of movie boxes.
    for i in reversed(range(grid.count())):
        grid.itemAt(i).widget().setParent(None)


def create_boxes():  # Creates posters and adds boxes to the grid.
    global grid, index
    clear_grid()
    temp = []
    for a in range(2):
        for b in range(2):
            movie = movies[index]
            r = requests.get(base_image + movie["poster_path"])
            poster_path = f"poster{index}.jpg"

            with open(poster_path, "wb") as p:
                p.write(r.content)

            box = Box(poster_path, movie)
            temp.append(box)
            grid.addWidget(box.get_box(), a, b)
            index += 1
            if index == len(movies):
                return
    pages.append(temp)


def show_page():
    global grid, page_num
    clear_grid()
    page = pages[page_num-1]
    i = 0
    for a in range(2):
        for b in range(2):
            grid.addWidget(page[i].get_box(), a, b)
            i += 1


def main():

    central_widget = QWidget()

    input_dock = QDockWidget()
    input_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
    input_dock.setFloating(False)

    top_widget = QWidget()
    top_layout = QHBoxLayout()
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("Enter a movie")
    comment_bar = QLineEdit()
    comment_bar.setPlaceholderText("Comments?")
    button = QPushButton()
    top_layout.addWidget(search_bar)
    top_layout.addWidget(comment_bar)
    top_layout.addWidget(button)
    top_widget.setLayout(top_layout)
    input_dock.setWidget(top_widget)
    win.addDockWidget(Qt.TopDockWidgetArea, input_dock)

    page_dock = QDockWidget()
    page_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
    page_dock.setFloating(False)

    bottom_widget = QWidget()
    bottom_layout = QHBoxLayout()
    last_btn = QPushButton("Back")
    num_label = QLabel()
    next_btn = QPushButton("Next")
    bottom_layout.addWidget(last_btn)
    bottom_layout.addWidget(num_label)
    bottom_layout.addWidget(next_btn)
    bottom_layout.addStretch()
    bottom_widget.setLayout(bottom_layout)
    page_dock.setWidget(bottom_widget)
    page_dock.setVisible(False)
    win.addDockWidget(Qt.BottomDockWidgetArea, page_dock)

    def show_boxes():
        global search_movie, comments
        search_movie = search_bar.text()
        comments = comment_bar.text()
        get_movies()
        create_boxes()
        central_widget.setLayout(grid)
        win.setCentralWidget(central_widget)
        input_dock.setVisible(False)
        num_label.setText(f"Page {page_num} of {total_pages}")
        last_btn.setVisible(False)
        if total_pages == 1:
            next_btn.setVisible(False)
        page_dock.setVisible(True)

    def next_page():
        global page_num
        page_num += 1
        if page_num <= len(pages):
            show_page()
        else:
            create_boxes()
        central_widget.setLayout(grid)
        win.setCentralWidget(central_widget)
        if page_num == total_pages:
            next_btn.setVisible(False)
        else:
            next_btn.setVisible(True)
        last_btn.setVisible(True)
        num_label.setText(f"Page {page_num} of {total_pages}")

    def last_page():
        global page_num
        page_num -= 1
        show_page()
        central_widget.setLayout(grid)
        win.setCentralWidget(central_widget)
        if page_num == total_pages-1:
            next_btn.setVisible(True)
        if page_num == 1:
            last_btn.setVisible(False)
        num_label.setText(f"Page {page_num} of {total_pages}")

    button.clicked.connect(show_boxes)
    next_btn.clicked.connect(next_page)
    last_btn.clicked.connect(last_page)

    win.show()
    sys.exit(app.exec_())


main()