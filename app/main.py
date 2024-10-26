from fastapi import FastAPI
from app.api.v1.endpoints import auth, stt, payments

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(stt.router, prefix="/api/v1/stt", tags=["stt"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
