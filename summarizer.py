from oracle_config import get_connection
import pandas as pd
import numpy as np
import networkx as nx
import re
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# ✅ SBERT 로드
model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS")

# ✅ 중복 제거
def remove_duplicate_sentences(sentences, threshold=0.75):
    if len(sentences) <= 1:
        return sentences
    embeddings = model.encode(sentences)
    sim_matrix = cosine_similarity(embeddings)
    keep = []
    seen = set()
    for i in range(len(sentences)):
        if i in seen:
            continue
        keep.append(sentences[i])
        for j in range(i + 1, len(sentences)):
            if sim_matrix[i][j] > threshold:
                seen.add(j)
    return keep

# ✅ MMR 다양성 고려 요약
def mmr(doc_embedding, word_embeddings, words, top_n=3, diversity=0.7):
    word_doc_similarity = cosine_similarity(word_embeddings, doc_embedding)
    word_similarity = cosine_similarity(word_embeddings)
    selected = [np.argmax(word_doc_similarity)]
    candidates = [i for i in range(len(words)) if i != selected[0]]
    for _ in range(top_n - 1):
        sim_to_doc = word_doc_similarity[candidates]
        sim_to_selected = np.max(word_similarity[candidates][:, selected], axis=1)
        mmr_score = (1 - diversity) * sim_to_doc.squeeze() - diversity * sim_to_selected
        selected_idx = candidates[np.argmax(mmr_score)]
        selected.append(selected_idx)
        candidates.remove(selected_idx)
    return [words[i] for i in selected]

# ✅ 핵심 요약 함수
def textrank_summarize_korean(text: str, num_sentences=3) -> list:
    sentences = re.split(r'(?<=[.!?])\s+|\n', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    if len(sentences) <= num_sentences:
        return sentences
    embeddings = model.encode(sentences)
    sim_matrix = cosine_similarity(embeddings)
    graph = nx.from_numpy_array(sim_matrix)
    scores = nx.pagerank(graph)
    ranked = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
    top_candidates = [s for _, s in ranked[:10]]
    top_embeddings = model.encode(top_candidates)
    doc_embedding = np.mean(top_embeddings, axis=0, keepdims=True)
    summary = mmr(doc_embedding, top_embeddings, top_candidates, top_n=num_sentences, diversity=0.7)
    return remove_duplicate_sentences(summary)

# ✅ 리뷰 요약 (점수 기반 감성 분류)
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
            result["positive"] = textrank_summarize_korean(pos_text, num_sentences=3)
        else:
            result["positive"] = ["긍정 리뷰가 없습니다."]

        if negative_reviews:
            neg_text = " ".join(negative_reviews)
            result["negative"] = textrank_summarize_korean(neg_text, num_sentences=3)
        else:
            result["negative"] = ["부정 리뷰가 없습니다."]

        return result

    finally:
        conn.close()
