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
        user_df, funding_df, tag_df, image_df = run_queries(user_id)
        result = generate_recommendations(user_df, funding_df, tag_df, image_df)
        return Response(
            json.dumps(result, ensure_ascii=False),
            content_type="application/json; charset=utf-8"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(json.dumps({"error": str(e)}, ensure_ascii=False), status=500)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
