import json
import os
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

DSL_PATH = Path(__file__).parent.parent / "dsl" / "income_tax_deduction.json"
CHROMA_PATH = Path(__file__).parent.parent / "rag" / "chroma_store"

def load_dsl() -> dict:
    with open(DSL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_chroma_client():
    return chromadb.PersistentClient(path=str(CHROMA_PATH))

def get_collection():
    client = get_chroma_client()
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(
        name="tax_rules",
        embedding_function=ef
    )

def index_dsl_rules():
    dsl = load_dsl()
    collection = get_collection()
    
    for rule in dsl["rules"]:
        document = f"""
        규칙ID: {rule['id']}
        규칙명: {rule['name']}
        설명: {rule['description']}
        내용: {json.dumps(rule, ensure_ascii=False)}
        """
        collection.upsert(
            ids=[rule["id"]],
            documents=[document],
            metadatas=[{"rule_id": rule["id"], "name": rule["name"]}]
        )
    return f"{len(dsl['rules'])}개 규칙 인덱싱 완료"

def query_tax_rules(query: str, n_results: int = 3) -> list:
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results["documents"][0] if results["documents"] else []

def get_all_rules() -> dict:
    return load_dsl()

def save_approved_case(case: dict) -> str:
    collection = get_collection()
    case_id = f"CASE_{case['id']}"
    document = f"""
    승인케이스ID: {case_id}
    질의: {case['query']}
    판단: {case['result']}
    세무사승인: True
    """
    collection.upsert(
        ids=[case_id],
        documents=[document],
        metadatas=[{"type": "approved_case", "case_id": case_id}]
    )
    return f"케이스 {case_id} RAG 저장 완료"

def save_rejected_case(case: dict) -> str:
    collection = get_collection()
    case_id = f"REJECTED_{case['id']}"
    document = f"""
    반려케이스ID: {case_id}
    질의: {case['query']}
    초안: {case['draft']}
    반려사유: {case['feedback']}
    세무사승인: False
    """
    collection.upsert(
        ids=[case_id],
        documents=[document],
        metadatas=[{"type": "rejected_case", "case_id": case_id}]
    )
    return f"반려 케이스 {case_id} RAG 저장 완료"
