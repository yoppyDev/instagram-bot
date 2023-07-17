import os
import json
import logging
import pickle
import re
from time import sleep
from logging.handlers import RotatingFileHandler
from datetime import datetime
import glob
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pyasn1.type import tag
import requests
import random


from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# import exceptions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import MoveTargetOutOfBoundsException


# 外部ファイル
from chatwork import chatworkmessage
from chatwork import chatwork_add_task
from login import login_user
from login import log_follower_num
from unfollow import unfollow_users
from unfollow import get_following_users
from settings import Settings
from file_manager import get_workspace, use_assets
from file_manager import get_logfolder
from browser import set_selenium_local_session
from like_util import get_links_for_tag
from like_util import like_image
from like_util import check_link


ig_homepage = "https://www.instagram.com/"


class Instapy:
    def __init__(
        self,
        item,
        headless_browser: bool = False,
        show_logs: bool = True,
        log_handler=None,
    ):

        self.needs_update = True
        self.executing_action = {}
        self.executing_action["liked_img"] = 0
        self.executing_action["unfollowed"] = 0

        self.username = item["ユーザー名"]["value"]
        self.password = item["パスワード"]["value"]
        self.tags = item["タグ"]["value"]
        GoogleSheetLink = item["GoogleSheetLink"]["value"]
        self.spreadsheet_key = GoogleSheetLink[39:]
        self.max_liked_img = int(item["max_liked_img"]["value"])
        self.max_unfollowed = int(item["max_unfollowed"]["value"])

        # kintone
        self.record_id = item["レコード番号"]["value"]

        self.follow_user_list = None
        self.aborting = False
        self.dt_now = datetime.now()
        self.needs_writing = True

        # スプレッドシート
        self.cell = None
        self.worksheetRecord = None

        # アクションカウント
        self.liked_img = 0
        self.already_liked = 0
        self.unfollowed = 0

        # アカウント情報
        self.follow_num = 0
        self.follower_num = 0

        get_workspace()

        if not self.seat_authorization():
            self.aborting = True
            return

        if not self.readsheet():
            self.aborting = True
            return

        if self.liked_img < self.max_liked_img:
            self.executing_action["liked_img"] = random.randint(15, 20)

        if self.unfollowed < self.max_unfollowed:
            self.executing_action["unfollowed"] = 1

        if not self.executing_action:
            self.aborting = True

        # assign logger
        self.show_logs = show_logs
        self.logfolder = get_logfolder(self.record_id)
        self.logger = self.get_instapy_logger(self.show_logs, log_handler)

        self.browser = set_selenium_local_session(
            headless_browser
        )

    def like_by_tags(
        self,
        amount,
    ):

        if self.aborting:
            return self

        tags = self.tags.strip("\n")
        tags = tags.split('、')
        browser = self.browser

        index = 0

        for tag in tags:
            if amount <= index:
                break
            self.logger.info(tag)
            try:
                links = get_links_for_tag(
                    browser,
                    tag,
                    amount
                )
            except NoSuchElementException:
                self.logger.info("Too few images, skipping this tag")
                continue

            for link in links:

                browser.get(link)

                sleep(3)

                user_name = check_link(browser)

                result = like_image(browser)

                sleep(3)

                if result:
                    index += 1
                    self.logger.info(f"-->{index}： {user_name}： いいね!\n{link}")

        self.liked_img = index + self.liked_img

        return self

    # フォロー解除

    def unfollow(
        self,
        no_active_judgement_period: int = 30,
        amount: int = 3
    ):
        if self.aborting:
            return self

        self.follow_user_list = get_following_users(
            ig_homepage,
            self.browser,
            self.username
        )

        self.unfollowed = unfollow_users(
            ig_homepage,
            self.browser,
            self.follow_user_list,
            self.dt_now,
            self.logger,
            no_active_judgement_period,
            amount,
            self.unfollowed
        )

        return self

    # ログイン

    def login(self):

        if self.aborting:
            return self

        if not login_user(
            self.username,
            self.password,
            self.logfolder,
            self.browser,
            self.logger,
            ig_homepage
        ):
            chatwork_add_task(
                f"{self.username}；\nログインに失敗しました！\nログイン情報を確認してください！！")
            self.aborting = True
        else:
            if self.needs_update:
                self.followed_by = log_follower_num(
                    self.browser, self.username, self.logfolder)
        return self

    # ロガー作成
    def get_instapy_logger(self, show_logs: bool, log_handler=None):
        """
        Handles the creation and retrieval of loggers to avoid
        re-instantiation.
        """

        existing_logger = Settings.loggers.get(self.username)
        if existing_logger is not None:
            return existing_logger
        else:
            # initialize and setup logging system for the InstaPy object
            logger = logging.getLogger(self.username)
            logger.setLevel(logging.DEBUG)
            # log name and format
            general_log = "{}general.log".format(self.logfolder)
            file_handler = logging.FileHandler(general_log)
            # log rotation, 5 logs with 10MB size each one
            file_handler = RotatingFileHandler(
                general_log, maxBytes=10 * 1024 * 1024, backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            extra = {"username": self.username}
            logger_formatter = logging.Formatter(
                "%(levelname)s [%(asctime)s] [%(username)s]  %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(logger_formatter)
            logger.addHandler(file_handler)

            # add custom user handler if given
            if log_handler:
                logger.addHandler(log_handler)

            if show_logs is True:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)
                console_handler.setFormatter(logger_formatter)
                logger.addHandler(console_handler)

            logger = logging.LoggerAdapter(logger, extra)

            Settings.loggers[self.username] = logger
            Settings.logger = logger
            return logger

    # 終了

    def end(self):
        try:
            if not self.aborting:
                if self.needs_update:
                    # 更新日、フォロワー数、いいね数、フォロー解除数、を入力
                    self.worksheetRecord.update_acell(
                        'A' + str(self.cell), self.dt_now.strftime("%Y年%m月%d日"))
                    self.worksheetRecord.update_acell(
                        'B' + str(self.cell), self.followed_by)

                self.worksheetRecord.update_acell(
                    'C' + str(self.cell), self.liked_img)
                self.worksheetRecord.update_acell(
                    'D' + str(self.cell), self.unfollowed)
        except Exception as e:
            chatwork_add_task(f"{self.username}：スプレッドシート書き込みに失敗しました！\n{e}")
        self.browser.quit()
        message = "Session ended!"
        self.logger.info(message)
        print("\n\n")

    # 記録シートに今日の日時を記述
    def readsheet(self):
        try:
            values = self.worksheetRecord.get_all_values()
            for index, value in enumerate(values):
                if self.dt_now.strftime("%Y年%m月%d日") == value[0]:
                    index += 1
                    # いいね数取得
                    liked_img = self.worksheetRecord.acell(
                        'C' + str(index)).value
                    # フォロー解除数取得
                    unfollowed = self.worksheetRecord.acell(
                        'D' + str(index)).value
                    # アップデートが必要ではない
                    self.needs_update = False
                    # 行数を取得
                    self.liked_img = int(liked_img)
                    self.unfollowed = int(unfollowed)
                    self.cell = index
                    break
                elif len(values) - 1 == index:
                    index += 2
                    # いいね数取得
                    self.liked_img = 0
                    # フォロー解除
                    self.unfollowed = 0
                    # 行数を取得
                    self.cell = index
                    break
            return True
        except Exception as e:
            chatwork_add_task(f"{self.username}：スプレッドシート読み込みに失敗しました！\n{e}")
            return False

    # スプレットシート認証

    def seat_authorization(self):
        try:
            jsonfiles = glob.glob("*.json")
            jsonfile = jsonfiles[0]

            # 2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']

            # 認証情報設定
            # ダウンロードしたjsonファイル名をcredentials変数に設定
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                jsonfile, scope)

            # OAuth2の資格情報を使用してGoogle APIにログインします。
            gc = gspread.authorize(credentials)

            # 共有設定したスプレッドシートを開く
            workbook = gc.open_by_key(self.spreadsheet_key)
            self.worksheetRecord = workbook.worksheet('記録')
            return True
        except Exception as e:
            chatwork_add_task(f"{self.username}：スプレッドシート認証に失敗しました！\n{e}")
            return False
