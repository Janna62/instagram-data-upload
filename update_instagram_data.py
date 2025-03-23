import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

# === Конфигурация ===
EXPORTS_FOLDER = "/Users/janna.c/MetaAnalytics/new_exports"
COMBINED_FILE = "/Users/janna.c/MetaAnalytics/instagram_combined_insights.csv"
CREDENTIALS_FILE = "/Users/janna.c/MetaAnalytics/credentials.json"
SPREADSHEET_NAME = "Instagram Insights"
WORKSHEET_NAME = "Сводка"

# === Шаг 1: Объединяем файлы ===
file_map = {
    "followers.csv": "Followers",
    "reach.csv": "Reach",
    "interactions.csv": "Interactions",
    "profile_views.csv": "Profile Views",
    "website_clicks.csv": "Website Clicks",
    "visits.csv": "Visits"
}

frames = []
for filename, metric in file_map.items():
    path = os.path.join(EXPORTS_FOLDER, filename)
    try:
        df = pd.read_csv(path, encoding="utf-16")
        df.columns = ["Date", metric]
        frames.append(df)
    except Exception as e:
        print(f"⚠️ Не удалось прочитать {filename}: {e}")

if not frames:
    print("❌ Нет данных для объединения. Проверь содержимое папки.")
    exit(1)

# Объединяем по дате
combined_df = frames[0]
for df in frames[1:]:
    combined_df = pd.merge(combined_df, df, on="Date", how="outer")

combined_df["Date"] = pd.to_datetime(combined_df["Date"], dayfirst=True, errors="coerce")
combined_df = combined_df.sort_values("Date")
combined_df.to_csv(COMBINED_FILE, index=False)
print("✅ CSV-файл объединён.")

# === Шаг 2: Загрузка в Google Таблицу ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

sheet = client.open(SPREADSHEET_NAME)
try:
    worksheet = sheet.worksheet(WORKSHEET_NAME)
except:
    worksheet = sheet.add_worksheet(title=WORKSHEET_NAME, rows="1000", cols="20")

worksheet.clear()
rows = [combined_df.columns.tolist()] + combined_df.fillna("").astype(str).values.tolist()
worksheet.update("A1", rows)
print("✅ Данные загружены в Google Таблицу.")

# === Шаг 3: Вызов Apps Script для обновления графика ===
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzBSWHonna3R5e6cOPg68Ey1osXH6dHOQjefw0JEGHX2I6ti1vPTEEcvb6b2m4hN3Dq/exec"
try:
    response = requests.get(SCRIPT_URL)
    if response.status_code == 200:
        print("📈 График обновлён через Apps Script!")
    else:
        print(f"⚠️ Ошибка вызова Apps Script: {response.status_code}")
except Exception as e:
    print(f"⚠️ Не удалось вызвать Apps Script: {e}")
