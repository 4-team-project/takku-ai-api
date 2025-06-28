from oracle_config import get_connection
import pandas as pd
import numpy as np
import networkx as nx
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def remove_duplicate_sentences(sentences, threshold=0.9):
    if len(sentences) <= 1:
        return sentences

    tfidf = TfidfVectorizer().fit_transform(sentences)
    sim_matrix = cosine_similarity(tfidf)

    keep = []
    seen = set()

    for i, s in enumerate(sentences):
        if i in seen:
            continue
        keep.append(s)
        for j in range(i + 1, len(sentences)):
            if sim_matrix[i][j] > threshold:
                seen.add(j)
    return keep

def textrank_summarize_korean(text: str, num_sentences=3) -> list:
    sentences = re.split(r'(?<=[.!?])\s+|\n', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

    if len(sentences) <= num_sentences:
        return sentences

    tfidf = TfidfVectorizer().fit_transform(sentences)
    sim_matrix = cosine_similarity(tfidf)

    graph = nx.from_numpy_array(sim_matrix)
    scores = nx.pagerank(graph)

    ranked = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
    summary_candidates = [s for _, s in ranked]

    filtered = remove_duplicate_sentences(summary_candidates)
    return filtered[:num_sentences]

def summarize_reviews_for_product(product_id: int) -> list:
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT content FROM (
                SELECT content FROM takku_review
                WHERE product_id = :pid
                ORDER BY created_at DESC
            ) WHERE ROWNUM <= 100
            """,
            conn,
            params={"pid": product_id}
        )
        df.columns = df.columns.str.lower()
        reviews = [str(c) for c in df["content"] if c]

        if not reviews:
            raise ValueError("No reviews found")

        text = " ".join(reviews)
        return textrank_summarize_korean(text, num_sentences=3)

    finally:
        conn.close()
