from fastapi import FastAPI
<<<<<<< HEAD
from app.upload_and_parse_route import router as parse_router


app = FastAPI()
app.include_router(parse_router)

=======
from app.routes.parse import router as parse_router  # adjust this import path if needed

# ✅ DEFINE the FastAPI app first
app = FastAPI()

# ✅ THEN include your routers

app.include_router(parse_router)
from app.lender_match import router as lender_router
>>>>>>> 680a722 (Add /ping route and fix main.py router import)
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
