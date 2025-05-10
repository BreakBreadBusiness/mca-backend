from fastapi import FastAPI
from app.upload_and_parse_route import router as parse_router


app = FastAPI()
app.include_router(parse_router)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["https://your-frontend.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lender_router)

@app.get("/")
def root():
    return {"message": "MCA backend is running"}
