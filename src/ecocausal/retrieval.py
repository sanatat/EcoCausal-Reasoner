"""Conservative hybrid retrieval: abstain on ungrounded queries instead of forced top-k.

Cosine similarities are not calibrated probabilities. Thresholds below are cautious
engineering gates, not externally validated measures of scientific relevance.
"""
from __future__ import annotations
import math
import re
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
from .schema import Evidence


def tokenize(x: str) -> list[str]:
    return [t for t in re.findall(r'[a-z0-9]+', x.lower()) if len(t) >= 2 and t not in ENGLISH_STOP_WORDS]


GENERIC_QUESTION_WORDS = frozenset({'effect', 'effects', 'impact', 'impacts', 'change', 'changes',
    'reducing', 'reduction', 'reduce', 'influence', 'influences', 'causes', 'cause',
    'study', 'studies', 'show', 'shows', 'evidence', 'scientific', 'question', 'research',
    'relationship', 'related', 'support', 'supports', 'whether', 'conclusion',
    'laboratory', 'blank', 'blanks', 'sample', 'samples', 'monitoring', 'record', 'records',
    'report', 'reports', 'data', 'dataset', 'paper', 'papers', 'result', 'results'})


def topic_sequence(text: str) -> list[str]:
    """Preserve concept order for guarding against off-topic partial matches."""
    out = []
    for term in tokenize(text):
        if term in GENERIC_QUESTION_WORDS:
            continue
        term = term[:-1] if term.endswith('s') and not term.endswith('us') and len(term) > 4 else term
        if term in {'algal', 'algae', 'biomass'}:
            term = 'chlorophyll'  # Explicitly scoped ecology alias, not general semantics.
        if term not in out:
            out.append(term)
    return out


def topic_terms(text: str) -> set[str]:
    return set(topic_sequence(text))


def shared_query_terms(query: str, text: str) -> int:
    """Cheap auditable anchor check; a shared word alone does NOT prove entailment."""
    return len(topic_terms(query) & topic_terms(text))


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> dict[int, float]:
    scores = {}
    for ids in rankings:
        for rank, i in enumerate(ids, 1):
            scores[i] = scores.get(i, 0.0) + 1.0 / (k + rank)
    return scores


class EvidenceRetriever:
    def __init__(self, evidence: list[Evidence], *, semantic=False, rerank=False,
                 embedding_model='sentence-transformers/all-MiniLM-L6-v2',
                 cross_encoder='cross-encoder/ms-marco-MiniLM-L6-v2',
                 semantic_min_similarity: float = .44, semantic_only_min_similarity: float = .68):
        if not evidence:
            raise ValueError('Need at least one evidence item')
        if len({e.source_id for e in evidence}) != len(evidence):
            raise ValueError('Duplicate source_id: provenance would be ambiguous')
        if not 0 <= semantic_min_similarity <= semantic_only_min_similarity <= 1:
            raise ValueError('Invalid semantic similarity thresholds')
        self.docs = evidence
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
        self.X = self.vectorizer.fit_transform([e.text for e in evidence])
        self.tf = [Counter(tokenize(e.text)) for e in evidence]
        self.doc_len = np.array([sum(c.values()) for c in self.tf])
        self.df = Counter(t for c in self.tf for t in c)
        self.semantic = bool(semantic)
        self.rerank = bool(rerank)
        self.semantic_min_similarity = semantic_min_similarity
        self.semantic_only_min_similarity = semantic_only_min_similarity
        self.embedding_model_id = None
        self.cross_encoder_id = None
        if self.semantic:
            try:
                from sentence_transformers import SentenceTransformer
                import faiss
            except ImportError as exc:
                raise RuntimeError('Semantic mode requires pip install -e .[semantic]') from exc
            self.embedder = SentenceTransformer(embedding_model, device='cpu')
            self.embedding_model_id = embedding_model
            vectors = np.asarray(self.embedder.encode([d.text for d in evidence], normalize_embeddings=True), dtype='float32')
            if vectors.ndim != 2 or not np.isfinite(vectors).all():
                raise ValueError('Invalid embedding matrix')
            self.index = faiss.IndexFlatIP(vectors.shape[1])
            self.index.add(vectors)
        if self.rerank:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as exc:
                raise RuntimeError('Reranker requires pip install -e .[semantic]') from exc
            self.reranker = CrossEncoder(cross_encoder, device='cpu')
            self.cross_encoder_id = cross_encoder

    def bm25_scores(self, query: str) -> np.ndarray:
        n = len(self.docs)
        scores = np.zeros(n)
        mean_len = float(np.mean(self.doc_len)) or 1.0
        for term in set(tokenize(query)):
            df = self.df.get(term, 0)
            if not df:
                continue
            idf = math.log(1 + (n - df + .5) / (df + .5))
            for i, ct in enumerate(self.tf):
                freq = ct.get(term, 0)
                if freq:
                    scores[i] += idf * (freq * 2.2) / (freq + 1.2 * (.25 + .75 * self.doc_len[i] / mean_len))
        return scores

    def query(self, query: str, top_k=5, *, rerank_pool=12) -> list[tuple[Evidence, float]]:
        if not query.strip() or not tokenize(query):
            raise ValueError('query needs non-stopword content')
        if top_k < 1 or rerank_pool < 1:
            raise ValueError('top_k and rerank_pool must be positive')
        ordered_topics = topic_sequence(query)
        # If both lead concepts are absent from the entire corpus, do not answer
        # a different question by using incidental downstream terms.
        if not self.semantic and len(ordered_topics) >= 3:
            lead = set(ordered_topics[:2])
            if not any(lead & topic_terms(d.text) for d in self.docs):
                return []
        q = self.vectorizer.transform([query])
        tfidf = cosine_similarity(q, self.X).reshape(-1)
        bm = self.bm25_scores(query)
        n = len(self.docs)
        lexical = (tfidf > 0) | (bm > 0)
        anchors = np.array([shared_query_terms(query, e.text) for e in self.docs])
        # Multi-concept questions require at least two content anchors in a text.
        # Avoid claiming a paper is relevant because it shares generic words such as "lake".
        min_anchors = 2 if len(topic_terms(query)) >= 3 else 1
        topic_count = len(topic_terms(query))
        coverage = anchors / max(1, topic_count)
        adequate_lexical = lexical & (anchors >= min_anchors) & (coverage >= .50)
        semantic_scores = np.zeros(n)
        allowed = adequate_lexical.copy()
        if self.semantic:
            vec = np.asarray(self.embedder.encode([query], normalize_embeddings=True), dtype='float32')
            if vec.ndim != 2 or vec.shape[0] != 1 or not np.isfinite(vec).all():
                raise ValueError('Invalid query embedding')
            sim, idx = self.index.search(vec, n)
            semantic_scores[idx[0]] = sim[0]
            # Query-specific abstention: semantic-only requires unusually strong similarity.
            # The thresholds are deliberately conservative and must be calibrated on real qrels.
            allowed |= ((semantic_scores >= self.semantic_min_similarity) & (anchors >= 1) & (coverage >= .50))
            allowed |= semantic_scores >= self.semantic_only_min_similarity
        if not allowed.any():
            return []
        rankings = [sorted(np.flatnonzero(allowed & (tfidf > 0)), key=lambda i: (-tfidf[i], int(i))),
                    sorted(np.flatnonzero(allowed & (bm > 0)), key=lambda i: (-bm[i], int(i)))]
        if self.semantic:
            rankings.append(sorted(np.flatnonzero(allowed), key=lambda i: (-semantic_scores[i], int(i))))
        fused = reciprocal_rank_fusion(rankings)
        pool = min(n, max(top_k, rerank_pool))
        selected = sorted(fused, key=lambda i: (-fused[i], i))[:pool]
        if self.rerank and selected:
            scores = np.asarray(self.reranker.predict([(query, self.docs[i].text) for i in selected]), dtype=float).reshape(-1)
            if len(scores) != len(selected) or not np.isfinite(scores).all():
                raise ValueError('Reranker returned invalid scores')
            scored = sorted(zip(selected, map(float, scores)), key=lambda x: (-x[1], x[0]))
        else:
            scored = [(i, float(fused[i])) for i in selected]
        return [(self.docs[i], float(v)) for i, v in scored[:top_k]]
