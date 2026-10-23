import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import prompts, schemas
from .config import settings
from .llm import LLMError, ask_json

app = FastAPI(title="Multimodal Construction Intelligence Platform", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}


async def _read_image(file: UploadFile | None, required: bool = False):
    if file is None or not file.filename:
        if required:
            raise HTTPException(400, "An image file is required for this analysis.")
        return None
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(415, "Only JPEG, PNG, WEBP or GIF images are supported.")
    data = await file.read()
    if len(data) > settings.max_image_mb * 1024 * 1024:
        raise HTTPException(413, f"Image exceeds {settings.max_image_mb} MB limit.")
    return (file.content_type, data)


def _run(system, prompt, model_cls, image=None):
    try:
        return ask_json(system, prompt, model_cls, [image] if image else None)
    except LLMError as e:
        raise HTTPException(502, str(e))


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_configured": bool(settings.anthropic_api_key)}


@app.post("/api/safety", response_model=schemas.SafetyReport)
async def safety(notes: str = Form(""), file: UploadFile | None = File(None)):
    img = await _read_image(file)
    if not img and not notes.strip():
        raise HTTPException(400, "Provide a site image or a description.")
    return _run(prompts.SAFETY, f"Site notes: {notes or 'none'}", schemas.SafetyReport, img)


@app.post("/api/cracks", response_model=schemas.CrackReport)
async def cracks(location: str = Form(""), notes: str = Form(""), file: UploadFile = File(...)):
    img = await _read_image(file, required=True)
    prompt = f"Surface/location: {location or 'unknown'}\nNotes: {notes or 'none'}"
    return _run(prompts.CRACK, prompt, schemas.CrackReport, img)


@app.post("/api/valuation", response_model=schemas.ValuationReport)
async def valuation(
    location: str = Form(...),
    property_type: str = Form("residential"),
    area_sqft: float = Form(...),
    age_years: int = Form(0),
    condition: str = Form("good"),
    currency: str = Form("INR"),
    notes: str = Form(""),
    file: UploadFile | None = File(None),
):
    if area_sqft <= 0:
        raise HTTPException(400, "area_sqft must be positive.")
    img = await _read_image(file)
    prompt = (
        f"Location: {location}\nType: {property_type}\nArea: {area_sqft} sq ft\n"
        f"Age: {age_years} years\nCondition: {condition}\nCurrency: {currency}\n"
        f"Notes: {notes or 'none'}"
    )
    return _run(prompts.VALUATION, prompt, schemas.ValuationReport, img)


@app.post("/api/planning", response_model=schemas.PlanReport)
async def planning(
    project_type: str = Form(...),
    location: str = Form(""),
    area_sqft: float = Form(...),
    floors: int = Form(1),
    budget: str = Form(""),
    notes: str = Form(""),
):
    prompt = (
        f"Project: {project_type}\nLocation: {location or 'unspecified'}\n"
        f"Built-up area: {area_sqft} sq ft\nFloors: {floors}\n"
        f"Budget: {budget or 'unspecified'}\nNotes: {notes or 'none'}"
    )
    return _run(prompts.PLANNING, prompt, schemas.PlanReport)


@app.post("/api/assistant", response_model=schemas.AssistantReport)
async def assistant(message: str = Form(...), file: UploadFile | None = File(None)):
    img = await _read_image(file)
    return _run(prompts.ASSISTANT, message, schemas.AssistantReport, img)


@app.post("/api/weather", response_model=schemas.WeatherAdvisory)
async def weather(city: str = Form(...), activity: str = Form("")):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            geo = (
                await c.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": city, "count": 1},
                )
            ).json()
            if not geo.get("results"):
                raise HTTPException(404, f"City '{city}' not found.")
            g = geo["results"][0]
            wx = (
                await c.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": g["latitude"],
                        "longitude": g["longitude"],
                        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                        "daily": "precipitation_sum,temperature_2m_max,wind_speed_10m_max",
                        "forecast_days": 3,
                    },
                )
            ).json()
    except httpx.HTTPError:
        raise HTTPException(502, "Weather service unavailable.")
    prompt = f"City: {g['name']}, {g.get('country', '')}\nPlanned activity: {activity or 'general'}\nWeather JSON: {wx}"
    return _run(prompts.WEATHER, prompt, schemas.WeatherAdvisory)


@app.post("/api/knowledge", response_model=schemas.KnowledgeReport)
async def knowledge(question: str = Form(...)):
    return _run(prompts.KNOWLEDGE, question, schemas.KnowledgeReport)
