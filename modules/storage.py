import pandas as pd
from pathlib import Path
from datetime import date

LOG_PATH = Path("data/health_logs.csv")

COLUMNS = ["date", "weight_kg", "fasting_glucose_mg_dl", "hba1c_percent", "blood_pressure", "notes"]

def ensure_log_file():
    LOG_PATH.parent.mkdir(exist_ok=True)
    if not LOG_PATH.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(LOG_PATH, index=False)

def add_health_log(weight_kg=None, fasting_glucose=None, hba1c=None, blood_pressure="", notes=""):
    ensure_log_file()
    df = pd.read_csv(LOG_PATH)
    new_row = {
        "date": str(date.today()),
        "weight_kg": weight_kg,
        "fasting_glucose_mg_dl": fasting_glucose,
        "hba1c_percent": hba1c,
        "blood_pressure": blood_pressure,
        "notes": notes,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(LOG_PATH, index=False)

def load_health_logs():
    ensure_log_file()
    return pd.read_csv(LOG_PATH)
