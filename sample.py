from instapy import InstaPy
from instapy import smart_run


# your login credentials
insta_username = '**********'
insta_password = '**********'

# C:\Program Files\Mozilla Firefox\firefox.exe
browser_executable_path = '****************'

session = InstaPy(username=insta_username, password=insta_password,
                  browser_executable_path=browser_executable_path)
with smart_run(session):
    session.like_by_tags(['love'], amount=100, media='Photo')
