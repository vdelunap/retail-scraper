"""
Plot each asset as a point whose intensity = its street's StreetScore.
Dots sit on the actual property, identical tone across the same street.
"""

import folium
from folium.plugins import HeatMap
import pandas as pd

from mining.kpi_score import compute_scores
from db.postgres import get_db_connection


def _fetch_assets() -> pd.DataFrame:
	with get_db_connection() as conn, conn.cursor() as cur:
		cur.execute("SELECT street_name, lat, lng FROM assets")
		return pd.DataFrame(cur.fetchall())


def build(path="street_heatmap.html") -> str:
	streets = compute_scores()[["street_name", "score"]]
	assets = _fetch_assets()
	assets = assets.merge(streets, on="street_name", how="left").dropna(subset=["score"])

	# normalise score to 0-1 for heatmap weight
	s_min, s_max = assets["score"].min(), assets["score"].max()
	assets["w"] = (assets["score"] - s_min) / max(1, s_max - s_min)

	m = folium.Map(location=[40.42, -3.7], zoom_start=12)
	HeatMap(data=assets[["lat", "lng", "w"]].values.tolist(), max_zoom=15).add_to(m)
	m.save(path)
	return path


if __name__ == "__main__":
	print("Heatmap saved →", build())
