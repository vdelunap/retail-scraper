# Retail-Scraper “Gold Mine”

End-to-end, zero-cost data stack that turns **OpenStreetMap + Catastro** into a living
database of Madrid’s 300 busiest retail streets and mines it for opportunities.


OSM → Overpass ┐
│ enrich_with_cadastre
Catastro ← SOAP ┘ ↓
Postgres (assets)
↓
┌──────── CLI mining tools ────────┐
│ KPI / StreetScore • Vacancies │
│ Heat-map export • Extensible │
└──────────────────────────────────┘



---

## 1 · Quick start

```bash
# clone + install
python -m venv .venv && source .venv/bin/activate      # Win → .venv\Scripts\activate
pip install -r requirements.txt

# prepare Postgres (adjust db/credentials)
createdb invero
psql -d invero -f sql/schema.sql     # creates table `assets`

# set creds
cp .env.example .env   # edit DB_* vars

# build “La Mina” (first run takes an hour more or less)
python main.py

# mine it
python cli.py score                 # StreetScore ranking
python cli.py vacancy               # candidate empty units
python cli.py vacancy --persist     # …and flag them in DB
python cli.py heatmap               # exports street_heatmap.html

```


# 2 · Pipeline details
Stage	                File	                          What happens
Scrape	                services/overpass.py	          Top 300 streets (shop=* density) + every shop node/way per street
Enrich	                services/cadastre.py	          Lat/Lon ➜ ref. catastral, legal address, surface, land-use
Validate                models/asset.py	                  Pydantic schema (+ snapshot date & vacancy flag)
Load	                db/postgres.py::insert_asset	  UPSERT into assets (ref_catastral unique)
Vacancy	                mining/vacancy_finder.py	      Regex + usage heuristic ➜ is_vacant = true
KPIs	                mining/kpi_score.py	              StreetScore = 0.5·quality + 0.3·density – 0.2·vacancy
Visual	                mining/heatmap.py	              Folium heat-layer, weight = StreetScore per asset



# 3 · DB schema
CREATE TABLE assets (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  street_name   TEXT,
  address       TEXT,
  ref_catastral TEXT UNIQUE,
  lat           DOUBLE PRECISION,
  lng           DOUBLE PRECISION,
  business_name TEXT,
  surface_m2    INT,
  usage         TEXT,
  snapshot_date DATE      DEFAULT current_date,
  is_vacant     BOOLEAN   DEFAULT false,
  updated_at    TIMESTAMP DEFAULT now()
);



# 5 · StreetScore formula
StreetScore = 0.5 × Tenant-Quality
            + 0.3 × Unit-Density
            – 0.2 × Vacancy-Pressure
Tenant-Quality weights live in _USAGE_WEIGHT.
Coefficients in _COEFS – tune or train against rent data later.



# Future Implementations
- Pull asking €/m² from Idealista API, predict fair rent from StreetScore + footfall, rank gaps.
- Nightly Overpass diff; Event alert when node flips to vacant.