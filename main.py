import os
import io
import base64
import streamlit as st
from PIL import Image
from openai import OpenAI

st.set_page_config(page_title="시설물 점검 보고서 자동 생성", page_icon="🧱", layout="centered")
st.title("🧱 이미지 기반 시설물 점검 보고서 생성기 (MVP)")
st.caption("사진 1장 업로드 → 손상 유형 판정 + 위험도 평가 + 개선 권고안 자동 작성 (ChatGPT API)")

# -------------------------
# API Key
# -------------------------
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
if not api_key:
    st.error("OPENAI_API_KEY가 설정되어 있지 않습니다. Streamlit Secrets 또는 환경변수로 설정하세요.")
    st.stop()

client = OpenAI(api_key=api_key)

# -------------------------
# Prompt (기관용 표준 양식 강제)
# -------------------------
SYSTEM_PROMPT = """
너는 고속도로 운영기관의 ‘시설물 점검 보고서(기술검토 메모 포함)’ 작성 보조관임.
입력된 사진과 사용자가 제공한 사실 정보만으로 보고서를 작성함.

중요 규칙:
1) 사진만으로 확정할 수 없는 내용은 단정 금지. '추정'이 아닌 '가능성'으로 표현함.
2) 입력에 없는 정보는 만들지 말고 '미상' 또는 '현장 확인 필요'로 표기함.
3) 과장/공포 조장 금지. 안전을 위한 합리적 권고만 제시함.
4) 보고서는 가독성 있게 구조화하여 아래 형식을 반드시 지킴.

반드시 아래 형식으로 출력(제목 포함, 줄바꿈 유지):
[1. 점검 개요]
[2. 관찰 내용(사진 기반)]
[3. 손상/이상 유형 판정(가능성 포함)]
[4. 위험도 평가(낮음/중간/높음) + 근거]
[5. 즉시 조치 권고(필요 시)]
[6. 보수/정비 권고안(단계별)]
[7. 추가 점검/확인 항목(체크리스트)]
[8. 참고/주의(면책 문구 1~2문장)]
""".strip()

def to_data_url(uploaded_file, max_width=1280):
    """업로드 이미지를 적당히 리사이즈 후 data URL로 변환(전송 안정성↑)."""
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    if w > max_width:
        new_h = int(h * (max_width / w))
        img = img.resize((max_width, new_h))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}", img

# -------------------------
# UI
# -------------------------
st.subheader("📥 입력")

facility_type = st.selectbox(
    "시설물 종류",
    ["포장(노면)", "차선/노면표지", "가드레일/방호벽", "방음벽", "교량/구조물", "배수시설", "표지판/부대시설", "기타"]
)
location = st.text_input("위치(선택)", placeholder="예) 천안→논산 34km, OOIC 인근")
when = st.text_input("촬영/점검 일시(선택)", placeholder="예) 2026-02-18 10:20")
notes = st.text_area("현장 메모(선택)", height=90, placeholder="예) 야간에 반사도 저하 민원, 균열 확대 의심, 누수 흔적 등")

uploaded = st.file_uploader("사진 업로드 (jpg/png)", type=["jpg", "jpeg", "png"])

col1, col2 = st.columns([1, 1])
with col1:
    generate_btn = st.button("✨ 보고서 생성", type="primary", use_container_width=True)
with col2:
    clear_btn = st.button("🧹 초기화", use_container_width=True)

if clear_btn:
    st.session_state["result"] = ""
    st.rerun()

if "result" not in st.session_state:
    st.session_state["result"] = ""

# 미리보기
if uploaded:
    data_url, preview_img = to_data_url(uploaded)
    st.image(preview_img, caption="업로드한 점검 사진(미리보기)", use_container_width=True)

# -------------------------
# Generate
# -------------------------
if generate_btn:
    if not uploaded:
        st.warning("사진을 업로드해주세요.")
    else:
        try:
            data_url, _ = to_data_url(uploaded)

            user_prompt = f"""
[사용자 제공 정보]
- 시설물 종류: {facility_type}
- 위치: {location.strip() if location.strip() else "미상"}
- 일시: {when.strip() if when.strip() else "미상"}
- 현장 메모: {notes.strip() if notes.strip() else "없음"}

요청:
업로드된 사진과 위 정보를 바탕으로, 지정된 형식의 ‘시설물 점검 보고서’를 작성해줘.
불확실한 부분은 '현장 확인 필요'로 표기해줘.
""".strip()

            with st.spinner("AI 분석 및 보고서 작성 중..."):
                resp = client.responses.create(
                    model="gpt-5.2",
                    input=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": user_prompt},
                                {"type": "input_image", "image_url": data_url},
                            ],
                        },
                    ],
                )

            st.session_state["result"] = resp.output_text.strip()

        except Exception as e:
            st.error("API 호출 중 오류가 발생했습니다. (키/네트워크/요금/모델/이미지 형식 등을 확인)")
            st.code(str(e))

# -------------------------
# Output
# -------------------------
if st.session_state["result"]:
    st.subheader("📄 생성된 점검 보고서")
    st.markdown(st.session_state["result"])
    st.download_button(
        "📥 텍스트로 저장",
        data=st.session_state["result"],
        file_name="facility_inspection_report.txt",
        mime="text/plain",
        use_container_width=True
    )
