from oracle_config import get_connection
import pandas as pd
import numpy as np
import networkx as nx
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def textrank_summarize_korean(text: str, num_sentences=3) -> list:
    sentences = re.split(r'(?<=[.!?])\s+|\n', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    if len(sentences) <= num_sentences:
        return sentences

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(sentences)
    sim_matrix = cosine_similarity(tfidf_matrix)
    graph = nx.from_numpy_array(sim_matrix)
    scores = nx.pagerank(graph)

    ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
    result = [s for _, s in ranked_sentences[:num_sentences]]
    return result

def summarize_reviews_for_product(product_id: int) -> dict:
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT rating, content FROM (
                SELECT rating, content FROM takku_review
                WHERE product_id = :pid
                ORDER BY created_at DESC
            ) WHERE ROWNUM <= 100
            """,
            conn,
            params={"pid": product_id}
        )
        df.columns = df.columns.str.lower()
        if df.empty:
            raise ValueError("No reviews found")

        df["sentiment"] = df["rating"].apply(lambda r: "positive" if r >= 4 else "negative")

        positive_reviews = [str(c) for c in df[df["sentiment"] == "positive"]["content"] if c]
        negative_reviews = [str(c) for c in df[df["sentiment"] == "negative"]["content"] if c]

        result = {}

        if positive_reviews:
            pos_text = " ".join(positive_reviews)
            result["positive"] = textrank_summarize_korean(pos_text)
        else:
            result["positive"] = ["긍정 리뷰가 없습니다."]

        if negative_reviews:
            neg_text = " ".join(negative_reviews)
            result["negative"] = textrank_summarize_korean(neg_text)
        else:
            result["negative"] = ["부정 리뷰가 없습니다."]

        return result
    finally:
        conn.close()
