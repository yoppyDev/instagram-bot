import re
import json
from time import sleep
from bs4 import BeautifulSoup
from time import time


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException


# 外部ファイル
from chatwork import chatwork_send_image


def image_err_message(message, browser, logfolder):
    # スクリーンショット取得
    file_name = str(time) + '.png'
    file_path = logfolder + file_name
    browser.save_screenshot(file_path)
    chatwork_send_image(file_name, file_path, message)


def get_additional_data(browser):
    """
    Get additional data object from page source
    Idea and Code by alokkumarsbg

    :param browser: The selenium webdriver instance
    :return additional_data: Json data from window.__additionalData extracted from page source
    """
    additional_data = None
    soup = BeautifulSoup(browser.page_source, "html.parser")
    for text in soup(text=re.compile(r"window.__additionalDataLoaded")):
        if re.search("^window.__additionalDataLoaded", text):
            additional_data = json.loads(text[48:-2])

    return additional_data


def click_element(browser, element, tryNum=0):
    try:
        # use Selenium's built in click function
        element.click()

    except Exception:
        # click attempt failed
        # try something funky and try again

        if tryNum == 0:
            # try scrolling the element into view
            try:
                # This tends to fail because the script fails to get the element class
                if element.get_attribute("class") != "":
                    browser.execute_script(
                        "document.getElementsByClassName('"
                        + element.get_attribute("class")
                        + "')[0].scrollIntoView({ inline: 'center' });"
                    )
            except Exception:
                pass

        elif tryNum == 1:
            # well, that didn't work, try scrolling to the top and then
            # clicking again
            browser.execute_script("window.scrollTo(0,0);")

        elif tryNum == 2:
            # that didn't work either, try scrolling to the bottom and then
            # clicking again
            browser.execute_script(
                "window.scrollTo(0,document.body.scrollHeight);")

        else:
            # try `execute_script` as a last resort
            # print("attempting last ditch effort for click, `execute_script`")
            try:
                if element.get_attribute("class") != "":
                    browser.execute_script(
                        "document.getElementsByClassName('"
                        + element.get_attribute("class")
                        + "')[0].click()"
                    )
                    # update server calls after last click attempt by JS
            except Exception:
                print("Failed to click an element, giving up now")

            # end condition for the recursive function
            return

        # update server calls after the scroll(s) in 0, 1 and 2 attempts

        # sleep for 1 second to allow window to adjust (may or may not be
        # needed)

        tryNum += 1

        # try again!
        click_element(browser, element, tryNum)


def web_address_navigator(browser, link):
    """Checks and compares current URL of web page and the URL to be
    navigated and if it is different, it does navigate"""
    current_url = get_current_url(browser)
    total_timeouts = 0
    page_type = None  # file or directory

    # remove slashes at the end to compare efficiently
    if current_url is not None and current_url.endswith("/"):
        current_url = current_url[:-1]

    if link.endswith("/"):
        link = link[:-1]
        page_type = "dir"  # slash at the end is a directory

    new_navigation = current_url != link

    if current_url is None or new_navigation:
        link = link + "/" if page_type == "dir" else link  # directory links
        # navigate faster

        while True:
            try:
                browser.get(link)
                # update server calls
                sleep(2)
                break

            except TimeoutException as exc:
                if total_timeouts >= 7:
                    raise TimeoutException(
                        "Retried {} times to GET '{}' webpage "
                        "but failed out of a timeout!\n\t{}".format(
                            total_timeouts,
                            str(link).encode("utf-8"),
                            str(exc).encode("utf-8"),
                        )
                    )
                total_timeouts += 1
                sleep(2)


def get_current_url(browser):
    """ Get URL of the loaded webpage """
    try:
        current_url = browser.execute_script("return window.location.href")

    except WebDriverException:
        try:
            current_url = browser.current_url

        except WebDriverException:
            current_url = None

    return current_url


def check_authorization(browser, id, method, logger, notify=True):
    """ Check if user is NOW logged in """
    if notify is True:
        logger.info("Checking if '{}' is logged in...".format(id))

    # different methods can be added in future
    if method == "activity counts":

        # navigate to owner's profile page only if it is on an unusual page
        current_url = get_current_url(browser)
        if (
                not current_url
                or "https://www.instagram.com" not in current_url
                or "https://www.instagram.com/graphql/" in current_url
        ):
            profile_link = "https://www.instagram.com/{}/".format(id)
            web_address_navigator(browser, profile_link)

        # if user is not logged in, `activity_counts` will be `None`- JS `null`
        try:
            activity_counts = browser.execute_script(
                "return window._sharedData.activity_counts"
            )

        except WebDriverException:
            try:
                browser.execute_script("location.reload()")

                activity_counts = browser.execute_script(
                    "return window._sharedData.activity_counts"
                )

            except WebDriverException:
                activity_counts = None

        # if user is not logged in, `activity_counts_new` will be `None`- JS
        # `null`
        try:
            activity_counts_new = browser.execute_script(
                "return window._sharedData.config.viewer"
            )

        except WebDriverException:
            try:
                browser.execute_script("location.reload()")
                activity_counts_new = browser.execute_script(
                    "return window._sharedData.config.viewer"
                )

            except WebDriverException:
                activity_counts_new = None

        if activity_counts is None and activity_counts_new is None:
            if notify is True:
                logger.critical(
                    "--> '{}' is not logged in!\n".format(id))
            return False

    return True


def explicit_wait(browser, track, ec_params, logger, timeout=35, notify=True):
    """
    Explicitly wait until expected condition validates

    :param browser: webdriver instance
    :param track: short name of the expected condition
    :param ec_params: expected condition specific parameters - [param1, param2]
    :param logger: the logger instance
    """
    # list of available tracks:
    # <https://seleniumhq.github.io/selenium/docs/api/py/webdriver_support/
    # selenium.webdriver.support.expected_conditions.html>

    if not isinstance(ec_params, list):
        ec_params = [ec_params]

    # find condition according to the tracks
    condition = None
    ec_name = None

    if track == "VOEL":
        elem_address, find_method = ec_params
        ec_name = "visibility of element located"

        find_by = (
            By.XPATH
            if find_method == "XPath"
            else By.CSS_SELECTOR
            if find_method == "CSS"
            else By.CLASS_NAME
        )
        locator = (find_by, elem_address)
        condition = ec.visibility_of_element_located(locator)

    elif track == "TC":
        expect_in_title = ec_params[0]
        ec_name = "title contains '{}' string".format(expect_in_title)

        condition = ec.title_contains(expect_in_title)

    elif track == "PFL":
        ec_name = "page fully loaded"

        def condition(browser): return browser.execute_script(
            "return document.readyState"
        ) in ["complete" or "loaded"]

    elif track == "SO":
        ec_name = "staleness of"
        element = ec_params[0]

        condition = ec.staleness_of(element)

    # generic wait block
    try:
        wait = WebDriverWait(browser, timeout)
        result = wait.until(condition)

    except TimeoutException:
        if notify is True:
            logger.info(
                "Timed out with failure while explicitly waiting until {}!\n".format(
                    ec_name
                )
            )
        return False

    return result
