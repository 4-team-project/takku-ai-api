import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack, csr_matrix


def format_funding_response(df):
    allowed_keys = {
        "fundingId", "productId", "storeId", "fundingType", "fundingName", "fundingDesc",
        "startDate", "endDate", "salePrice", "targetQty", "maxQty", "currentQty", "perQty",
        "status", "createdAt", "tagList", "images", "thumbnailImageUrl", "storeName",
        "price", "avgRating", "reviewCnt", "score"
    }

    rename_map = {
        "funding_id": "fundingId",
        "product_id": "productId",
        "store_id": "storeId",
        "funding_type": "fundingType",
        "funding_name": "fundingName",
        "funding_desc": "fundingDesc",
        "start_date": "startDate",
        "end_date": "endDate",
        "sale_price": "salePrice",
        "target_qty": "targetQty",
        "max_qty": "maxQty",
        "current_qty": "currentQty",
        "per_qty": "perQty",
        "status": "status",
        "created_at": "createdAt",
        "tagList": "tagList",
        "images": "images",
        "thumbnail_image_url": "thumbnailImageUrl",
        "store_name": "storeName",
        "price": "price",
        "avg_rating": "avgRating",
        "review_cnt": "reviewCnt",
        "score": "score"
    }

    for col in ["start_date", "end_date", "created_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

    df = df.rename(columns=rename_map)

    return [
        {k: v for k, v in record.items() if k in allowed_keys}
        for record in df.to_dict(orient="records")
    ]


def generate_recommendations(user_df, funding_df, tag_df, image_df):

    if funding_df.empty:
        print("[INFO] funding_df is empty. No recommendations available.")
        return []

    def enrich(df):
        tag_map = tag_df.groupby("funding_id")["tag_name"].apply(list).to_dict() if not tag_df.empty else {}
        image_map = image_df.groupby("funding_id")["image_url"].apply(
            lambda urls: [{"imageUrl": url} for url in urls]
        ).to_dict() if not image_df.empty else {}

        df["tagList"] = df["funding_id"].apply(lambda fid: tag_map.get(fid, []))
        df["images"] = df["funding_id"].apply(lambda fid: image_map.get(fid, []))
        return df

    def prepare_urgency_score(df):
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
        df["days_left"] = df["end_date"].apply(
            lambda x: max((x - pd.Timestamp.today()).days, 0) if pd.notnull(x) else 0
        )
        df["urgency_score"] = 1 / (1 + df["days_left"])
        return df

    funding_df = funding_df.fillna({"avg_rating": 0, "urgency_score": 0})

    if user_df.empty:
        funding_df = prepare_urgency_score(funding_df)
        funding_df["score"] = funding_df["avg_rating"].fillna(0) * 0.7 + funding_df["urgency_score"].fillna(0) * 0.3
        top = funding_df.sort_values("score", ascending=False).head(10).copy()
        top = enrich(top)
        return format_funding_response(top)

    user_tag_counts = user_df.groupby("tag_name")["qty"].sum()
    all_tags = sorted(set(tag_df["tag_name"].unique()))
    user_tag_vector = np.array([user_tag_counts.get(tag, 0) for tag in all_tags]).reshape(1, -1)

    user_df["text"] = user_df["funding_name"].fillna("") + " " + user_df["funding_desc"].fillna("")
    funding_df["text"] = funding_df["funding_name"].fillna("") + " " + funding_df["funding_desc"].fillna("")

    tfidf = TfidfVectorizer(max_features=500)
    try:
        combined_text = pd.concat([user_df["text"], funding_df["text"]], ignore_index=True)
        tfidf.fit(combined_text)
    except ValueError:
        print("[ERROR] TF-IDF fitting failed. Returning empty result.")
        return []

    user_text_matrix = tfidf.transform(user_df["text"])
    user_text_vector = np.asarray(user_text_matrix.mean(axis=0)).reshape(1, -1)
    funding_text_matrix = tfidf.transform(funding_df["text"])

    pivot = tag_df.pivot_table(index="funding_id", columns="tag_name", aggfunc="size", fill_value=0) if not tag_df.empty else pd.DataFrame()

    for tag in all_tags:
        if tag not in pivot.columns:
            pivot[tag] = 0
    pivot = pivot[all_tags]

    try:
        pivot = pivot.reindex(funding_df["funding_id"]).fillna(0)
    except Exception as e:
        print(f"[ERROR] Pivot reindex failed: {e}")
        return []

    funding_tag_matrix = csr_matrix(pivot.values)
    user_tag_matrix = csr_matrix(user_tag_vector)

    try:
        funding_full_matrix = hstack([funding_tag_matrix, funding_text_matrix])
        user_full_vector = hstack([user_tag_matrix, user_text_vector])
    except ValueError as e:
        print(f"[ERROR] Sparse matrix stacking failed: {e}")
        return []

    try:
        scores = cosine_similarity(funding_full_matrix, user_full_vector).flatten()
    except ValueError as e:
        print(f"[ERROR] Cosine similarity failed: {e}")
        return []

    funding_df["score"] = scores
    top = funding_df.sort_values("score", ascending=False).head(10).copy()
    top = enrich(top)
    return format_funding_response(top)
