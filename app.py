from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from oracle_config import run_queries
from recommender import generate_recommendations
import traceback

app = FastAPI()

@app.get("/")
def home():
    return {"message": "✅ 서버 정상 동작 중"}

@app.get("/recommend/{user_id}")
def recommend(user_id: int):
    try:
        user_df, funding_df, tag_df, image_df = run_queries(user_id)
        result = generate_recommendations(user_df, funding_df, tag_df, image_df)
        return JSONResponse(content=result, media_type="application/json")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
