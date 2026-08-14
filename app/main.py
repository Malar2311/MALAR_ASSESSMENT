from fastapi import FastAPI

app = FastAPI(title="Multi-Source Data Harmonization Pipeline")


@app.get("/")
def home():
    return {
        "message": "Data Harmonization Pipeline is running"
    }