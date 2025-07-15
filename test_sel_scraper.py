from config import sb_key, sb_url
from supabase import create_client, Client
import pandas as pd
from sel_scraper import diff_2



def set_up():
    supabase: Client = create_client(sb_url, sb_key)
    return supabase

def test_diff_2():
    supabase = set_up()


    df = make_dummy_df()
    result = diff_2(df, supabase)
    print(result)
    assert result is not None
    assert len(result) < 9


def make_dummy_df():
    # Original data
    data = {
        'number': [426, 427, 428, 429, 430, 431, 432],
        'team': ['Ogden HS', 'Carbon HS', 'Carbon HS', 'Carbon HS', 'Morgan HS', 'Ogden HS', 'Carbon HS'],
        'gender': ['Girls'] * 7,
        'name': [
            'Malyn Eliason', 'Aly Bryner', 'Kaylee Pitcher',
            'Alexa Jones', 'Eliza Keller', 'Eliza Bohne', 'Briella Hatch'
        ],
        'graduation_year': [2025, 2026, 2026, 2026, 2025, 2026, 2026]
    }
    df = pd.DataFrame(data)
    new_rows = [
        {'number': 101, 'team': 'Wallaby HS', 'gender': 'Girls', 'name': 'Reese Jordonson',
         'graduation_year': 2083},
        {'number': 101, 'team': 'Carbon HS', 'gender': 'Girls', 'name': 'Jojo Marks', 'graduation_year': 2025}
    ]
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    return df
