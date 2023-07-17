from concurrent.futures import ThreadPoolExecutor
from instapy import Instapy
import json
import requests
from settings import Settings

item_list = []


URL = Settings.KINTONE_USER_INFO["GET"]["URL"]
API_TOKEN = Settings.KINTONE_USER_INFO["GET"]["API_TOKEN"]


headers = {"X-Cybozu-API-Token": API_TOKEN}

resp = requests.get(URL, headers=headers)
items = json.loads(resp.text)["records"]

for item in items:
    if (item["レコード番号"]["value"] in ["50"]):
        item_list.append(item)


def main(item):
    session = Instapy(item,headless_browser=True)
    if session.executing_action["liked_img"] == 0 and session.executing_action["unfollowed"] == 0:
        session.end()
        return "成功"
    else:
        session.login()
        session.like_by_tags(amount=session.executing_action["liked_img"])
        session.unfollow(amount=session.executing_action["unfollowed"])
        session.end()
        return "成功"


with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(main, item_list)
    # results.shutdown()
for result in results:
    print(result)
