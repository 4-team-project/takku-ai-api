import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack, csr_matrix

# ✅ 필요 없는 필드를 제거해서 Spring DTO에 맞게 변환
def format_funding_response(df):
    allowed_keys = {
        "funding_id", "product_id", "store_id", "funding_type", "funding_name", "funding_desc",
        "start_date", "end_date", "sale_price", "target_qty", "max_qty", "current_qty", "per_qty",
        "status", "created_at", "tagList", "images", "thumbnail_image_url", "store_name",
        "price", "avg_rating", "review_cnt", "score"
    }

    # 날짜 포맷 통일
    for col in ["start_date", "end_date", "created_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

    # 필요한 컬럼만 포함된 dict 리스트로 변환
    return [
        {k: v for k, v in record.items() if k in allowed_keys}
        for record in df.to_dict(orient="records")
    ]

# 사용자 행동 기반 추천 리스트 생성 함수
def generate_recommendations(user_df, funding_df, tag_df, image_df):

    # 펀딩 데이터에 태그 및 이미지 정보 추가
    def enrich(df):
        tag_map = tag_df.groupby("funding_id")["tag_name"].apply(list).to_dict()
        image_map = image_df.groupby("funding_id")["image_url"].apply(
            lambda urls: [{"imageUrl": url} for url in urls]
        ).to_dict()
        df["tagList"] = df["funding_id"].apply(lambda fid: tag_map.get(fid, []))
        df["images"] = df["funding_id"].apply(lambda fid: image_map.get(fid, []))
        return df

    # 긴급도 점수 계산
    def prepare_urgency_score(df):
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
        df["days_left"] = df["end_date"].apply(
            lambda x: max((x - pd.Timestamp.today()).days, 0) if pd.notnull(x) else 0
        )
        df["urgency_score"] = 1 / (1 + df["days_left"])
        return df

    # 콜드 스타트: 유저 기록 없음
    if user_df.empty:
        funding_df = prepare_urgency_score(funding_df)
        funding_df["score"] = funding_df["avg_rating"] * 0.7 + funding_df["urgency_score"] * 0.3

        top = funding_df.sort_values("score", ascending=False).head(10).copy()
        top = enrich(top)
        return format_funding_response(top)

    # ============ 유저 기반 추천 프로세스 ============ #

    user_tag_counts = user_df.groupby("tag_id")["qty"].sum()
    all_tags = sorted(
        set(map(str, user_tag_counts.index)).union(map(str, tag_df["tag_name"].unique()))
    )
    user_tag_vector = np.array([user_tag_counts.get(tag, 0) for tag in all_tags]).reshape(1, -1)

    user_df["text"] = user_df["funding_name"].fillna("") + " " + user_df["funding_desc"].fillna("")
    funding_df["text"] = funding_df["funding_name"].fillna("") + " " + funding_df["funding_desc"].fillna("")

    tfidf = TfidfVectorizer(max_features=500)
    tfidf.fit(pd.concat([user_df["text"], funding_df["text"]], ignore_index=True))

    user_text_matrix = tfidf.transform(user_df["text"])
    user_text_vector = np.asarray(user_text_matrix.mean(axis=0)).reshape(1, -1)
    funding_text_matrix = tfidf.transform(funding_df["text"])

    pivot = tag_df.pivot_table(index="funding_id", columns="tag_name", aggfunc="size", fill_value=0)
    for tag in all_tags:
        if tag not in pivot.columns:
            pivot[tag] = 0
    pivot = pivot[all_tags]
    pivot = pivot.reindex(funding_df["funding_id"]).fillna(0)

    funding_tag_matrix = csr_matrix(pivot.values)
    user_tag_matrix = csr_matrix(user_tag_vector)

    funding_full_matrix = hstack([funding_tag_matrix, funding_text_matrix])
    user_full_vector = hstack([user_tag_matrix, user_text_vector])

    scores = cosine_similarity(funding_full_matrix, user_full_vector).flatten()
    funding_df["score"] = scores

    top = funding_df.sort_values("score", ascending=False).head(10).copy()
    top = enrich(top)
    return format_funding_response(top)
