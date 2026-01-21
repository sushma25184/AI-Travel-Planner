import pandas as pd
import json
import os

INPUT_CSV = "data/places.csv"
OUTPUT_JSON = "places_kaggle.json"

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"❌ File not found: {INPUT_CSV}")
        print("👉 Put your Kaggle CSV as backend/data/places.csv")
        return

    df = pd.read_csv(INPUT_CSV)

    print("✅ Columns found in your dataset:")
    print(list(df.columns))

    # Auto-detect city and place columns (works for most datasets)
    city_col = None
    name_col = None

    for c in df.columns:
        lc = c.lower().strip()
        if city_col is None and lc in ["city", "destination", "district", "location", "state"]:
            city_col = c
        if name_col is None and lc in ["place", "place_name", "tourist_place", "attraction", "name", "spot"]:
            name_col = c

    # Fallback: partial match
    if city_col is None:
        for c in df.columns:
            if "city" in c.lower() or "district" in c.lower() or "location" in c.lower() or "state" in c.lower():
                city_col = c
                break

    if name_col is None:
        for c in df.columns:
            if "place" in c.lower() or "attraction" in c.lower() or "spot" in c.lower() or "name" in c.lower():
                name_col = c
                break

    if city_col is None or name_col is None:
        print("❌ Could not detect city/place columns automatically.")
        print("👉 Send me the columns list shown above, I will fix it.")
        return

    # Optional columns
    category_col = None
    rating_col = None
    cost_col = None

    for c in df.columns:
        lc = c.lower()
        if category_col is None and ("category" in lc or "type" in lc or "tag" in lc):
            category_col = c
        if rating_col is None and ("rating" in lc or "star" in lc):
            rating_col = c
        if cost_col is None and ("cost" in lc or "fee" in lc or "price" in lc or "entry" in lc):
            cost_col = c

    clean = pd.DataFrame()
    clean["city"] = df[city_col].astype(str).str.strip()
    clean["name"] = df[name_col].astype(str).str.strip()

    if category_col:
        clean["category"] = df[category_col].astype(str).str.strip().str.lower()
    else:
        clean["category"] = "general"

    if rating_col:
        clean["rating"] = pd.to_numeric(df[rating_col], errors="coerce").fillna(0).round(1)
    else:
        clean["rating"] = 0

    if cost_col:
        clean["avg_cost"] = pd.to_numeric(df[cost_col], errors="coerce").fillna(0).astype(int)
    else:
        clean["avg_cost"] = 0

    # Remove empty + duplicates
    clean = clean[(clean["city"] != "") & (clean["name"] != "")]
    clean = clean.drop_duplicates(subset=["city", "name"])

    records = clean.to_dict(orient="records")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"✅ Created: {OUTPUT_JSON}")
    print(f"✅ Total places: {len(records)}")
    print("✅ Sample:", records[:5])

if __name__ == "__main__":
    main()
