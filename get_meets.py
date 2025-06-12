from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import csv
import json
import re
import sys
import sel_scraper

options = webdriver.ChromeOptions()
options.binary_location = "/usr/bin/google-chrome"
service = Service("/home/zack/byu/cs452/running/chromedriver-linux64/chromedriver")
options.add_argument('--headless')  # run in background
driver = webdriver.Chrome(service=service, options=options)



def get_meets(url):
    year = re.search(r'\d\d\d\d', url).group(0)
    print(year)
    driver.get(url)
    sleep(2)

    rows = driver.find_elements(By.TAG_NAME, "tr")

    events = []

    i = 0
    while i < len(rows):
        try:
            event_name_els = rows[i].find_elements(By.CLASS_NAME, "blacklinkbold2")
            if event_name_els:
                event_name = event_name_els[0].text.strip()

                # Get result link
                try:
                    result_link_el = rows[i].find_element(By.CLASS_NAME, "blacklink")
                    result_link = result_link_el.get_attribute("href")
                except:
                    result_link = ""

                # Get location, date, start time from next row
                location, date =  "", ""
                if i + 1 < len(rows):
                    font_els = rows[i + 1].find_elements(By.TAG_NAME, "font")
                    for font in font_els:
                        lines = font.text.splitlines()
                        for line in lines:
                            if "Location:" in line:
                                location = line.split("Location:")[-1].strip()
                            elif "Date:" in line:
                                date = line.split("Date:")[-1].strip()

                if location:
                    if "UT" in location: # or any(month in date for month in ("November", "December")): # to include regionals and nationals
                        if any(month in date for month in ("July", "August", "September", "October", "November", "December")):

                            event_id = get_meet_id(result_link)
                            races = find_races(event_name, location, date, result_link)
                            if races:
                                events.append((event_name, event_id, location, date, result_link, races))

                i += 2  # Skip to next event row
            else:
                i += 1
        except Exception as e:
            print(f"Error processing row {i}: {e}")
            i += 1

    driver.quit()

    # Print results
    # for event in events:
    #     print(event)
    filename = str(year) + "_meets.json"
    with open(filename, "w") as file:

        file.write(json.dumps(events))


def find_races(meet_name, location, date, url):
    driver = sel_scraper.set_up(url)
    anchors = driver.find_elements("tag name", "a")
    races = []

    for anchor in anchors:
        if "Boys" in anchor.text or "Girls" in anchor.text:
            race_link = anchor.get_attribute("href")
            race_id = get_event_id(race_link)
            races.append((anchor.text, race_id, race_link))
    if races:
        return races


def get_event_id(link):

    match = re.search(r'eventId=.*', link)
    if match:
        event_id = match.group(0)[8:43]
    else:
        event_id = None
    return event_id

def get_meet_id(link):

    match = re.search(r'meetId=.*', link)
    if match:
        event_id = match.group(0)[8:43]
    else:
        event_id = None
    return event_id


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please provide a link")
    else:
        get_meets(sys.argv[1])