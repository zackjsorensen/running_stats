import requests
import html
import json
import re
import csv


# level one data scraping - an event within a meet, at the results page

# let's make this take the meet id and the event id as args,

def scrape_event(meet_id: int, event_id: int):
    url = "https://meettrax.com/meets/" + str(meet_id) + "/results/by-event/" + str(event_id)
    res = requests.get(url)
    # Step 1: Decode HTML entities
    html_decoded = html.unescape(res.text)

    pattern = r'"op_meet_event_round_results"\s*:\s*(\{.*?\})\s*,\s*"meta":'
    match = re.search(pattern, html_decoded, re.DOTALL)

    if match:
        result = match.group(1) + "}}"
        # print(result)
    else:
        print("Phrase not found.")

    # Step 2: Parse as JSON (if it's a valid JSON string)
    try:
        data = json.loads(result)
        # print(json.dumps(data, indent=4))
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)

    max_splits = max(len(athlete.get("splits", [])) for athlete in data["results"]["data"])

    fieldnames = [
        "id",
        "meet_event_entry_id",
        "team_name",
        "athlete_first_name",
        "athlete_last_name",
        "athlete_grade",
        "points",
        "meet_event_round_place",
        "split_1_mark_raw"
    ]

    split_fields = [f"split_{i+1}" for i in range(max_splits)]

    fieldnames = fieldnames + split_fields


    # Step 3: Write CSV
    filename = "meet_" + str(meet_id) + "_raw_data.csv"

    with open(filename, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for athlete in data["results"]["data"]:
            row = {key: athlete.get(key) for key in fieldnames}

            for i in range(max_splits):
                if i < len(athlete.get("splits", [])):
                    row[f"split_{i+1}"] = athlete["splits"][i]["mark"]["mark_raw"]
                else:
                    row[f"split_{i+1}"] = None

            writer.writerow(row)

def get_event_ids(meet_id):
    url = "https://meettrax.com/meets/" + str(meet_id) + "/results/by-event"
    res = requests.get(url)
    # print(res.text)
    # print("roar")
    html_decoded = html.unescape(res.text)
    # print(html_decoded)

    pattern = r'("data"\s*:\s*)\[\s*.*?\s*\](?=\s*,\s*"links")'
    match = re.search(pattern, html_decoded, re.DOTALL)

    if match:
        result = "{" + match.group(0) + "}"
        # print(result)
    else:
        print("Phrase not found.")

    id_data = json.loads(result)
    # print(id_data)

    ids = [event["id"] for event in id_data["data"]]
    return ids

# TODO: extract splits -- may need to visit each athlete's result and do it there....

def scrape_meet(meet_id: int):
    ids = get_event_ids(meet_id)
    for id in ids:
        scrape_event(meet_id, id)

# scrape_event(387, 15087)
# scrape_meet(351)

# https://meettrax.com/sports/xc?sight=past%25levels%3Dcollege&name=&groups[level][]=high_school

def scrape_hs_date_range(start_date, end_date):
    url = ("https://meettrax.com/sports/xc?date_from=" + start_date +
           "&date_to=" + end_date + "&groups%5Blevel%5D%5B0%5D=high_school&sight=past&state=UT")
    res = requests.get(url)
    decoded = html.unescape(res.text)
    match = re.search(r'"meets":.*?"total":(.*?)"filters"', decoded, re.DOTALL)
    result = match.group(0)
    result = "{" + result[:-11] + "}}"
    # print(result)
    # print(json.loads(result))
    data = json.loads(result)
    meet_ids = []
    for meet in data['meets']['list']:
        meet_ids.append((meet['name'], meet['id']))
    with open("meet_info.txt", "a") as f:
        f.write(str(meet_ids))
    print(len(meet_ids))
    # get the data btwn first "meets": and "filters"

dates = [
    "2022-06-01", "2022-06-29", "2022-07-27", "2022-08-24", "2022-09-21", "2022-10-19", "2022-11-16", "2022-12-14",
    "2023-06-01", "2023-06-29", "2023-07-27", "2023-08-24", "2023-09-21", "2023-10-19", "2023-11-16", "2023-12-14",
    "2024-06-01", "2024-06-29", "2024-07-27", "2024-08-24", "2024-09-21", "2024-10-19", "2024-11-16", "2024-12-14",
    "2025-06-01", "2025-06-29", "2025-07-27", "2025-08-24", "2025-09-21", "2025-10-19", "2025-11-16", "2025-12-14"
]

def get_data():
    for i in range(len(dates)-1):
        scrape_hs_date_range(dates[i], dates[i+1])
        i+= 1

get_data()