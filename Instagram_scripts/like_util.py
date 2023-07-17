
import random
import re
from time import sleep


from constants import MEDIA_PHOTO
from constants import MEDIA_CAROUSEL
from constants import MEDIA_ALL_TYPES


# import exceptions
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException


# 外部ファイル
from xpath import read_xpath
from util import click_element
from util import get_additional_data


def check_link(
    browser
):
    try:
        # Check if the Post is Valid/Exists
        post_page = get_additional_data(browser)

        media = post_page["graphql"]["shortcode_media"]
        user_name = media["owner"]["username"]

        return user_name
    except:
        user_name = "None"
        return user_name


def get_links_for_tag(browser, tag, amount):

    tag = tag[1:] if tag[:1] == "#" else tag

    tag_link = "https://www.instagram.com/explore/tags/{}".format(tag)

    browser.get(tag_link)

    sleep(5)

    main_elem = browser.find_element_by_xpath(
        read_xpath(get_links_for_tag.__name__, "main_elem")
    )

    link_elems = main_elem.find_elements_by_tag_name("a")
    sleep(2)

    del link_elems[amount:]

    links = []

    for link_elem in link_elems:
        links.append(link_elem.get_attribute("href"))

    return links


def like_image(browser):
    like_xpath = read_xpath(like_image.__name__, "like")
    unlike_xpath = read_xpath(like_image.__name__, "unlike")

    # find first for like element
    like_elem = browser.find_elements_by_xpath(like_xpath)

    if len(like_elem) == 1:
        # sleep real quick right before clicking the element
        sleep(2)
        like_elem = browser.find_elements_by_xpath(like_xpath)
        if len(like_elem) > 0:
            click_element(browser, like_elem[0])
        # check now we have unlike instead of like
        liked_elem = browser.find_elements_by_xpath(unlike_xpath)

        if len(liked_elem) == 1:
            # logger.info(f"--> {user_name}： いいね!\n{link}")
            return True

        else:
            # if like not seceded wait for 2 min
            sleep(10)

    else:
        liked_elem = browser.find_elements_by_xpath(unlike_xpath)
        if len(liked_elem) == 1:
            # logger.info(f"--> {user_name}： いいね済み!\n{link}")
            return False

    return False
