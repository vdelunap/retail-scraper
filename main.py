import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from tqdm import tqdm

from utils.logging_config import configure_logging
from services.overpass import get_top_commercial_streets, get_commercial_units_on_street
from services.cadastre import get_parcel_info
from db.postgres import insert_asset
from models.asset import Asset

# ---------- bootstrap ----------
load_dotenv()
configure_logging()
_LOG = logging.getLogger("main")
# -------------------------------


def enrich_with_cadastre(unit: dict) -> Asset | None:
	parcel = get_parcel_info(unit["lat"], unit["lng"])
	if parcel is None:
		return None

	return Asset(
		street_name=unit["street_name"],
		address=parcel["address"] or unit["address"],
		ref_catastral=parcel["ref_catastral"],
		lat=unit["lat"],
		lng=unit["lng"],
		business_name=unit["business_name"],
		surface_m2=parcel["surface_m2"] or unit["surface_m2"],
		usage=parcel["usage"] or unit["usage"],
	)


def main() -> None:
	_LOG.info("Discovering top Madrid commercial streets…")
	streets = get_top_commercial_streets(300)

	with ThreadPoolExecutor(max_workers=8) as pool:
		for street in tqdm(streets, desc="Streets"):
			units = get_commercial_units_on_street(street)
			futures = [pool.submit(enrich_with_cadastre, u) for u in units]

			for f in as_completed(futures):
				asset = f.result()
				if asset is None:
					continue
				insert_asset(asset)

	_LOG.info("Pipeline finished ✅")


if __name__ == "__main__":
	main()
