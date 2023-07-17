import logging
from chatwork import chatworkmessage
import pickle
import re
import json
from time import sleep
from bs4 import BeautifulSoup


from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


# import exceptions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import MoveTargetOutOfBoundsException

# 外部ファイル
from util import check_authorization
from util import explicit_wait
from xpath import read_xpath
from util import image_err_message


# ログイン関数
def login_user(
    username,
    password,
    logfolder,
    browser,
    logger,
    ig_homepage
):

    browser.get(ig_homepage+"accounts/login/?source=desktop_nav")

    browser.implicitly_wait(5)

    cookie_file = "{0}{1}_cookie.pkl".format(logfolder, username)
    cookie_loaded = None
    login_state = None

    # try to load cookie from username
    try:
        for cookie in pickle.load(open(cookie_file, "rb")):
            # SameSite = Strict, your cookie will only be sent in a
            # first-party context. In user terms, the cookie will only be sent
            # if the site for the cookie matches the site currently shown in
            # the browser's URL bar.
            if "sameSite" in cookie and cookie["sameSite"] == "None":
                cookie["sameSite"] = "Strict"

            browser.add_cookie(cookie)

        sleep(4)
        cookie_loaded = True
        logger.info("- Cookie file for user '{}' loaded...".format(username))

        # force refresh after cookie load or check_authorization() will FAIL
        browser.execute_script("location.reload()")
        sleep(4)

        if "instagram.com/challenge" in browser.current_url:
            return False

        # cookie has been LOADED, so the user SHOULD be logged in
        login_state = check_authorization(
            browser, username, "activity counts", logger, False
        )
        sleep(4)

    except (WebDriverException, OSError, IOError):
        # Just infor the user, not an error
        logger.info("- Cookie file not found, creating cookie...")

    if login_state and cookie_loaded:
        # Cookie loaded and joined IG, dismiss following features if availables
        dismiss_save_information(browser, logger)
        home_screen(browser, logger)
        dismiss_notification_offer(browser, logger)
        dismiss_get_app_offer(browser, logger)
        use_the_app(browser)
        return True

    # Check if the first div is 'Create an Account' or 'Log In'
    try:
        login_elem = browser.find_element_by_xpath(
            read_xpath(login_user.__name__, "login_elem")
        )
    except NoSuchElementException:
        logger.warning("Login A/B test detected! Trying another string...")
        try:
            login_elem = browser.find_element_by_xpath(
                read_xpath(login_user.__name__, "login_elem_no_such_exception")
            )
        except NoSuchElementException:
            logger.warning(
                "Could not pass the login A/B test. Trying last string...")
            try:
                login_elem = browser.find_element_by_xpath(
                    read_xpath(login_user.__name__,
                               "login_elem_no_such_exception_2")
                )
            except NoSuchElementException as e:
                # NF: start
                logger.exception(
                    "Login A/B test failed!\n\t{}".format(
                        str(e).encode("utf-8"))
                )
                return False
                # NF: end

    if login_elem is not None:
        try:
            (ActionChains(browser).move_to_element(login_elem).click().perform())
        except MoveTargetOutOfBoundsException:
            login_elem.click()

    # ログインID
    input_username_XP = browser.find_element_by_xpath(
        read_xpath(login_user.__name__, "input_username_XP")
    )

    (
        ActionChains(browser)
        .move_to_element(input_username_XP)
        .click()
        .send_keys(username)
        .perform()
    )

    sleep(1)

    # password
    input_password = browser.find_elements_by_xpath(
        read_xpath(login_user.__name__, "input_password")
    )

    sleep(1)

    (
        ActionChains(browser)
        .move_to_element(input_password[0])
        .click()
        .send_keys(password)
        .perform()
    )

    sleep(1)

    (
        ActionChains(browser)
        .move_to_element(input_password[0])
        .click()
        .send_keys(Keys.ENTER)
        .perform()
    )

    sleep(5)

    # Dismiss following features if availables
    dismiss_save_information(browser, logger)
    home_screen(browser, logger)
    dismiss_notification_offer(browser, logger)
    dismiss_get_app_offer(browser, logger)
    use_the_app(browser)

    # check for login error messages and display it in the logs
    if "instagram.com/challenge" in browser.current_url:
        # check if account is disabled by Instagram,
        # or there is an active challenge to solve
        try:
            account_disabled = browser.find_element_by_xpath(
                read_xpath(login_user.__name__, "account_disabled")
            )
            logger.warning(account_disabled.text)
            return False
        except NoSuchElementException:
            pass

        # in case the user doesnt have a phone number linked to the Instagram account
        try:
            browser.find_element_by_xpath(
                read_xpath(login_user.__name__, "add_phone_number")
            )
            challenge_warn_msg = (
                "Instagram initiated a challenge before allow your account to login. "
                "At the moment there isn't a phone number linked to your Instagram "
                "account. Please, add a phone number to your account, and try again."
            )
            logger.warning(challenge_warn_msg)
            return False
        except NoSuchElementException:
            pass

    # check for wrong username or password message, and show it to the user
    try:
        error_alert = browser.find_element_by_xpath(
            read_xpath(login_user.__name__, "error_alert")
        )
        logger.warning(error_alert.text)
        return False
    except NoSuchElementException:
        pass

    if "instagram.com/accounts/onetap" in browser.current_url:
        browser.get(ig_homepage)

    cookie_file = "{0}{1}_cookie.pkl".format(logfolder, username)

    # ユーザーがログインしているかどうかを確認します (2 つの「nav」要素がある場合)
    nav = browser.find_elements_by_xpath(
        read_xpath(login_user.__name__, "nav"))
    if len(nav) == 2:
        # ユーザー名のクッキーを作成して保存
        cookies_list = browser.get_cookies()

        for cookie in cookies_list:
            if "sameSite" in cookie and cookie["sameSite"] == "None":
                cookie["sameSite"] = "Strict"

        try:
            # Open the cookie file to store the data
            with open(cookie_file, "wb") as cookie_f_handler:
                pickle.dump(cookies_list, cookie_f_handler)

        except pickle.PicklingError:
            # Next time, cookie will be created for the session so we are safe
            logger.warning(
                "- Browser cookie list could not be saved to your local...")

        finally:
            return True

    else:
        return False


def log_follower_num(browser, username, logfolder):
    """Prints and logs the current number of followers to
    a seperate file"""
    try:
        user_link = "https://www.instagram.com/{}".format(username)
        browser.get(user_link)

        followed_by = getUserData(
            "graphql.user.edge_followed_by.count", browser)

        return followed_by
    except Exception as e:
        image_err_message(
            f"{username}：フォロワー取得に失敗しました。\n{e}", browser, logfolder)
        return None


def getUserData(
        query,
        browser,
        basequery="no-longer-needed",
):
    shared_data = get_shared_data(browser)
    data = shared_data["entry_data"]["ProfilePage"][0]

    if query.find(".") == -1:
        data = data[query]
    else:
        subobjects = query.split(".")
        for subobject in subobjects:
            data = data[subobject]

    return data


def get_shared_data(
        browser
):
    """
    Get shared data object from page source
    Code by schealex

    :param browser: The selenium webdriver instance
    :return shared_data: Json data from window._sharedData extracted from page source
    """
    shared_data = None
    soup = BeautifulSoup(browser.page_source, "html.parser")
    for text in soup(text=re.compile(r"window._sharedData")):
        if re.search("^window._sharedData", text):
            shared_data = json.loads(text[21:-1])

    return shared_data


def dismiss_get_app_offer(browser, logger):
    """ Dismiss 'Get the Instagram App' page after a fresh login """
    offer_elem = read_xpath(dismiss_get_app_offer.__name__, "offer_elem")
    dismiss_elem = read_xpath(dismiss_get_app_offer.__name__, "dismiss_elem")

    # wait a bit and see if the 'Get App' offer rises up
    offer_loaded = explicit_wait(
        browser, "VOEL", [offer_elem, "XPath"], logger, 5, False
    )

    if offer_loaded:
        browser.find_element_by_xpath(dismiss_elem).click()


def dismiss_notification_offer(browser, logger):
    """ Dismiss 'Turn on Notifications' offer on session start """
    offer_elem_loc = read_xpath(
        dismiss_notification_offer.__name__, "offer_elem_loc")
    dismiss_elem_loc = read_xpath(
        dismiss_notification_offer.__name__, "dismiss_elem_loc"
    )

    # wait a bit and see if the 'Turn on Notifications' offer rises up
    offer_loaded = explicit_wait(
        browser, "VOEL", [offer_elem_loc, "XPath"], logger, 4, False
    )

    if offer_loaded:
        browser.find_element_by_xpath(dismiss_elem_loc).click()


def dismiss_save_information(browser, logger):
    """ Dismiss 'Save Your Login Info?' offer on session start """
    # This question occurs when pkl doesn't exist
    offer_elem_loc = read_xpath(
        dismiss_save_information.__name__, "offer_elem_loc")
    dismiss_elem_loc = read_xpath(
        dismiss_save_information.__name__, "dismiss_elem_loc")

    offer_loaded = explicit_wait(
        browser, "VOEL", [offer_elem_loc, "XPath"], logger, 4, False
    )

    if offer_loaded:
        # When prompted chose "Not Now", we don't know if saving information
        # contributes or stimulate IG to target the acct, it would be better to
        # just pretend that we are using IG in different browsers.
        logger.info("- Do not save Login Info by now...")
        browser.find_element_by_xpath(dismiss_elem_loc).click()


def accept_igcookie_dialogue(browser, logger):
    """ Presses 'Accept' button on IG cookie dialogue """
    offer_elem_loc = read_xpath(
        accept_igcookie_dialogue.__name__, "accept_button")

    offer_loaded = explicit_wait(
        browser, "VOEL", [offer_elem_loc, "XPath"], logger, 4, False
    )

    if offer_loaded:
        logger.info("- Accepted IG cookies by default...")
        browser.find_element_by_xpath(offer_elem_loc).click()


def home_screen(browser, logger):
    offer_elem_loc = read_xpath(home_screen.__name__, "offer_elem_loc")
    dismiss_elem_loc = read_xpath(
        home_screen.__name__, "dismiss_elem_loc"
    )

    # wait a bit and see if the 'Turn on Notifications' offer rises up
    offer_loaded = explicit_wait(
        browser, "VOEL", [offer_elem_loc, "XPath"], logger, 4, False
    )

    if offer_loaded:
        browser.find_element_by_xpath(dismiss_elem_loc).click()


def use_the_app(browser):
    use_the_app_body_xpath = read_xpath(
        use_the_app.__name__, "use_the_app_body_xpath"
    )
    close_button = read_xpath(
        use_the_app.__name__, "close_button"
    )

    use_the_app_body = browser.find_elements_by_xpath(use_the_app_body_xpath)

    if use_the_app_body:
        browser.find_element_by_xpath(close_button).click()
