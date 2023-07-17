# import built-in & third-party modules
from sys import platform
from os import environ as environmental_variables
from os.path import join as join_path

WORKSPACE = {
    "name": "InstaPy",
    "path": environmental_variables.get("INSTAPY_WORKSPACE"),
}
OS_ENV = (
    "windows" if platform == "win32" else "osx" if platform == "darwin" else "linux"
)


def localize_path(*args):
    """ Join given locations as an OS path """
    if WORKSPACE["path"]:
        path = join_path(WORKSPACE["path"], *args)
        return path
    else:
        return None


class Settings:
    """ Globally accessible settings throughout whole project """

    KINTONE_USER_INFO = {
        "GET": {
            "URL": "************",
            "API_TOKEN": "************"
        }
    }

    CHATWORK = {
        "CHATWORK_ROOM_ID": "************",
        "CHATWORK_API_TOKEN": "************",
        "member": "************"
    }

    # locations
    log_location = localize_path("logs")
    database_location = localize_path("db", "instapy.db")

    # set a logger cache outside the InstaPy object to avoid
    # re-instantiation issues
    loggers = {}
    logger = None

    user_agent = {
        "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
    }
