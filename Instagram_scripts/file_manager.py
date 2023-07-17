import os
from os.path import expanduser
from os.path import exists as path_exists
from os.path import sep as native_slash
from platform import python_version


from settings import Settings
from settings import localize_path
from settings import WORKSPACE


"""ワークスペースフォルダを取得"""


def use_workspace():
    workspace_path = slashen(WORKSPACE["path"], "native")
    validate_path(workspace_path)
    return workspace_path


"""アセットフォルダを取得"""


def use_assets():
    assets_path = "{}{}assets".format(use_workspace(), native_slash)
    validate_path(assets_path)
    return assets_path


"""ユーザーのためにワークスペースを準備します"""


def get_workspace():

    if WORKSPACE["path"]:
        workspace = verify_workspace_name(WORKSPACE["path"])

    else:
        home_dir = get_home_path()
        workspace = "{}/{}".format(home_dir, WORKSPACE["name"])

    update_workspace(workspace)
    update_locations()
    return WORKSPACE


""" ユーザーのホーム ディレクトリを取得する """


def get_home_path():

    if python_version() >= "3.5":
        from pathlib import Path

        home_dir = str(Path.home())  # this method returns slash as dir sep*
    else:
        home_dir = expanduser("~")

    home_dir = slashen(home_dir)
    home_dir = remove_last_slash(home_dir)

    return home_dir


"""
ワークスペースが変更されたので、場所も更新する必要があります

ユーザーがすでに場所を設定している場合は、変更しないでください
"""


def update_locations():

    # update logs location
    if not Settings.log_location:
        Settings.log_location = localize_path("logs")

    # update database location
    if not Settings.database_location:
        Settings.database_location = localize_path("db", "instapy.db")


""" ワークスペース定数を最新のパスで更新します """


def update_workspace(latest_path):

    latest_path = slashen(latest_path, "native")
    validate_path(latest_path)
    WORKSPACE.update(path=latest_path)


""" パスのバックスラッシュをスラッシュに置き換えます """


def slashen(path, direction="forward"):

    if direction == "forward":
        path = path.replace("\\", "/")

    elif direction == "backwards":
        path = path.replace("/", "\\")

    elif direction == "native":
        path = path.replace("/", str(native_slash))
        path = path.replace("\\", str(native_slash))

    return path


""" 指定されたパスが存在することを確認してください """


def validate_path(path):

    if not path_exists(path):
        try:
            os.makedirs(path)
        except:
            pass


""" 選択したワークスペース名が InstaPy フレンドリーであることを確認してください """


def verify_workspace_name(path):

    path = slashen(path)
    path = remove_last_slash(path)
    custom_workspace_name = path.split("/")[-1]
    default_workspace_name = WORKSPACE["name"]

    if default_workspace_name not in custom_workspace_name:
        if default_workspace_name.lower() not in custom_workspace_name.lower():
            path += "/{}".format(default_workspace_name)
        else:
            nicer_name = custom_workspace_name.lower().replace(
                default_workspace_name.lower(), default_workspace_name
            )
            path = path.replace(custom_workspace_name, nicer_name)

    return path


""" 指定されたパスの最後のスラッシュを削除します [もしあれば] """


def remove_last_slash(path):

    if path.endswith("/"):
        path = path[:-1]

    return path


def get_logfolder(record_id):
    logfolder = "{0}{1}{2}{1}".format(
        Settings.log_location, native_slash, record_id)

    validate_path(logfolder)
    return logfolder
