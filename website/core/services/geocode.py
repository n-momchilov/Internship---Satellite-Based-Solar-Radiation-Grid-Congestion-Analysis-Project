from geopy.geocoders import Nominatim
from rapidfuzz import fuzz
from unidecode import unidecode
from ..config import BBOX

PLACES = ["Eindhoven","Tilburg","Breda","Helmond","'s-Hertogenbosch","Den Bosch", "Oss","Roosendaal","Bergen op Zoom","Waalwijk","Oosterhout","Veldhoven","Etten-Leur","Uden","Veghel","Boxtel","Best","Vught","Oirschot","Schijndel","Son en Breugel","Nuenen","Heeze-Leende","Geldrop","Mierlo","Goirle","Rijen","Dongen","Drunen","Sint-Oedenrode","Cuijk","Boxmeer","Veghel"]

def _norm(s): return unidecode((s or "").strip().lower())
def in_bbox(lat, lon, bbox=BBOX): return bbox[0] <= lat <= bbox[1] and bbox[2] <= lon <= bbox[3]

def geocode_osm(query, country="nl", limit=3, timeout=5):
    geo = Nominatim(user_agent="sis-demo-ui")
    try:
        res = geo.geocode(query, addressdetails=False, language="en",
                          country_codes=country, exactly_one=False,
                          limit=limit, timeout=timeout)
        return res or []
    except Exception:
        return []

def pick_best_hit(hits):
    if not hits: return None
    for h in hits:
        if in_bbox(h.latitude, h.longitude):
            return h
    return hits[0]

def fuzzy_suggest(query, choices=PLACES, k=5, min_score=70):
    qn = _norm(query)
    scored = [(name, fuzz.WRatio(qn, _norm(name))) for name in choices]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [name for name, score in scored[:k] if score >= min_score]
