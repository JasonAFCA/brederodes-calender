from io import StringIO

import pandas as pd
import requests

URL = "https://www.brederodes.nl/273/uitslagen--programma/"

def get_matches() -> pd.DataFrame:
    response = requests.get(URL, timeout=15)
    response.raise_for_status()
    
    tables = pd.read_html(StringIO(response.text))
    
    for table in tables:
        required_columns = {"Datum", "Tijd", "Thuis", "Uit"}
        
        if required_columns.issubset(table.columns):
            return table
    
    raise ValueError("No matches found")

if __name__ == "__main__":
    matches = get_matches()
    print(matches.to_string(index=False))