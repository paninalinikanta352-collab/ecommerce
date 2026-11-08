from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import admin, auth, cart, orders, products

app = FastAPI(title="Shop API", version="0.1.0")

origins = list({settings.FRONTEND_ORIGIN, "http://localhost:3000"})
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"ok": True}
