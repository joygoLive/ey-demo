import os
import json
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
import sys
sys.path.append(str(__import__('pathlib').Path(__file__).parent.parent))
from mcp_server.tax_mcp import query_tax_rules, save_approved_case, save_rejected_case

load_dotenv()

llm = ChatOllama(
    model="gemma3:12b",
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
)

class TaxAgentState(TypedDict):
    query: str
    rag_results: list
    draft: str
    status: str
    feedback: str
    case_id: str

def retrieve_rules(state: TaxAgentState) -> TaxAgentState:
    query = state["query"]
    results = query_tax_rules(query)
    return {**state, "rag_results": results}

def generate_draft(state: TaxAgentState) -> TaxAgentState:
    query = state["query"]
    rag_results = state["rag_results"]
    
    context = "\n".join(rag_results)
    prompt = f"""
당신은 한국 세무 전문가입니다. 아래 규칙만 참고하여 질의에 답변하세요.

[규칙]
{context}

[질의]
{query}

[답변 규칙]
1. 질의와 직접 관련된 규칙만 사용하세요
2. 관련 없는 규칙은 무시하세요
3. 계산 시 질의에 명시된 금액 기준으로만 계산하세요
4. 계산 근거를 단계별로 명확히 작성하세요
5. 최종 공제 한도/금액을 명확히 제시하세요
6. 불확실한 정보는 추측하지 말고 "확인 필요"로 표시하세요
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "draft": response.content, "status": "대기중"}

def wait_for_approval(state: TaxAgentState) -> TaxAgentState:
    print("\n" + "="*50)
    print("【세무사 검토 요청】")
    print("="*50)
    print(f"\n[질의]\n{state['query']}")
    print(f"\n[초안]\n{state['draft']}")
    print("\n" + "="*50)
    
    while True:
        action = input("\n승인(a) / 반려(r) / 수정 후 재검토(m): ").strip().lower()
        if action == "a":
            return {**state, "status": "승인"}
        elif action == "r":
            feedback = input("반려 사유: ")
            return {**state, "status": "반려", "feedback": feedback}
        elif action == "m":
            feedback = input("수정 요청 내용: ")
            return {**state, "status": "수정요청", "feedback": feedback}
        else:
            print("a, r, m 중 하나를 입력해주세요.")

def handle_approved(state: TaxAgentState) -> TaxAgentState:
    import time
    case = {
        "id": str(int(time.time())),
        "query": state["query"],
        "result": state["draft"]
    }
    result = save_approved_case(case)
    print(f"\n✅ 승인 완료: {result}")
    return {**state, "case_id": case["id"]}

def handle_rejected(state: TaxAgentState) -> TaxAgentState:
    import time
    case = {
        "id": str(int(time.time())),
        "query": state["query"],
        "draft": state["draft"],
        "feedback": state["feedback"]
    }
    result = save_rejected_case(case)
    print(f"\n❌ 반려 처리: {state['feedback']}")
    print(f"📝 반려 이력 저장: {result}")
    return state

def handle_revision(state: TaxAgentState) -> TaxAgentState:
    feedback = state["feedback"]
    prompt = f"""
    다음 수정 요청을 반영하여 공제 계산 초안을 수정해주세요.
    
    [기존 초안]
    {state['draft']}
    
    [수정 요청]
    {feedback}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "draft": response.content, "status": "대기중"}

def route_approval(state: TaxAgentState) -> str:
    if state["status"] == "승인":
        return "approved"
    elif state["status"] == "반려":
        return "rejected"
    elif state["status"] == "수정요청":
        return "revision"
    return "approved"

def build_agent():
    graph = StateGraph(TaxAgentState)
    
    graph.add_node("retrieve_rules", retrieve_rules)
    graph.add_node("generate_draft", generate_draft)
    graph.add_node("wait_for_approval", wait_for_approval)
    graph.add_node("handle_approved", handle_approved)
    graph.add_node("handle_rejected", handle_rejected)
    graph.add_node("handle_revision", handle_revision)
    
    graph.set_entry_point("retrieve_rules")
    graph.add_edge("retrieve_rules", "generate_draft")
    graph.add_edge("generate_draft", "wait_for_approval")
    graph.add_conditional_edges(
        "wait_for_approval",
        route_approval,
        {
            "approved": "handle_approved",
            "rejected": "handle_rejected",
            "revision": "handle_revision"
        }
    )
    graph.add_edge("handle_approved", END)
    graph.add_edge("handle_rejected", END)
    graph.add_edge("handle_revision", "wait_for_approval")
    
    return graph.compile()

if __name__ == "__main__":
    agent = build_agent()
    
    print("개인소득세 공제 계산 Agent 시작")
    print("="*50)
    
    from mcp_server.tax_mcp import index_dsl_rules
    print(index_dsl_rules())
    
    query = input("\n공제 관련 질의를 입력하세요: ")
    
    result = agent.invoke({
        "query": query,
        "rag_results": [],
        "draft": "",
        "status": "",
        "feedback": "",
        "case_id": ""
    })
    
    print("\n처리 완료")
