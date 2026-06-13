from fastapi import FastAPI, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import uvicorn
from app.database import init_db
from app.routers import resources, remediation, dashboard

app = FastAPI(
    title="Cloud Cost Optimizer & Remediation Engine",
    description="FinOps tool to identify orphaned cloud resources and generate remediation commands",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(resources.router, prefix="/api/resources", tags=["Resources"])
app.include_router(remediation.router, prefix="/api/remediation", tags=["Remediation"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Cloud Cost Optimizer"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
