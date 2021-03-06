import re
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Correctly fill in the variables below, and then run this script with python3 message.py
username = 'your_username'
password = 'your_password'

# The URL of the group you want to post to. You MUST be a member of this group. Make sure there's no slash at the end.
group_link = 'https://www.linkedin.com/groups/10356456'

# The regex you want to look for in the person's title.
# For instance, if I want to look for CEOs, I would add '.*ceo.*'. Case insensitive.
member_title_regex_list = ['.*founder .*', '.*partner .*']

# A list of locations you want to contact people in.
# If I wanted to contact people in India and Canada, I would set this to ['India', 'Canada']
locations = ['India']

# The types of organisations the people you want to contact work at. There is a fixed list of types set by LinkedIn.
org_types = ['Legal Services', 'Law Practice']
# Set the following to True if you want to message people whose org types are unclear. False otherwise.
message_if_org_type_unclear = True

# The message you want to send people matching these descriptions.
# Potential inputs are {member_full_name}, {member_first_name}, {member_position}, {current_org}
message = "Hi {member_first_name}, \n\n" \
          "My name is Utkarsh and I'm co-founder of a LegalTech startup called Firmation (www.firmation.in). " \
          "We're both members of the Legal Transformation with Technology group, " \
          "and I saw that you're a decision maker at {current_org}, " \
          "so I wanted to reach out. \n\n" \
          "Many of the lawyers we've spoken to have complained that associates do not log their time regularly, " \
          "waste billable hours doing this at a later date, and sometimes even forget to log time for short " \
          "phone calls and email opinions, which means money lost.\n\n" \
          "To help address this issue, we're currently working on software to help lawyers automatically keep track " \
          "of time they spend working. \n\n" \
          "Does this sound like it could be useful to you? If so, I would love to set up a quick 20-minute chat " \
          "to discuss how our software could help you. \n\n" \
          "Thank you, and looking forward to hearing from you!\n\n" \
          "Utkarsh"


def check_if_member_messaged(linkedin_profile_url):
    # Open the file in read only mode
    with open('messaged_members.txt', 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            # For each line, check if line contains the string
            if linkedin_profile_url in line:
                return True
    return False


def write_member_url_to_file(linkedin_profile_url):
    # Open the file in read only mode
    with open('messaged_members.txt', 'a') as file:
        # Read all lines in the file one by one
        file.write(linkedin_profile_url + '\n')


options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
# options.add_argument('--headless')
driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)

driver.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')

username_field = driver.find_element_by_id('username')
username_field.send_keys(username)

password_field = driver.find_element_by_id('password')
password_field.send_keys(password)

driver.find_element_by_xpath('//button[text()="Sign in"]').click()

driver.get(f'{group_link}/members')
members = driver.find_elements_by_class_name('groups-members-list__typeahead-result')
regex_list_str = '(?:% s)' % '|'.join(map(str.lower, member_title_regex_list))
ctr = 0
while True:
    members = driver.find_elements_by_class_name('groups-members-list__typeahead-result')
    while ctr < len(members):
        member = members[ctr]
        try:
            member_title = member.find_element_by_class_name('artdeco-entity-lockup__subtitle').text
            if re.match(regex_list_str, member_title.lower()):
                member_full_name = member.find_element_by_class_name('artdeco-entity-lockup__title').text
                member_first_name = member_full_name.split(' ')[0]
                member_position = member_title.split(' at ')[0]
                message_member = False
                href = member.find_element_by_class_name("ui-entity-action-row__link").get_attribute("href")

                # handle current tab
                first_tab = driver.window_handles[0]

                # open new tab with specific url
                driver.execute_script("window.open('" + href + "');")

                # hadle new tab
                second_tab = driver.window_handles[1]

                # switch to second tab
                driver.switch_to.window(second_tab)

                member_url = driver.current_url

                if not check_if_member_messaged(member_url):
                    member_location = driver.find_element_by_class_name('pv-top-card--list-bullet').text
                    if any(location in member_location for location in locations):
                        try:
                            current_org_item = driver.find_element_by_class_name('pv-top-card--experience-list-item')
                            current_org = current_org_item.text
                            current_org_item.click()
                            wait = WebDriverWait(driver, 10).until(EC.presence_of_element_located
                                                                   ((By.CLASS_NAME, 'pv-entity__summary-info')))
                            experience_list = driver.find_element_by_class_name('pv-entity__summary-info').click()
                            wait = WebDriverWait(driver, 5).until(EC.presence_of_element_located
                                                                  ((By.CLASS_NAME,
                                                                    'org-top-card-summary-info-list__info-item')))
                            organisation_type = \
                            driver.find_elements_by_class_name('org-top-card-summary-info-list__info-item')[0].text

                            if organisation_type in org_types:
                                message_member = True

                        except TimeoutException as e:
                            print('No experience or company does not exist')
                            if message_if_org_type_unclear:
                                message_member = True
                else:
                    print("Already messaged this member, skipping.")

                driver.close()
                # switch to first tab
                driver.switch_to.window(first_tab)

                if message_member:
                    member.find_element_by_class_name('message-anywhere-button').click()
                    message_text_field = driver.find_element_by_class_name('msg-form__contenteditable')
                    message_to_send = message.format(member_full_name=member_full_name,
                                                     member_first_name=member_first_name,
                                                     member_position=member_position,
                                                     current_org=current_org)
                    print(f'Messaging {member_full_name} who is {member_position} at {current_org}: {message_to_send}')
                    message_text_field.send_keys(message_to_send)
                    driver.find_element_by_class_name('msg-form__send-button').click()
                    driver.find_element_by_xpath(
                        "//button[@data-control-name='overlay.close_conversation_window']").click()
                    write_member_url_to_file(member_url)
                    try:
                        driver.find_element_by_class_name("mlA").click()
                    except NoSuchElementException as e:
                        print("No confirm discard button")
        except Exception as e:
            print(e)
        ctr += 1
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    new_members_len = len(driver.find_elements_by_class_name('groups-members-list__typeahead-result'))
    load_iterations = 0
    while new_members_len == len(members) and load_iterations < 100:
        new_members_len = len(driver.find_elements_by_class_name('groups-members-list__typeahead-result'))
        load_iterations += 1
        sleep(0.1)
    if new_members_len == len(members):
        break
