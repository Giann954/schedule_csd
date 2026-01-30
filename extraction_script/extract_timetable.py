import tabula
import pandas as pd
import json
import re

# Parameters
in_file  = ' extraction_script/WROLOGIO PROGRAMMA EAERINOY E3AMHNOY 2025-26.pdf'
out_file = 'data.json'
version = "30/01/2026"  # or parse dynamically from the PDF

days_in  = ('ΔΕΥΤΕΡΑ', 'ΤΡΙΤΗ', 'ΤΕΤΑΡΤΗ', 'ΠΕΜΠΤΗ', 'ΠΑΡΑΣΚΕΥΗ')
days_out = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday')

# Read PDF
df = tabula.read_pdf(in_file, pages='all', multiple_tables=False, stream=True)[0]

schedule = {}
last_course = None

def parse_time_slot(entry):
    """Convert '9-11 ΑΜΦ ΣΟ (ΦΡΟΝΤ)' to {'start':9, 'end':11, 'classroom':'ΑΜΦ ΣΟ (ΦΡΟΝΤ)'}."""
    if pd.isna(entry):
        return None
    entry = str(entry).strip()
    # Separate time and classroom
    m = re.match(r'(\d+)[-:](\d+)\s*(.*)', entry)
    if m:
        start, end, room = m.groups()
        return {'start': int(start), 'end': int(end), 'classroom': room.strip()}
    else:
        # If only a note like (ΦΡΟΝΤ), keep it in classroom with dummy time
        return {'start': None, 'end': None, 'classroom': entry}

for _, row in df.iterrows():
    code = row.iloc[0]
    title = row.iloc[1]
    teacher = row.iloc[2]

    if pd.notna(code):
        course = {
            'code': code,
            'title': title,
            'teacher': teacher,
            'teaching_slots': {}
        }
        for day_in, day_out in zip(days_in, days_out):
            slot = parse_time_slot(row[day_in])
            if slot:
                course['teaching_slots'][day_out] = slot
        schedule[code] = course
        last_course = course
    else:
        # Merge info like (ΦΡΟΝΤ) to previous course
        if last_course:
            for day_in, day_out in zip(days_in, days_out):
                if pd.notna(row[day_in]):
                    extra_slot = str(row[day_in]).strip()
                    if day_out in last_course['teaching_slots']:
                        last_course['teaching_slots'][day_out]['classroom'] += f" {extra_slot}"
                    else:
                        last_course['teaching_slots'][day_out] = {'start': None, 'end': None, 'classroom': extra_slot}

# Write to JS file
data = {
    "version": version,
    "schedule": schedule  # your already-built schedule dictionary
}

with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Data extracted successfully to {out_file}")


