from fastapi import FastAPI

app = FastAPI(title="Interview Practice Partner - API")

@app.get("/health")
async def health():
    return {"status": "ok"}