from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.upload_and_parse_route import router as parse_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.upload_and_parse_route import router as parse_router
from app.lender_match import router as lender_router

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(parse_router)
app.include_router(lender_router)

@app.get("/")
def root():
    return {"message": "MCA backend is running"}
