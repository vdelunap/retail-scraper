def compute_asset_score(asset) -> float:
	score = 0

	if asset.usage and "comercial" in asset.usage.lower():
		score += 2

	if asset.surface_m2 and asset.surface_m2 >= 100:
		score += 1

	if "Gran Vía" in asset.street_name:
		score += 2

	return score
