import logging
import requests
from typing import Optional, Dict

_LOG = logging.getLogger(__name__)

_CADASTRE_URL = (
    "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/"
    "OVCCoordenadas.asmx/Consulta_RCCOOR"
)


def get_parcel_info(lat: float, lon: float) -> Optional[Dict]:
	"""
	Reverse-geocode (lat, lon) against Spanish Cadastre.
	Returns None when parcel not found.
	"""
	params = {
		"SRS": "EPSG:4326",
		"Coordenada_X": lon,
		"Coordenada_Y": lat,
	}
	try:
		resp = requests.get(_CADASTRE_URL, params=params, timeout=20)
		resp.raise_for_status()
	except Exception as exc:  # noqa: BLE001
		_LOG.warning("Cadastre lookup failed: %s", exc)
		return None

	# Response is XML; we’ll be lazy and just find substring tags
	if "<coord>" not in resp.text:
		return None

	def _extract(tag: str) -> str | None:
		open_tag, close_tag = f"<{tag}>", f"</{tag}>"
		if open_tag in resp.text:
			return resp.text.split(open_tag)[1].split(close_tag)[0].strip()
		return None

	refcat = _extract("pc1") + _extract("pc2") if _extract("pc1") else None
	address = _extract("ldt")
	usage = _extract("destino")
	surface = _extract("supe")  # superficie construida

	if not refcat:
		return None

	return {
		"ref_catastral": refcat,
		"address": address,
		"surface_m2": int(surface) if surface and surface.isdigit() else None,
		"usage": usage,
	}
