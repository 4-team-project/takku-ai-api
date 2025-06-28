from oracle_config import get_connection
import pandas as pd
from konlpy.tag import Okt
import numpy as np
import networkx as nx
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

okt = Okt()

def remove_duplicate_sentences(sentences, threshold=0.9):
    """
    유사한 문장을 제거하는 함수 (cosine similarity 기준)
    """
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

def textrank_summarize_korean(text: str, num_sentences=3) -> list[str]:
    # 문장 분리 및 전처리
    sentences = re.split(r'(?<=[.!?])\s+|\n', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

    if len(sentences) <= num_sentences:
        return sentences

    def sentence_to_words(sent):
        return okt.nouns(sent)

    docs = [sentence_to_words(s) for s in sentences]
    vocab = list(set(w for doc in docs for w in doc if len(w) > 1))
    vocab_idx = {w: i for i, w in enumerate(vocab)}

    tf = np.zeros((len(sentences), len(vocab)))
    for i, doc in enumerate(docs):
        for word in doc:
            if word in vocab_idx:
                tf[i][vocab_idx[word]] += 1

    sim = np.dot(tf, tf.T)
    norm = np.linalg.norm(tf, axis=1, keepdims=True)
    sim = sim / (np.dot(norm, norm.T) + 1e-10)

    graph = nx.from_numpy_array(sim)
    scores = nx.pagerank(graph)

    ranked = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
    summary_candidates = [s for _, s in ranked]

    filtered = remove_duplicate_sentences(summary_candidates)

    return filtered[:num_sentences]

def summarize_reviews_for_product(product_id: int) -> list[str]:
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT content FROM (
                SELECT content
                FROM takku_review
                WHERE product_id = :pid
                ORDER BY created_at DESC
            )
            WHERE ROWNUM <= 100
            """,
            conn,
            params={"pid": product_id}
        )
        df.columns = df.columns.str.lower()

        if "content" not in df.columns or df.empty:
            return []

        reviews = [str(c) for c in df["content"] if c]
        if not reviews:
            return []

        text = " ".join(reviews)
        return textrank_summarize_korean(text, num_sentences=3)

    finally:
        conn.close()
