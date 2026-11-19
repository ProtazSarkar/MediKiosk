"""
ChromaDB-powered RAG Engine for Clinical Symptom Matching and Medical Guidance.
Operates 100% locally with zero external ChromaDB API keys required.
"""

import os
import json
import logging
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from utils.medical_kb import CLINICAL_DISEASE_PROFILES

logger = logging.getLogger(__name__)

class LocalClinicalEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Self-contained, fast, zero-network embedding function using TF-IDF.
    Ensures ChromaDB functions reliably without downloading remote models
    or requiring external embedding API keys.
    """
    def __init__(self, corpus=None):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=256,
            token_pattern=r'(?u)\b[a-zA-Z0-9_\-\.]{2,}\b'
        )
        self.is_fitted = False
        if corpus:
            self.fit(corpus)

    def fit(self, corpus):
        self.vectorizer.fit(corpus)
        self.is_fitted = True

    def __call__(self, input: Documents) -> Embeddings:
        if not self.is_fitted:
            self.fit(input)
        matrix = self.vectorizer.transform(input).toarray()
        return matrix.tolist()

class MedicalRAGEngine:
    def __init__(self, persist_dir="storage/chroma_db"):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)

        # Prepare corpus for local embedding function
        corpus = []
        for d in CLINICAL_DISEASE_PROFILES:
            text = f"{d['name']} {d['department']} {' '.join(d['hallmark_symptoms'])} {' '.join(d['differentiating_questions'])}"
            corpus.append(text)

        self.embedding_fn = LocalClinicalEmbeddingFunction(corpus=corpus)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="medical_knowledge",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        self._ensure_knowledge_base_indexed()

    def _ensure_knowledge_base_indexed(self):
        """Index or update clinical disease profiles into ChromaDB."""
        current_count = self.collection.count()
        if current_count < len(CLINICAL_DISEASE_PROFILES):
            logger.info("Indexing clinical disease profiles into ChromaDB...")
            ids = []
            documents = []
            metadatas = []

            for d in CLINICAL_DISEASE_PROFILES:
                doc_text = (
                    f"Condition: {d['name']}\n"
                    f"Department: {d['department']}\n"
                    f"ICD-11: {d['icd11_code']} | SNOMED: {d['snomed_code']}\n"
                    f"Hallmark Symptoms: {', '.join(d['hallmark_symptoms'])}\n"
                    f"Key Differentiating Questions:\n" +
                    "\n".join([f"- {q}" for q in d['differentiating_questions']]) + "\n"
                    f"Pertinent Negatives: {', '.join(d['pertinent_negatives'])}\n"
                    f"Red Flags: {', '.join(d['red_flags'])}\n"
                    f"Typical Duration: {d['typical_duration']}"
                )
                ids.append(d["id"])
                documents.append(doc_text)
                metadatas.append({
                    "disease_id": d["id"],
                    "name": d["name"],
                    "department": d["department"],
                    "icd11": d["icd11_code"],
                    "snomed": d["snomed_code"],
                    "raw_json": json.dumps(d)
                })

            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Indexed {len(ids)} clinical profiles into ChromaDB.")

    def search_relevant_diseases(self, query_text: str, n_results: int = 4):
        """
        Query ChromaDB for conditions semantically matching the patient symptoms.
        Returns list of matched disease profiles with metadata and distance scores.
        """
        if not query_text or not query_text.strip():
            return []

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results, len(CLINICAL_DISEASE_PROFILES))
            )

            matched_diseases = []
            if results and results.get("ids") and len(results["ids"][0]) > 0:
                for idx, doc_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][idx]
                    doc_content = results["documents"][0][idx]
                    distance = results["distances"][0][idx] if "distances" in results and results["distances"] else 0.0
                    raw_data = json.loads(metadata.get("raw_json", "{}"))

                    matched_diseases.append({
                        "id": doc_id,
                        "name": metadata.get("name"),
                        "department": metadata.get("department"),
                        "icd11": metadata.get("icd11"),
                        "snomed": metadata.get("snomed"),
                        "document": doc_content,
                        "distance": float(distance),
                        "details": raw_data
                    })

            return matched_diseases
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []

# Singleton instance
_rag_engine_instance = None

def get_rag_engine():
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = MedicalRAGEngine()
    return _rag_engine_instance
