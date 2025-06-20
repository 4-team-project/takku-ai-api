# recommender.py
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack, csr_matrix

def generate_recommendations(user_df, funding_df, tag_df):
    if user_df.empty:
        # 콜드 스타트 처리
        funding_df["end_date"] = pd.to_datetime(funding_df["end_date"])
        funding_df["days_left"] = (funding_df["end_date"] - pd.Timestamp.today()).dt.days.clip(lower=0)
        funding_df["urgency_score"] = 1 / (1 + funding_df["days_left"])
        funding_df["score"] = funding_df["avg_rating"] * 0.7 + funding_df["urgency_score"] * 0.3

        # 직렬화 가능한 형태로 변환
        top_funding = funding_df.sort_values("score", ascending=False).head(10).copy()
        top_funding["end_date"] = top_funding["end_date"].dt.strftime("%Y-%m-%d")
        top_funding["score"] = top_funding["score"].astype(float)
        top_funding["urgency_score"] = top_funding["urgency_score"].astype(float)
        top_funding["days_left"] = top_funding["days_left"].astype(int)
        top_funding["avg_rating"] = top_funding["avg_rating"].astype(float)
        top_funding["review_cnt"] = top_funding["review_cnt"].astype(int)

        return top_funding.to_dict(orient="records")

    # 태그 벡터
    user_tag_counts = user_df.groupby("tag_id")["qty"].sum()
    tag_vector_columns = sorted(set(user_tag_counts.index).union(tag_df["tag_id"].unique()))
    user_tag_vector = np.array([user_tag_counts.get(tag_id, 0) for tag_id in tag_vector_columns]).reshape(1, -1)

    # 텍스트 벡터
    user_df["text"] = user_df["funding_name"].fillna("") + " " + user_df["funding_desc"].fillna("")
    tfidf = TfidfVectorizer(max_features=500)
    tfidf.fit(user_df["text"].drop_duplicates())
    user_text_vector = tfidf.transform(user_df["text"].drop_duplicates()).mean(axis=0)

    funding_df["text"] = funding_df["funding_name"].fillna("") + " " + funding_df["funding_desc"].fillna("")
    funding_text_matrix = tfidf.transform(funding_df["text"])

    # 태그 매트릭스
    pivot = tag_df.groupby(["funding_id", "tag_id"]).size().unstack(fill_value=0)
    for col in tag_vector_columns:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot = pivot[tag_vector_columns]
    pivot = pivot.reindex(funding_df["funding_id"]).fillna(0)
    funding_tag_matrix = csr_matrix(pivot.values)
    user_tag_matrix = csr_matrix(user_tag_vector)

    # 유사도 계산
    funding_full_matrix = hstack([funding_tag_matrix, funding_text_matrix])
    user_full_vector = hstack([user_tag_matrix, user_text_vector])
    scores = cosine_similarity(funding_full_matrix, user_full_vector).flatten()

    funding_df["score"] = scores

    # 직렬화 변환
    top_funding = funding_df.sort_values("score", ascending=False).head(10).copy()
    if "end_date" in top_funding.columns:
        top_funding["end_date"] = pd.to_datetime(top_funding["end_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    top_funding["score"] = top_funding["score"].astype(float)
    if "avg_rating" in top_funding.columns:
        top_funding["avg_rating"] = top_funding["avg_rating"].astype(float)
    if "review_cnt" in top_funding.columns:
        top_funding["review_cnt"] = top_funding["review_cnt"].astype(int)

    return top_funding.to_dict(orient="records")
