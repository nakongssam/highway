import os
import streamlit as st
from openai import OpenAI

# -------------------------
# Page
# -------------------------
st.set_page_config(page_title="사고·상황 보고서 자동 생성", page_icon="🛣️", layout="centered")
st.title("🛣️ 사고·상황 보고서 자동 생성기")
st.caption("입력한 사실을 기반으로 고속도로 상황실 보고체 문장을 자동 생성합니다. (ChatGPT API)")

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
너는 ‘천안–논산 고속도로’ 운영기관 상황실의 공식 보고서 작성 담당자다.
보고서는 내부 결재 및 상급기관 보고에 활용되는 문서 수준으로 작성한다.

작성 기준:
1) 공식적이고 전문적인 공문체 사용.
2) 문장은 충분히 구체적으로 서술하되 과장이나 추정은 금지.
3) 입력에 없는 정보는 생성하지 말고 '미상' 또는 '확인 중'으로 표기.
4) 단문 나열이 아닌, 연결된 문단형 보고서로 작성.
5) 전체 분량은 8~12문장 내외로 작성.

보고서 구성:
① 발생 개요 (일시, 방향, 위치, 사고 유형을 종합 서술)
② 사고 경위 및 현장 상황 (차량 수, 피해 상황, 교통 영향 등)
③ 조치 사항 (출동, 통제, 유관기관 협조 등)
④ 향후 계획 및 요청 사항
⑤ 마지막 줄에 '추가 확인 항목:' 1~3개 제시

출력은 제목 없이 본문만 작성한다.
""".strip()

def build_user_prompt(incident_type, direction, location, time_text, damage, notes):
    return f"""
[입력 정보]
- 사고/상황 유형: {incident_type}
- 방향: {direction}
- 위치: {location if location.strip() else "미상"}
- 발생 시각: {time_text if time_text.strip() else "미상"}
- 피해 정도(인명/차량/시설 등): {damage if damage.strip() else "미상"}
- 특이사항: {notes if notes.strip() else "미상"}

요청: 위 정보를 바탕으로 ‘공식 보고서 문장’을 작성해줘.
출력 규칙: 제목/머리말 없이 결과만 출력.
""".strip()

# -------------------------
# UI Inputs
# -------------------------
col1, col2 = st.columns(2)
with col1:
    incident_type = st.selectbox(
        "사고/상황 유형",
        ["추돌", "낙하물", "차량 고장", "기상(강우/안개/결빙)", "정체/혼잡", "시설물 이상", "기타"]
    )
with col2:
    direction = st.selectbox("방향", ["천안 → 논산", "논산 → 천안", "양방향", "미상"])

location = st.text_input("위치", placeholder="예) 34km 지점 / OOIC 인근 / 톨게이트명")
time_text = st.text_input("발생 시각", placeholder="예) 2026-02-18 14:32 또는 14:32")
damage = st.text_input("피해 정도", placeholder="예) 인명피해 없음 / 경상 1명 / 차량 2대 파손 등")
notes = st.text_area("특이사항", height=120, placeholder="예) 2차로 부분 통제, 견인 요청, 119 출동 등")

btn_col1, btn_col2 = st.columns([1, 1])
with btn_col1:
    generate_btn = st.button("✨ 보고서 생성", type="primary", use_container_width=True)
with btn_col2:
    clear_btn = st.button("🧹 초기화", use_container_width=True)

if clear_btn:
    for k in ["result_text"]:
        if k in st.session_state:
            st.session_state[k] = ""
    st.rerun()

if "result_text" not in st.session_state:
    st.session_state["result_text"] = ""

# -------------------------
# Generate
# -------------------------
if generate_btn:
    # 최소 필수는 '유형'이라서 나머지는 미상 처리 가능하게 둠
    try:
        with st.spinner("보고서 생성 중..."):
            user_prompt = build_user_prompt(
                incident_type=incident_type,
                direction=direction,
                location=location,
                time_text=time_text,
                damage=damage,
                notes=notes
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
    st.subheader("📄 생성된 공식 보고서 문장")
    st.text_area("복사해서 사용하세요", st.session_state["result_text"], height=240)
    st.download_button(
        "📥 텍스트로 저장",
        data=st.session_state["result_text"],
        file_name="incident_report.txt",
        mime="text/plain",
        use_container_width=True
    )
