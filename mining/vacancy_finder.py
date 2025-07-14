"""
Detect vacancies and optionally persist them.
Rules:
1. usage == 'vacant' OR NULL
2. business_name looks like “se alquila / for rent / traspaso / disponible …”
"""

import re
import pandas as pd
from dotenv import load_dotenv

from db.postgres import get_db_connection, mark_vacant

load_dotenv()

_RE_VACANT = re.compile(r"(?:se\s+alquila|for\s+rent|traspaso|disponible|vacant)", re.I)
_USAGE_EMPTY = {"vacant", "yes", "empty", None}


def _fetch() -> pd.DataFrame:
	with get_db_connection() as conn, conn.cursor() as cur:
		cur.execute("SELECT * FROM assets")
		return pd.DataFrame(cur.fetchall())


def detect() -> pd.DataFrame:
	df = _fetch()
	df["by_usage"] = df["usage"].isin(_USAGE_EMPTY)
	df["by_regex"] = df["business_name"].fillna("").str.contains(_RE_VACANT, regex=True)
	df["vacant_guess"] = df["by_usage"] | df["by_regex"] | df["is_vacant"]
	return df[df["vacant_guess"]]


def run(persist: bool = False) -> None:
    vac = detect()
    print(f"{len(vac)} potential vacancies")
    print(
        vac[["street_name", "address", "business_name"]]
        .head(40)
        .to_markdown()
    )

    if persist and not vac.empty:
        mark_vacant(vac["id"].tolist())
        print("DB updated ✔")


if __name__ == "__main__":          # direct call → behave like CLI helper
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--persist", action="store_true")
    run(**vars(p.parse_args()))
