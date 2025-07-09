import logging
import time
from collections import Counter
from typing import List, Dict

import requests
from shapely.geometry import shape

_LOG = logging.getLogger(__name__)

# Madrid municipality → relation 5326784
_RELATION_ID = 5_326_784
_AREA_ID = 3_600_000_000 + _RELATION_ID          # 3.6 b offset converts relation→area
_OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _query_overpass(query: str) -> dict:
	for attempt in range(3):
		resp = requests.post(_OVERPASS_URL, data=query, timeout=140)
		if resp.ok:
			return resp.json()
		_LOG.warning("Overpass error %s – retrying (%s/3)", resp.status_code, attempt + 1)
		time.sleep(5)
	raise RuntimeError(f"Overpass failed: {resp.text[:200]}...")


def get_top_commercial_streets(limit: int = 300) -> List[str]:
	query = f"""
		[out:json][timeout:1200];
		area({_AREA_ID})->.searchArea;
		(
		  node["shop"](area.searchArea);
		  way["shop"](area.searchArea);
		);
		out center tags;
	"""
	data = _query_overpass(query)

	street_counts = Counter(
		el["tags"].get("addr:street")
		for el in data["elements"]
		if el["tags"].get("addr:street")
	)

	top = [s for s, _ in street_counts.most_common(limit)]
	_LOG.info("Identified %s candidate commercial streets", len(top))
	return top


def get_commercial_units_on_street(street: str) -> List[Dict]:
	escaped = street.replace('"', r"\"")
	query = f"""
		[out:json][timeout:600];
		area({_AREA_ID})->.searchArea;
		(
		  node["shop"]["addr:street"="{escaped}"](area.searchArea);
		  way["shop"]["addr:street"="{escaped}"](area.searchArea);
		);
		out center tags;
	"""
	data = _query_overpass(query)
	results = []
	for el in data["elements"]:
		lat = el.get("lat") or el.get("center", {}).get("lat")
		lon = el.get("lon") or el.get("center", {}).get("lon")
		if lat is None or lon is None:
			continue
		results.append(
			{
				"street_name": street,
				"lat": lat,
				"lng": lon,
				"address": _compose_address(el["tags"]),
				"business_name": el["tags"].get("name"),
				"usage": el["tags"].get("shop"),
				"surface_m2": _polygon_area(el) if el["type"] == "way" else None,
			}
		)
	return results


def _compose_address(tags: dict) -> str:
	return ", ".join(
		part for part in (
			tags.get("addr:street"),
			tags.get("addr:housenumber"),
			tags.get("addr:postcode"),
			"Madrid"
		) if part
	)


def _polygon_area(el: dict) -> int | None:
	if "geometry" not in el:
		return None
	coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
	try:
		return int(shape({"type": "Polygon", "coordinates": [coords]}).area * 10_000_000)
	except Exception:
		return None
