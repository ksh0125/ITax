from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class InputQuery(BaseModel):
    keywords: str

@app.post("/recommend-laws")
def recommend_laws(query: InputQuery):
    return {"message": f"'{query.keywords}'에 대한 세법 추천입니다 (테스트용 응답)"}
