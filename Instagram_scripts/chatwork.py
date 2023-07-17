import requests
from settings import Settings
import os
import json


CHATWORK_ROOM_ID = Settings.CHATWORK["CHATWORK_ROOM_ID"]
CHATWORK_API_TOKEN = Settings.CHATWORK["CHATWORK_API_TOKEN"]
member = Settings.CHATWORK["member"]


# メンヴバー情報取得

def chatwork_get_member():
    url = f'https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/members'

    headers = {'X-ChatWorkToken': CHATWORK_API_TOKEN}

    request = requests.get(
        url,
        headers=headers,
    )

    request = json.loads(request.content)

    member_list = []
    for user in request:
        member_list.append(user["account_id"])

    return member_list


# chatwork 画像付きメッセージ送信
def chatwork_send_image(file_name, file_path, message):
    # バイナリファイルでの読み込み
    file_data = open(file_path, 'rb').read()

    # ファイルの形式を設定
    files = {
        "file": (file_name, file_data, "image/png"),
    }

    # メッセージ設定
    data = {
        "message": message
    }

    # URL、ヘッダーを設定
    post_message_url = f"https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/files"
    headers = {'X-ChatWorkToken': CHATWORK_API_TOKEN}

    # リクエスト送信
    requests.post(
        post_message_url,
        headers=headers,
        files=files,
        data=data,
    )
    os.remove(file_path)

# chateork タスク追加


def chatwork_add_task(meg):
    url = f'https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/tasks'

    headers = {'X-ChatWorkToken': CHATWORK_API_TOKEN}
    params = {
        'body': meg,
        'to_ids': member
    }

    request = requests.post(
        url,
        headers=headers,
        params=params
    )


# chatworkメッセージ送信
def chatworkmessage(meg):
    url = f'https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/messages'

    headers = {'X-ChatWorkToken': CHATWORK_API_TOKEN}
    params = {'body': meg}

    requests.post(
        url,
        headers=headers,
        params=params
    )


# chatwork画像付きメッセージ送信
def error_sending(file_name, file_path, id):
    # バイナリファイルでの読み込み
    file_data = open(file_path, 'rb').read()

    # ファイルの形式を設定
    files = {
        "file": (file_name, file_data, "image/png"),
    }

    # メッセージ設定
    data = {
        "message": id + "：エラーが発生しました。"
    }

    # URL、ヘッダーを設定
    post_message_url = f"https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/files"
    headers = {'X-ChatWorkToken': CHATWORK_API_TOKEN}

    # リクエスト送信
    requests.post(
        post_message_url,
        headers=headers,
        files=files,
        data=data,
    )
    os.remove(file_path)
