from flask import Flask, Response
import json
from oracle_config import run_queries
from recommender import generate_recommendations

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ 서버 정상 동작 중"

@app.route("/recommend/<int:user_id>")
def recommend(user_id):
    try:
        user_df, funding_df, tag_df = run_queries(user_id)
        result = generate_recommendations(user_df, funding_df, tag_df)
        return Response(
            json.dumps(result, ensure_ascii=False),  # 🔥 핵심: 한글 유지
            content_type="application/json; charset=utf-8"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(json.dumps({"error": str(e)}, ensure_ascii=False), status=500)


if __name__ == "__main__":
    app.run(debug=True)
