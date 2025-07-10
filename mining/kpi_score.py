"""
StreetScore = 0.5*Tenant-Quality + 0.3*Density – 0.2*Vacancy‐Pressure
Tune the weightings in _USAGE_WEIGHT & _COEFS as business learns.

StreetScore = 0.5 × Tenant-Quality
            + 0.3 × Unit-Density
            – 0.2 × Vacancy-Pressure
"""

import logging
import pandas as pd
from dotenv import load_dotenv

from db.postgres import get_db_connection

load_dotenv()
_LOG = logging.getLogger(__name__)

_USAGE_WEIGHT = {
	"department_store": 4,
	"fashion": 3,
	"clothes": 3,
	"shoes": 2,
	"jewelry": 2,
	"supermarket": 1,
	"convenience": 1,
	"mobile_phone": 1,
	"books": 1,
	# vacant stock carries zero value
	"vacant": 0,
	None: 0,
}

_COEFS = dict(quality=0.5, units=0.3, vacants=-0.2)


def _fetch() -> pd.DataFrame:
	with get_db_connection() as conn, conn.cursor() as cur:
		cur.execute("SELECT * FROM assets")
		return pd.DataFrame(cur.fetchall())


def compute_scores() -> pd.DataFrame:
	df = _fetch()

	# infer vacancy if flag or usage == 'vacant'
	df["is_vacant_flag"] = df["is_vacant"] | (df["usage"] == "vacant")

	# tenant quality only for non-vacant
	df["quality_weight"] = df.apply(
		lambda r: 0 if r["is_vacant_flag"] else _USAGE_WEIGHT.get(r["usage"], 0),
		axis=1,
	)

	kpis = (
		df.groupby("street_name")
		.agg(
			units=("id", "count"),
			quality=("quality_weight", "sum"),
			vacants=("is_vacant_flag", "sum"),
			avg_size_m2=("surface_m2", "mean"),
		)
		.reset_index()
	)

	kpis["score"] = (
		kpis["quality"] * _COEFS["quality"]
		+ kpis["units"] * _COEFS["units"]
		+ kpis["vacants"] * _COEFS["vacants"]
	)

	return kpis.sort_values("score", ascending=False)


def main() -> None:
	print(compute_scores().to_markdown(index=False, floatfmt=".1f"))


if __name__ == "__main__":
	main()
