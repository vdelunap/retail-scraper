import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Iterable
from dotenv import load_dotenv
from models.asset import Asset


load_dotenv()

def get_db_connection():
	return psycopg2.connect(
		dbname=os.getenv("DB_NAME"),
		user=os.getenv("DB_USER"),
		password=os.getenv("DB_PASSWORD"),
		host=os.getenv("DB_HOST"),
		port=os.getenv("DB_PORT"),
		cursor_factory=RealDictCursor
	)

def insert_asset(asset: Asset):
	query = """
		INSERT INTO assets (street_name, address, ref_catastral, lat, lng, business_name, surface_m2, usage)
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
		ON CONFLICT (ref_catastral) DO NOTHING
	"""
	conn = None
	cursor = None

	try:
		conn = get_db_connection()
		cursor = conn.cursor()

		cursor.execute(query, (
			asset.street_name,
			asset.address,
			asset.ref_catastral,
			asset.lat,
			asset.lng,
			asset.business_name,
			asset.surface_m2,
			asset.usage
		))
		conn.commit()

	except Exception as e:
		if conn:
			conn.rollback()
		print(f"DB insert failed: {e}")
	finally:
		if cursor:
			cursor.close()
		if conn:
			conn.close()

def mark_vacant(ids: Iterable[str]) -> None:
	"""
	Set is_vacant = TRUE for the given asset UUIDs (or ref_catastral list
	if you prefer – keep UUID for brevity).
	"""
	if not ids:
		return

	query = """
		UPDATE assets
		SET is_vacant = TRUE
		WHERE id = ANY(%s::uuid[])
	"""
	with get_db_connection() as conn, conn.cursor() as cur:
		cur.execute(query, (list(map(str, ids)),))
		conn.commit()