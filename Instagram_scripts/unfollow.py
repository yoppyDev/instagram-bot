from datetime import datetime
from time import sleep


from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


from xpath import read_xpath


# フォロー解除
def unfollow_users(
    ig_homepage,
    browser,
    follow_user_list,
    dt_now,
    logger,
    no_active_judgement_period,
    amount,
    unfollowed
):

    index = 0

    for follow_user in follow_user_list:
        if (amount == index):
            break

        try:
            browser.get(ig_homepage+follow_user)

            browser.implicitly_wait(5)

            latest_posts = browser.find_elements_by_xpath(
                read_xpath(unfollow_users.__name__, "latest_posts")
            )

            not_active = None

            if not latest_posts:
                not_active = True
            else:
                (
                    ActionChains(browser)
                    .move_to_element(latest_posts[0])
                    .click()
                    .perform()
                )

                browser.implicitly_wait(5)

                latest_posts_date_str = browser.find_element_by_xpath(
                    read_xpath(unfollow_users.__name__, "latest_posts_date")
                ).get_attribute("datetime")

                latest_posts_date = datetime.strptime(
                    latest_posts_date_str[:10], '%Y-%m-%d')

                period = dt_now - latest_posts_date

                if (no_active_judgement_period <= period.days):

                    not_active = True

            browser.back()

            browser.implicitly_wait(5)

            if (not_active):
                browser.find_element_by_xpath(
                    read_xpath(unfollow_users.__name__,
                               "follow_stats_confirmation")
                ).click()

                browser.implicitly_wait(5)

                browser.find_element_by_xpath(
                    read_xpath(unfollow_users.__name__, "confirm_unfollow")
                ).click()

                logger.info(follow_user+"：フォロー解除しました")
                index += 1
        except Exception as e:
            logger.info(e)
            logger.info(follow_user+"：フォロー解除できませんでした")

    index = unfollowed + index

    return index


# 全てのフォロー中のユーザーを取得
def get_following_users(
    ig_homepage,
    browser,
    id
):

    follow_user_list = []
    follow_name = None
    browser.get(ig_homepage+id)

    sleep(3)

    browser.find_element_by_xpath(
        read_xpath(get_following_users.__name__, "following_botton")
    ).click()

    sleep(3)

    while True:
        browser.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
        elms = browser.find_elements_by_class_name("d7ByH")

        if follow_name == elms[-1].text:
            for elm in elms:
                follow_user_list.append(elm.text)
            break

        sleep(2)
        follow_name = elms[-1].text

    return follow_user_list
