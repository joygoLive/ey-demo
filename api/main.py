import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

sys.path.append(str(__import__('pathlib').Path(__file__).parent.parent))
from mcp_server.tax_mcp import (
    index_dsl_rules,
    query_tax_rules,
    get_all_rules,
    save_approved_case
)

load_dotenv()

app = FastAPI(title="EY Tax DSL Demo API")

class QueryRequest(BaseModel):
    query: str
    n_results: int = 3

class ApproveRequest(BaseModel):
    id: str
    query: str
    result: str

@app.on_event("startup")
async def startup():
    index_dsl_rules()

@app.get("/rules")
async def get_rules():
    return get_all_rules()

@app.post("/query")
async def query_rules(request: QueryRequest):
    results = query_tax_rules(request.query, request.n_results)
    if not results:
        raise HTTPException(status_code=404, detail="관련 규칙을 찾을 수 없습니다")
    return {"results": results}

@app.post("/approve")
async def approve_case(request: ApproveRequest):
    result = save_approved_case({
        "id": request.id,
        "query": request.query,
        "result": request.result
    })
    return {"message": result}

@app.get("/health")
async def health():
    return {"status": "ok"}
