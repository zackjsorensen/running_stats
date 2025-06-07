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
from datetime import datetime
import os
import pandas as pd


# Takes in a list of tuples of events, and scrapes all of those events and puts the results in csvs, one per meet

def time_to_seconds(time_str):
    if not time_str or time_str.strip() in {"", "DNF", "DNS"}:
        return float('nan')  # or float('nan') if preferred
    try:
        parts = time_str.strip().split(":")
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 1:
            return float(parts[0])  # just seconds
        else:
            return None
    except:
        return None


def get_grad_year(grade: str, date:datetime):
    year = date.year
    if grade == "Fr":
        return year + 4
    elif grade == "So":
        return year + 3
    elif grade == "Jr":
        return year + 2
    elif grade == "Sr":
        return year + 1
    else:
        return float('nan')


def sel_scrape_event(url, meet_name, meet_id, event_name, event_id, location, gender, date, i):
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome"
    service = Service("/home/zack/byu/cs452/running/chromedriver-linux64/chromedriver")
    options.add_argument('--headless')  # run in background
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    sleep(2)

    if meet_id is None:
        meet_id = float('nan')
    if event_id is None:
        event_id = float('nan')

    rows = driver.find_elements("tag name", "tr")

    all_data = []
    data = []
    columns = []
    for j, row in enumerate(rows):
        cells = row.find_elements("tag name", "th")  or row.find_elements("tag name", "td")
        values = [cell.text.strip() for cell in cells]
        if not values:
            continue

        if j == 0:
            if 'Team' in values:
                index = values.index('Team')
                values = values[:index] + ['Team_Place', 'Team'] + values[index + 1:]
            columns = values + ["Meet_Name", "Meet_ID", "Event_Name", "Event_ID", "Location", "Gender", "Date"]

        else:
            values += [meet_name, meet_id, event_name, event_id, location, gender, date]
            if len(values) == len(columns):

                data.append(values)
            else:
                print("Error: skipped malformed row")
                print(values)

    df = pd.DataFrame(data, columns = columns)
    df["Time_Seconds"] = df["Time"].apply(time_to_seconds)

    pd.set_option('display.max_columns', None)
    print(df.head(20))


    # bucket = i//10
    # directory_name = "data_" + str(bucket)
    # os.makedirs(directory_name, exist_ok=True)
    #
    # # filename =  "data_" + str(bucket) + "/" + meet_name + ".csv"
    # with open(os.path.join(directory_name, (meet_name) + ".csv"), "w") as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(header)
    #     writer.writerows(all_data)


def sel_scrape_meet(url, meet_name, meet_id, location, date, i):
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome"
    service = Service("/home/zack/byu/cs452/running/chromedriver-linux64/chromedriver")
    options.add_argument('--headless')  # run in background
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    sleep(2)
    anchors = driver.find_elements("tag name", "a")
    links = []

    gender = "None"
    for anchor in anchors:
        if "Boys" in anchor.text:
            gender = "Boys"
            links.append((anchor.text, anchor.get_attribute("href"), gender))
        elif "Girls" in anchor.text:
            gender = "Girls"
            links.append((anchor.text, anchor.get_attribute("href"), gender))


    for link in links[:2]:

        match = re.search(r'eventId=.*', link[1])
        if match:
            event_id = match.group(0)[8:43]
        else:
            event_id = "None"
        sel_scrape_event(link[1], meet_name, meet_id, link[0], event_id, location, link[2], date, i)



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please provide a filename containing the json string")
    else:
        with open(sys.argv[1], "r") as file:
            json_string = file.read()
            meets = json.loads(json_string)
            for i, meet in enumerate(meets[:2]):
                pattern1 = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}'
                meet_id = re.search(pattern1, meet[3])
                if not meet_id:
                    meet_id = re.search(r'\d{6,7}', meet[3])
                date_str = meet[2].split("--")[-1].strip()
                date = datetime.strptime(date_str, "%B %d, %Y").date()

                sel_scrape_meet(url = meet[3], meet_name = meet[0], meet_id=meet_id.group(0), location = meet[1], date = date, i =i)

