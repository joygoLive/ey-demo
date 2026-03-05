# 프로젝트 개요
EY 세무본부 AI Native 세무 플랫폼 데모
개인소득세 공제 규칙 DSL 기반 RAG + LangGraph Agent + Human-in-the-loop 예제

# 기술 스택
- LLM: Ollama (llama3.2) + Claude API
- RAG: ChromaDB
- Agent: LangGraph
- MCP: Anthropic MCP Python SDK
- Backend: FastAPI
- Language: Python 3.11+

# 코딩 규칙
- PEP 8 준수
- 함수/변수: snake_case
- 클래스: PascalCase
- 상수: UPPER_SNAKE_CASE
- 파일명: snake_case

# 디렉토리 구조
- dsl/: 세무 규칙 DSL JSON 파일
- rag/: ChromaDB 벡터 저장소
- mcp_server/: MCP 서버 및 Tool 정의
- agent/: LangGraph Agent 워크플로우
- api/: FastAPI 백엔드

# 환경변수 (.env)
- ANTHROPIC_API_KEY: Claude API 키
- OLLAMA_BASE_URL: http://localhost:11434

# DSL 규칙
- 모든 세무 규칙은 JSON DSL로 정의
- dsl/ 디렉토리에서 관리
- 변경 시 Git 커밋 필수
