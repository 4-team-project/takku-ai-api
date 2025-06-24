import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack, csr_matrix

# 사용자 행동 기반 추천 리스트 생성 함수
def generate_recommendations(user_df, funding_df, tag_df, image_df):

    # 펀딩 데이터에 태그 및 이미지 정보 추가하는 함수
    def enrich(df):
        tag_map = tag_df.groupby("funding_id")["tag_name"].apply(list).to_dict()
        image_map = image_df.groupby("funding_id")["image_url"].apply(
            lambda urls: [{"imageUrl": url} for url in urls]
        ).to_dict()

        # 펀딩별 태그 리스트, 이미지 리스트 추가
        df["tagList"] = df["funding_id"].apply(lambda fid: tag_map.get(fid, []))
        df["images"] = df["funding_id"].apply(lambda fid: image_map.get(fid, []))
        return df

    # 펀딩 마감 임박 정도(긴급도) 점수를 계산하는 함수
    def prepare_urgency_score(df):
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
        df["days_left"] = df["end_date"].apply(
            lambda x: max((x - pd.Timestamp.today()).days, 0) if pd.notnull(x) else 0
        )
        # 긴급도 점수: 마감일이 가까울수록 높은 점수
        df["urgency_score"] = 1 / (1 + df["days_left"])
        return df

    # 날짜 컬럼을 문자열로 변환 (API 응답 등 가독성 목적)
    def convert_dates_to_str(df, date_columns):
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
        return df

    # 사용자의 기록이 없는 경우 (cold start)
    if user_df.empty:
        funding_df = prepare_urgency_score(funding_df)
        # 평점과 긴급도 기반 가중치 스코어
        funding_df["score"] = funding_df["avg_rating"] * 0.7 + funding_df["urgency_score"] * 0.3

        # 상위 10개 추출
        top = funding_df.sort_values("score", ascending=False).head(10).copy()
        top = convert_dates_to_str(top, ["start_date", "end_date", "created_at"])
        top = enrich(top)
        return top.to_dict(orient="records")

    # ============ 유저 기반 추천 프로세스 ============ #

    # 유저가 많이 주문한 태그별 수량 계산
    user_tag_counts = user_df.groupby("tag_id")["qty"].sum()

    # 전체 태그 리스트 정의 (유저 태그 + 전체 태그)
    all_tags = sorted(
        set(map(str, user_tag_counts.index)).union(map(str, tag_df["tag_name"].unique()))
    )

    # 유저 태그 벡터 (tag_id를 기준으로 수량 구성)
    user_tag_vector = np.array([user_tag_counts.get(tag, 0) for tag in all_tags]).reshape(1, -1)

    # 텍스트 데이터 전처리: 펀딩 이름 + 설명 결합
    user_df["text"] = user_df["funding_name"].fillna("") + " " + user_df["funding_desc"].fillna("")
    funding_df["text"] = funding_df["funding_name"].fillna("") + " " + funding_df["funding_desc"].fillna("")

    # TF-IDF 벡터라이저 학습 (펀딩 설명 기반)
    tfidf = TfidfVectorizer(max_features=500)
    tfidf.fit(pd.concat([user_df["text"], funding_df["text"]], ignore_index=True))

    # 유저 및 펀딩의 TF-IDF 벡터 생성
    user_text_matrix = tfidf.transform(user_df["text"])
    user_text_vector = np.asarray(user_text_matrix.mean(axis=0)).reshape(1, -1)
    funding_text_matrix = tfidf.transform(funding_df["text"])

    # 펀딩의 태그 정보를 pivot하여 벡터화
    pivot = tag_df.pivot_table(index="funding_id", columns="tag_name", aggfunc="size", fill_value=0)
    
    # 유저 기준으로 사용된 태그가 펀딩 태그에도 반영되도록 컬럼 보정
    for tag in all_tags:
        if tag not in pivot.columns:
            pivot[tag] = 0
    pivot = pivot[all_tags]
    pivot = pivot.reindex(funding_df["funding_id"]).fillna(0)

    # 희소 행렬로 변환
    funding_tag_matrix = csr_matrix(pivot.values)
    user_tag_matrix = csr_matrix(user_tag_vector)

    # 텍스트 벡터 + 태그 벡터 결합
    funding_full_matrix = hstack([funding_tag_matrix, funding_text_matrix])
    user_full_vector = hstack([user_tag_matrix, user_text_vector])

    # 코사인 유사도로 유저와 펀딩 간 유사도 계산
    scores = cosine_similarity(funding_full_matrix, user_full_vector).flatten()
    funding_df["score"] = scores

    # 스코어 상위 10개 추천
    top = funding_df.sort_values("score", ascending=False).head(10).copy()
    top = convert_dates_to_str(top, ["start_date", "end_date", "created_at"])
    top = enrich(top)
    return top.to_dict(orient="records")
