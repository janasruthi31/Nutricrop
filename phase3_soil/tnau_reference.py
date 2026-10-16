"""
Reference data for Phase 3.

SOURCE OF THE FERTILITY RATING THRESHOLDS
  Supplied by the project owner as the Tamil Nadu ratings of TNAU, citing
  https://agritech.tnau.ac.in/pdf/2.pdf (Tables 1 & 2). The text layer of that PDF refers to these tables
  but does not expose their numbers, so the values below were NOT independently re-verified from the PDF text.
  Verify against the printed tables before production use.

These are soil-STATUS classes only. They are never fertilizer doses.
"""

# (low_upper_exclusive, high_lower_exclusive). value < low -> Low ; low <= value <= high -> Medium ; value > high -> High
TNAU_RATINGS = {
    "organic_carbon": {"unit": "%",     "method": None,    "low": 0.5,  "high": 0.75},
    "nitrogen":       {"unit": "kg/ha", "method": None,    "low": 280.0, "high": 450.0},
    "phosphorus":     {
        "unit": "kg/ha",
        "Olsen": {"low": 11.0, "high": 22.0},
        "Bray":  {"low": 24.2, "high": 49.7},
    },
    "potassium":      {"unit": "kg/ha", "method": None,    "low": 118.0, "high": 280.0},
}
TNAU_SOURCE = "TNAU Tamil Nadu soil fertility ratings (https://agritech.tnau.ac.in/pdf/2.pdf, Tables 1-2; as supplied by project owner)"

# field key -> display label, kind
FIELDS = {
    "nitrogen":       {"label": "Nitrogen (N)",          "primary": True,  "units": ["kg/acre", "kg/ha", "mg/kg"], "canonical": "kg/ha"},
    "phosphorus":     {"label": "Phosphorus (P)",        "primary": True,  "units": ["kg/acre", "kg/ha", "mg/kg"], "canonical": "kg/ha"},
    "potassium":      {"label": "Potassium (K)",         "primary": True,  "units": ["kg/acre", "kg/ha", "mg/kg"], "canonical": "kg/ha"},
    "ph":             {"label": "pH",                    "primary": True,  "units": [None],                         "canonical": None},
    "organic_carbon": {"label": "Organic Carbon (OC)",   "primary": True,  "units": ["%", "g/kg"],                  "canonical": "%"},
    "ec":             {"label": "Electrical Conductivity (EC)", "primary": False, "units": ["dS/m", "uS/cm", "mS/cm"], "canonical": "dS/m"},
    "sulphur":        {"label": "Sulphur (S)",           "primary": False, "units": ["kg/acre", "kg/ha", "mg/kg"], "canonical": "mg/kg"},
    "zinc":           {"label": "Zinc (Zn)",             "primary": False, "units": ["kg/acre", "mg/kg", "ppm"],   "canonical": "mg/kg"},
    "iron":           {"label": "Iron (Fe)",             "primary": False, "units": ["kg/acre", "mg/kg", "ppm"],   "canonical": "mg/kg"},
    "manganese":      {"label": "Manganese (Mn)",        "primary": False, "units": ["kg/acre", "mg/kg", "ppm"],   "canonical": "mg/kg"},
    "copper":         {"label": "Copper (Cu)",           "primary": False, "units": ["kg/acre", "mg/kg", "ppm"],   "canonical": "mg/kg"},
    "boron":          {"label": "Boron (B)",             "primary": False, "units": ["kg/acre", "mg/kg", "ppm"],   "canonical": "mg/kg"},
}
PRIMARY = [k for k, v in FIELDS.items() if v["primary"]]
P_METHODS = ["Olsen", "Bray"]

# Plausibility bounds. ENGINEERING GUARDS ONLY (not TNAU ratings, not agronomic advice).
# hard = physically impossible outside -> INVALID.  soft = unusual -> UNCERTAIN/warning, farmer may still confirm.
PLAUSIBILITY = {
    ("nitrogen", "kg/ha"):       {"hard": (0, 5000),  "soft": (20, 1000)},
    ("nitrogen", "kg/acre"):     {"hard": (0, 2500),  "soft": (8, 500)},
    ("nitrogen", "mg/kg"):       {"hard": (0, 5000),  "soft": (5, 500)},
    ("phosphorus", "kg/ha"):     {"hard": (0, 2000),  "soft": (0.5, 250)},
    ("phosphorus", "kg/acre"):   {"hard": (0, 1000),  "soft": (0.2, 120)},
    ("phosphorus", "mg/kg"):     {"hard": (0, 2000),  "soft": (0.5, 150)},
    ("potassium", "kg/ha"):      {"hard": (0, 5000),  "soft": (20, 1500)},
    ("potassium", "kg/acre"):    {"hard": (0, 2500),  "soft": (8, 700)},
    ("potassium", "mg/kg"):      {"hard": (0, 5000),  "soft": (10, 800)},
    ("ph", None):                {"hard": (0, 14),    "soft": (3.5, 10.0)},
    ("organic_carbon", "%"):     {"hard": (0, 60),    "soft": (0.05, 3.0)},
    ("organic_carbon", "g/kg"):  {"hard": (0, 600),   "soft": (0.5, 30.0)},
    ("ec", "dS/m"):              {"hard": (0, 60),    "soft": (0, 8)},
    ("ec", "uS/cm"):             {"hard": (0, 60000), "soft": (0, 8000)},
    ("ec", "mS/cm"):             {"hard": (0, 60),    "soft": (0, 8)},
    ("sulphur", "kg/acre"):      {"hard": (0, 2500),  "soft": (0, 100)},
    ("sulphur", "mg/kg"):        {"hard": (0, 5000),  "soft": (0, 200)},
    ("sulphur", "kg/ha"):        {"hard": (0, 5000),  "soft": (0, 200)},
    ("zinc", "kg/acre"):         {"hard": (0, 500),   "soft": (0, 15)},
    ("zinc", "mg/kg"):           {"hard": (0, 1000),  "soft": (0, 30)},
    ("zinc", "ppm"):             {"hard": (0, 1000),  "soft": (0, 30)},
    ("iron", "kg/acre"):         {"hard": (0, 2500),  "soft": (0, 120)},
    ("iron", "mg/kg"):           {"hard": (0, 5000),  "soft": (0, 250)},
    ("iron", "ppm"):             {"hard": (0, 5000),  "soft": (0, 250)},
    ("manganese", "kg/acre"):    {"hard": (0, 1000),  "soft": (0, 75)},
    ("manganese", "mg/kg"):      {"hard": (0, 2000),  "soft": (0, 150)},
    ("manganese", "ppm"):        {"hard": (0, 2000),  "soft": (0, 150)},
    ("copper", "kg/acre"):       {"hard": (0, 500),   "soft": (0, 25)},
    ("copper", "mg/kg"):         {"hard": (0, 1000),  "soft": (0, 50)},
    ("copper", "ppm"):           {"hard": (0, 1000),  "soft": (0, 50)},
    ("boron", "kg/acre"):        {"hard": (0, 100),   "soft": (0, 10)},
    ("boron", "mg/kg"):          {"hard": (0, 200),   "soft": (0, 10)},
    ("boron", "ppm"):            {"hard": (0, 200),   "soft": (0, 10)},
}

TN_DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode",
    "Kallakurichi", "Kancheepuram", "Kanniyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
    "Nagapattinam", "Namakkal", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivagangai",
    "Tenkasi", "Thanjavur", "The Nilgiris", "Theni", "Thoothukudi", "Tiruchirapalli", "Tirunelveli", "Tirupathur",
    "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Villupuram", "Virudhunagar",
]  # same 38 names as the Phase 2 yield-model metadata, so Phase 3/2 district strings match
DISTRICT_ALIASES = {
    "trichy": "Tiruchirapalli", "tiruchirappalli": "Tiruchirapalli", "tiruchirapalli": "Tiruchirapalli",
    "tiruchi": "Tiruchirapalli", "villupuram": "Villupuram", "viluppuram": "Villupuram",
    "kanchipuram": "Kancheepuram", "kancheepuram": "Kancheepuram", "kanyakumari": "Kanniyakumari",
    "kanniyakumari": "Kanniyakumari", "nilgiris": "The Nilgiris", "the nilgiris": "The Nilgiris",
    "tuticorin": "Thoothukudi", "thoothukkudi": "Thoothukudi", "thiruvallur": "Tiruvallur",
    "tiruvallur": "Tiruvallur", "thiruvarur": "Tiruvarur", "tiruvarur": "Tiruvarur",
    "thiruvannamalai": "Tiruvannamalai", "tirupur": "Tiruppur", "tiruppur": "Tiruppur",
    "pudukottai": "Pudukkottai", "sivaganga": "Sivagangai", "thanjavur": "Thanjavur", "tanjore": "Thanjavur",
    "tirunelveli": "Tirunelveli", "tirupattur": "Tirupathur", "tirupathur": "Tirupathur",
    "virudunagar": "Virudhunagar", "ramnad": "Ramanathapuram", "nagapatinam": "Nagapattinam",
    "ஈரோடு": "Erode", "கோயம்புத்தூர்": "Coimbatore", "கோவை": "Coimbatore", "திருப்பூர்": "Tiruppur",
    "சேலம்": "Salem", "மதுரை": "Madurai", "திண்டுக்கல்": "Dindigul", "திருச்சிராப்பள்ளி": "Tiruchirapalli",
    "திருச்சி": "Tiruchirapalli", "தஞ்சாவூர்": "Thanjavur", "திருநெல்வேலி": "Tirunelveli",
    "வேலூர்": "Vellore", "விழுப்புரம்": "Villupuram", "கடலூர்": "Cuddalore", "தருமபுரி": "Dharmapuri",
    "கிருஷ்ணகிரி": "Krishnagiri", "நாமக்கல்": "Namakkal", "கரூர்": "Karur", "பெரம்பலூர்": "Perambalur",
    "அரியலூர்": "Ariyalur", "புதுக்கோட்டை": "Pudukkottai", "சிவகங்கை": "Sivagangai", "ராமநாதபுரம்": "Ramanathapuram",
    "விருதுநகர்": "Virudhunagar", "தூத்துக்குடி": "Thoothukudi", "கன்னியாகுமரி": "Kanniyakumari", "தேனி": "Theni",
    "நீலகிரி": "The Nilgiris", "திருவள்ளூர்": "Tiruvallur", "காஞ்சிபுரம்": "Kancheepuram",
    "செங்கல்பட்டு": "Chengalpattu", "ராணிப்பேட்டை": "Ranipet", "திருப்பத்தூர்": "Tirupathur",
    "கள்ளக்குறிச்சி": "Kallakurichi", "மயிலாடுதுறை": "Mayiladuthurai", "திருவாரூர்": "Tiruvarur",
    "நாகப்பட்டினம்": "Nagapattinam", "திருவண்ணாமலை": "Tiruvannamalai", "சென்னை": "Chennai",
}
