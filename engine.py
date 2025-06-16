from sqlalchemy import create_engine, text
import pandas as pd
from config import sb_key, sb_url
import supabase
import json


if __name__ == '__main__':

    supabase = supabase.create_client(sb_url, sb_key)

    athlete_name = input("Enter the athlete's first and last name: ")
    grad_year = input("Enter the athlete's graduation year: ")
    team_name = input("Enter the athlete's team name: ")
    gender = input("Enter the athlete's gender: " )

    print("Finding similar athletes ...")

    find_athlete_query = """"
        select * from athlete where name = :athlete_name
        and team = :team and gender = :gender
        and graduation_year = :grad_year
        """

    target_athlete = supabase.table("athlete").select("id").eq('name', athlete_name).eq('graduation_year', grad_year).execute()

    athlete_id = target_athlete.data[0]['id']
    threshold = 10

    response = supabase.rpc("find_similar_athletes_3", {
        "target_athlete_id": athlete_id,
        "time_threshold": threshold
    }).execute()

    if response.data:
        for athlete in response.data:
            print(
                f"{athlete['name']} - Event: {athlete['event_id']} - Time: {athlete['time_seconds']}s - Δ: {athlete['delta']}")
    else:
        print("No similar athletes found.")

    # use only data of the same gender


# supabase doesn't support joins with python rn... so long term, we may want to figure that out...




