from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
import numpy as np
import json
import re
from datetime import datetime
import pandas as pd
from config import sb_key, sb_url
from supabase import create_client, Client
from selenium.webdriver.support import expected_conditions as EC


# Takes in a list of tuples of events, and scrapes all of those events and puts the results in csvs, one per meet

def set_up(url):
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome"
    service = Service("/home/zack/byu/cs452/running/chromedriver-linux64/chromedriver")
    options.add_argument('--headless')  # run in background
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    sleep(0.5)
    return driver


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


def get_grad_year(grade: str, date:datetime)-> int:
    year = int(date.year)
    if grade == "Fr":
        return year + 4
    elif grade == "So":
        return year + 3
    elif grade == "Jr":
        return year + 2
    elif grade == "Sr":
        return year + 1
    else:
        return None


def safe_grad_year(row):
    try:
        year_val = row['Year']
        if isinstance(year_val, str):
            return get_grad_year(year_val.strip(), row['Date'])
    except Exception as e:
        print(f"Bad row: {row['Year']}, {row['Date']}, error: {e}")
        return None


def wait_for_table(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "tr"))
    )


def sel_scrape_event(url, meet_name, meet_id, event_name, event_id, location, gender, date, df_list):
    driver = set_up(url)
    wait_for_table(driver)
    rows = driver.find_elements("tag name", "tr")

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
            # else:
            #     print("Error: skipped malformed row")
                # print(values)

    df = pd.DataFrame(data, columns = columns)
    df["Time_Seconds"] = df["Time"].apply(time_to_seconds)
    df["Graduation_Year"] = df.apply(safe_grad_year, axis=1)
    df_list.append(df)




def sel_scrape_meet(url, meet_name, meet_id, location, date):
    driver = set_up(url)
    anchors = driver.find_elements("tag name", "a")
    links = []

    for anchor in anchors:
        if "Boys" in anchor.text:
            gender = "Boys"
            links.append((anchor.text, anchor.get_attribute("href"), gender))
        elif "Girls" in anchor.text:
            gender = "Girls"
            links.append((anchor.text, anchor.get_attribute("href"), gender))

    df_list = []
    for link in links[:5]:
        meet_url = link[1]
        match = re.search(r'eventId=.*', link[1])
        if match:
            event_id = match.group(0)[8:43]
        else:
            event_id = None
        sel_scrape_event(link[1], meet_name, meet_id, link[0], event_id, location, link[2], date, df_list)

    if df_list:
        combined_df = pd.concat(df_list)
        combined_df = combined_df.drop(combined_df.columns[8], axis = 1)
        athletes_df = combined_df[['Name', 'Graduation_Year', 'Team', 'Gender']].drop_duplicates()
        athletes_df = athletes_df.rename(columns={
            "Gender": "gender",
            "Graduation_Year": "graduation_year",
            "Name": "name",
            "Team": "team"
        })
        combined_df = combined_df.rename(columns={
            "Gender": "gender",
            "Graduation_Year": "graduation_year",
            "Name": "name",
            "Team": "team"
        })
        athletes_df['graduation_year'] = athletes_df['graduation_year'].astype('Int64')
        return combined_df, athletes_df



def process_year_doc(meet):
    pattern1 = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}'
    meet_id = re.search(pattern1, meet[4])
    if not meet_id:
        meet_id = re.search(r'\d{6,7}', meet[3])
    date_str = meet[3].split("--")[-1].strip()
    date = datetime.strptime(date_str, "%B %d, %Y").date()
    return date, meet_id


def multiset_diff(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:
    """
    Return rows in df_a minus those in df_b, counting duplicates:
      - if a row appears 3× in df_a and 1× in df_b, result has it 2×
      - if it appears <= times in df_b, it’s dropped entirely
    """
    # get value_counts Series for each
    vc_a = df_a.value_counts().rename("count_a")
    vc_b = df_b.value_counts().rename("count_b")

    # combine, subtract counts
    diff = (
        pd.concat([vc_a, vc_b], axis=1, sort=False)
          .fillna(0)
    )
    diff["leftover"] = (diff["count_a"] - diff["count_b"]).clip(lower=0)

    # keep only positive leftovers
    diff = diff[diff["leftover"] > 0]

    # rebuild a DataFrame by repeating each row ‘leftover’ times
    rows = []
    for idx, row in diff.iterrows():
        # idx is a tuple of column-values in the same order as df.columns
        for _ in range(int(row["leftover"])):
            rows.append(dict(zip(df_a.columns, idx)))

    return pd.DataFrame(rows, columns=df_a.columns)


"""takes in a json file that contains the links to all meets in a year, and scrapes them"""
def scrape_year(filename: str, batch_start: int, batch_end: int):
    with open(filename, "r") as file:
        json_string = file.read()
        meets = json.loads(json_string)


    supabase: Client = create_client(sb_url, sb_key)
    response = supabase.table("athlete").select("*").execute()
    athlete_df = pd.DataFrame(response.data)

    for i, meet in enumerate(meets[batch_start:batch_end]):
        date, meet_id = process_year_doc(meet)

        meet_performances_df, meet_athlete_df = sel_scrape_meet(url=meet[4], meet_name=meet[0], meet_id=meet_id.group(0), location=meet[2], date=date)
        # find new athletes
        cols = ["name", "graduation_year", "team", "gender"]
        new_athletes = multiset_diff(meet_athlete_df[cols], athlete_df[cols])
        new_athletes.drop_duplicates(inplace=True)
        if not new_athletes.empty:

            new_athletes['graduation_year'] = new_athletes['graduation_year'].astype('Int64')
            records = new_athletes.to_dict(orient="records")
            supabase.table("athlete").insert(records).execute()
        athlete_df = pd.DataFrame(
            supabase.table("athlete").select("*").execute().data
        )

        sleep(2)
        res = supabase.table("athlete").select("*").execute()
        updated_athletes = pd.DataFrame(res.data)
        merged_df = pd.merge(meet_performances_df, updated_athletes, on= ['gender', 'name', 'team', 'graduation_year'], how = 'inner')
        merged_df['graduation_year'] = merged_df['graduation_year'].astype('Int64')
        merged_df['Date'] = merged_df['Date'].astype(str)
        cols_to_keep = ['Date', 'Event_ID', 'Meet_ID', "Place", "Team_Place", "Time_Seconds", "id"]
        merged_df = merged_df[cols_to_keep]
        merged_df = merged_df.rename(columns = {
            "Date": "date",
            "Event_ID": "event_id",
            "Meet_ID": "meet_id",
            "Place": "place",
            "Team_Place": "team_place",
            "Time_Seconds": "time_seconds",
            "id": "athlete_id"
        })

        merged_df = merged_df[np.isfinite(merged_df.select_dtypes(include=[np.number])).all(axis=1)]


        records = merged_df.to_dict(orient="records")
        print(merged_df.columns.tolist())

        print(records[:3])
        supabase.table("performance").insert(records).execute()



scrape_year("2022_meets.json", 0, 2)



