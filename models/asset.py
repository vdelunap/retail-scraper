from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date


class Asset(BaseModel):
	id: Optional[UUID] = None
	street_name: str
	address: str
	ref_catastral: str
	lat: float
	lng: float
	business_name: Optional[str] = None
	surface_m2: Optional[int] = None
	usage: Optional[str] = None
	snapshot_date: date = date.today()
	is_vacant: bool = False
