import os
import streamlit as st
from openai import OpenAI

# -------------------------
# Page
# -------------------------
st.set_page_config(page_title="회사 워크숍 계획 자동 생성", page_icon="🧩", layout="centered")
st.title("🧩 회사 워크숍 계획 자동 생성기")
st.caption("입력한 조건을 바탕으로 워크숍 기획안을 구조화된 문서로 자동 생성합니다. (ChatGPT API)")

# -------------------------
# API Key (Streamlit Secrets 또는 환경변수)
# Streamlit Cloud: App → Settings → Secrets 에 OPENAI_API_KEY 저장
# -------------------------
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
if not api_key:
    st.error("OPENAI_API_KEY가 설정되어 있지 않습니다. Streamlit Secrets 또는 환경변수로 설정하세요.")
    st.stop()

client = OpenAI(api_key=api_key)

# -------------------------
# Prompts
# -------------------------
SYSTEM_PROMPT = """
너는 회사 인사/조직문화 담당자 수준의 ‘워크숍 기획안’ 작성 전문가임.
목표: 사용자가 입력한 조건을 바탕으로 실행 가능한 워크숍 운영 계획을 구조화하여 작성함.

원칙:
1) 과장/허위 금지. 입력에 없는 정보는 임의로 확정하지 말고 ‘제안’ 형태로 표현함.
2) 현장에서 바로 사용할 수 있도록 구체적으로 작성하되, 불필요한 장황함은 지양함.
3) 출력은 반드시 아래 형식/섹션을 유지하고, 각 섹션은 줄바꿈으로 구분함.
4) 문체는 간결한 실무 문서체(보고/기획 문서 톤)로 작성함.

출력 형식(제목 없이 본문만):
[1. 워크숍 개요]
[2. 목표 및 기대효과]
[3. 대상/인원/운영 방식]
[4. 전체 일정표(시간대별)]
[5. 세션 상세(각 세션: 목적-진행-준비물-산출물)]
[6. 준비물/공간/운영 인력(R&R)]
[7. 사전 준비 체크리스트]
[8. 리스크 및 대응 방안]
[9. 사후 평가 및 후속 실행(액션 아이템)]
마지막 줄: 추가 질문(최대 3개)
""".strip()

def build_user_prompt(
    title, purpose, audience, headcount, duration, date_place, budget,
    constraints, tone, include_ai
) -> str:
    ai_line = "포함(워크숍 내 AI 활용 활동 1개 이상 포함)" if include_ai else "미포함"
    return f"""
[입력 정보]
- 워크숍 제목(가칭): {title if title.strip() else "미상"}
- 목적/해결하고 싶은 문제: {purpose if purpose.strip() else "미상"}
- 대상(예: 전사/팀리더/신입 등): {audience if audience.strip() else "미상"}
- 예상 인원: {headcount if headcount.strip() else "미상"}
- 진행 시간: {duration}
- 일정/장소: {date_place if date_place.strip() else "미상"}
- 예산(대략): {budget if budget.strip() else "미상"}
- 제약/주의사항(예: 외부강사 불가, 게임 싫어함, 이동 제한 등): {constraints if constraints.strip() else "없음"}
- 문서 톤: {tone}
- AI 활동: {ai_line}

요청:
위 정보를 기반으로 워크숍 기획안을 작성해줘. 실무자가 그대로 실행할 수 있게 구체적으로 작성해줘.
""".strip()

# -------------------------
# UI
# -------------------------
col1, col2 = st.columns(2)
with col1:
    duration = st.selectbox("진행 시간", ["2시간", "3시간", "4시간", "반나절(4~5h)", "하루(6~8h)"])
with col2:
    tone = st.selectbox("문서 톤", ["실무형(간결)", "임원 보고형(격식)", "팀 운영형(친근하지만 정돈)"])

title = st.text_input("워크숍 제목(가칭)", placeholder="예) 2026 상반기 전략 워크숍 / 팀 리부트 워크숍")
purpose = st.text_area("목적/해결하고 싶은 문제", height=100, placeholder="예) 부서 간 협업 문제 개선, 목표 정렬, 신사업 아이디어 발굴 등")
audience = st.text_input("대상", placeholder="예) 팀 리더 12명 / 개발팀 전원 / 전사 등")
headcount = st.text_input("예상 인원", placeholder="예) 20명")
date_place = st.text_input("일정/장소", placeholder="예) 3/15(금) 13:00~17:00, 본사 3층 대회의실")
budget = st.text_input("예산(대략)", placeholder="예) 50만원 / 200만원 / 미정")
constraints = st.text_area("제약/주의사항", height=80, placeholder="예) 외부 강사 불가, 활동은 조용한 형태 선호, 노트북 지참 어려움 등")
include_ai = st.checkbox("워크숍 안에 AI 활용 활동(예: 아이디어 발산/정리)을 1개 이상 포함", value=True)

btn_col1, btn_col2 = st.columns([1, 1])
with btn_col1:
    generate_btn = st.button("✨ 워크숍 계획 생성", type="primary", use_container_width=True)
with btn_col2:
    clear_btn = st.button("🧹 초기화", use_container_width=True)

if clear_btn:
    st.session_state["result_text"] = ""
    st.rerun()

if "result_text" not in st.session_state:
    st.session_state["result_text"] = ""

# -------------------------
# Generate
# -------------------------
if generate_btn:
    if not purpose.strip():
        st.warning("‘목적/해결하고 싶은 문제’는 최소 1줄이라도 입력해 주세요.")
    else:
        try:
            with st.spinner("기획안 생성 중..."):
                user_prompt = build_user_prompt(
                    title=title,
                    purpose=purpose,
                    audience=audience,
                    headcount=headcount,
                    duration=duration,
                    date_place=date_place,
                    budget=budget,
                    constraints=constraints,
                    tone=tone,
                    include_ai=include_ai
                )

                resp = client.responses.create(
                    model="gpt-5.2",
                    input=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                st.session_state["result_text"] = resp.output_text.strip()

        except Exception as e:
            st.error("API 호출 중 오류가 발생했습니다. (키/네트워크/요금/모델명 등을 확인)")
            st.code(str(e))

# -------------------------
# Output
# -------------------------
if st.session_state["result_text"]:
    st.subheader("📄 생성된 워크숍 기획안")
    # 구조 가독성 위해 markdown 추천
    st.markdown(st.session_state["result_text"])
    st.download_button(
        "📥 텍스트로 저장",
        data=st.session_state["result_text"],
        file_name="workshop_plan.txt",
        mime="text/plain",
        use_container_width=True
    )
