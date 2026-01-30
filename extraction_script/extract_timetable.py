import tabula
import pandas as pd
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
out_file = BASE_DIR / "data" / "data.json"

# Parameters
in_file  = 'extraction_script/WROLOGIO PROGRAMMA EAERINOY E3AMHNOY 2025-26.pdf'
out_file = BASE_DIR / "data.json"
version = "30/01/2026"  # or parse dynamically from the PDF

days_in  = ('ΔΕΥΤΕΡΑ', 'ΤΡΙΤΗ', 'ΤΕΤΑΡΤΗ', 'ΠΕΜΠΤΗ', 'ΠΑΡΑΣΚΕΥΗ')
days_out = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday')

# Read PDF
dfs = tabula.read_pdf(in_file, pages='all', multiple_tables=True, lattice=True)

schedule = {}

def parse_time_slot(entry):
    """Convert '9-11 ΑΜΦ ΣΟ (ΦΡΟΝΤ)' to {'start':9, 'end':11, 'classroom':'ΑΜΦ ΣΟ (ΦΡΟΝΤ)'}."""
    if pd.isna(entry):
        return None
    entry = str(entry).replace('\r(', ' ').replace(')', '').strip()
    # Separate time and classroom
    m = re.match(r'(\d+)[-:](\d+)\s*(.*)', entry)
    if m:
        start, end, room = m.groups()
        return {'start': int(start), 'end': int(end), 'classroom': room.strip()}
    else:
        # If only a note like (ΦΡΟΝΤ), keep it in classroom with dummy time
        return {'start': None, 'end': None, 'classroom': entry}

for i, df in enumerate(dfs):
    for _, row in df.iterrows():
        code = row.iloc[0]
        title = row.iloc[1] 
        teacher = row.iloc[2]
        if pd.notna(code):
            course = {
                "code": code,
                "title": title,
                "teacher": teacher,
                "teaching_slots": {}
            }
            DAY_COL_START = 3  # iloc index where Monday starts

            for i, day_out in enumerate(days_out):
                cell = row.iloc[DAY_COL_START + i]
                slot = parse_time_slot(cell)
                if slot:
                    course["teaching_slots"][day_out] = slot

            schedule[course["code"]] = course
            last_course = course

    if df.empty:
        cols = list(df.columns)
        code = cols[0]
        title = cols[1]
        teacher = cols[2]
        course = {
            "code": code,
            "title": title,
            "teacher": teacher,
            "teaching_slots": {}
        }
        DAY_COL_START = 3  # iloc index where Monday starts

        for i, day_out in enumerate(days_out):
            cell = cols[DAY_COL_START + i]
            slot = parse_time_slot(cell)
            print('slot from empty df:', slot)
            if slot:
                course["teaching_slots"][day_out] = slot

        if code not in schedule:
            schedule[code] = course
            last_course = course

# Write to JS file
data = {
    "version": version,
    "schedule": schedule  # your already-built schedule dictionary
}

with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Data extracted successfully to {out_file}")







