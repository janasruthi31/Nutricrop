from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .api import soil_router
from agronomy.api import agronomy_router
from phase5_nutrient.api import nutrient_router
from phase6_fertilizer.api import fertilizer_router, fertilizer_opt_router
from phase7_integration.api import integration_router
from phase7_integration.extra_api import extra_router

app = FastAPI(title="Sustainable Fertilizer Usage Optimizer Master API (Phases 1-8)")

# Enable CORS for web clients (e.g. Flutter Web on Chrome)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()
app.include_router(soil_router)
app.include_router(agronomy_router)
app.include_router(nutrient_router)
app.include_router(fertilizer_router)
app.include_router(fertilizer_opt_router)
app.include_router(integration_router)
app.include_router(extra_router)



@app.get("/health")
def health():
    return {"status": "ok"}

