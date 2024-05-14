from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from api.api import api_router
from asyncio import get_event_loop
from config import Config
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from logging import basicConfig
from integrations.citrineos.citrineos import CitrineOSIntegration
from uvicorn import run
import stripe

from db.init_db import init_db

basicConfig(format=Config.LOG_FORMAT, level=Config.LOG_LEVEL)

''' Create the Fast API web app and define cors. API router used to attach root path from Config. '''
app = FastAPI(title=Config.OPENAPI_TITLE,)
router = APIRouter()

origins = ["*",]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

''' On startup of the web app also start the event consumer and set stripe api key '''
stripe.api_key = Config.STRIPE_API_KEY
ocpp_integration = CitrineOSIntegration()
app.ocpp_integration = ocpp_integration
@app.on_event("startup")
async def startup_event():
    loop = get_event_loop()
    loop.create_task(coro=ocpp_integration.receive_events())


''' Add the API router to the web app '''
app.include_router(api_router, prefix=Config.WEBSERVER_PATH,)


''' Add a health check route '''
@app.get("/health_check")
async def health_check():
    return {"status": "healthy"}


''' Add the frontend web app '''
templates = Jinja2Templates(directory="frontend/build")
frontend_routes = ["/", "/checkout/{evse_id}", "/charging/{evse_id}/{checkout_id}"]
async def serve_frontend(request: Request,):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "CLIENT_API_URL": Config.CLIENT_API_URL,}
    )
for route in frontend_routes:
    app.get(route, response_class=HTMLResponse)(serve_frontend)
app.mount("/", StaticFiles(directory="frontend/build",), name="frontend",)



# Check if DB is reachable
# db = get_db()
# db.execute(text("select (1)"))
init_db()

if __name__ == "__main__":
    try:
        run(app, host=Config.WEBSERVER_HOST, port=Config.WEBSERVER_PORT)
    except Exception as e:
        # logger.error(e)
        raise e
