import os
import streamlit as st
from openai import OpenAI
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="운영실적 보고 자동 생성 시스템", page_icon="📊")
st.title("📊 운영실적 보고 자동 생성 시스템 (MVP)")
st.caption("월간/정기 운영실적 보고서 및 이사회 요약 자동 생성")

# 🔐 API KEY
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
if not api_key:
    st.error("OPENAI_API_KEY가 설정되지 않았습니다.")
    st.stop()

client = OpenAI(api_key=api_key)

# -----------------------
# SYSTEM PROMPT
# -----------------------
SYSTEM_PROMPT = """
너는 고속도로 운영기관의 행정 보고서 작성 담당자임.
입력된 데이터를 기반으로 객관적이고 분석적인 행정 보고 문체로 작성함.

작성 원칙:
1. 과장 및 추정 금지.
2. 수치는 해석을 포함하되 임의 생성 금지.
3. 보고체 종결어미(~함, ~됨, ~중임) 사용.
4. 문서는 구조화하여 가독성 있게 작성.

반드시 아래 3가지를 모두 출력:

[1. 월간 운영실적 보고서 본문]
- 10~15문장
- 교통량, 통행수입, 사고현황, 특이사항 포함

[2. 이사회 보고용 요약]
- 5~7문장
- 핵심 지표 중심

[3. PPT 보고용 Bullet]
- 5개 이내 핵심 bullet
"""

# -----------------------
# 입력 UI
# -----------------------
st.subheader("📥 데이터 입력")

period = st.text_input("보고 기간", placeholder="예: 2026년 2월")
traffic = st.text_input("총 교통량", placeholder="예: 1,250,000대")
revenue = st.text_input("총 통행수입", placeholder="예: 32억 원")
accidents = st.text_input("사고 발생 건수", placeholder="예: 3건")
notes = st.text_area("특이사항", placeholder="예: 설 연휴 교통량 증가, 일부 구간 보수공사 시행 등")

# -----------------------
# 보고서 생성
# -----------------------
if st.button("✨ 보고서 생성하기"):

    if not period:
        st.warning("보고 기간은 입력해주세요.")
    else:
        with st.spinner("보고서 생성 중..."):
            try:
                user_prompt = f"""
[입력 데이터]
- 보고 기간: {period}
- 총 교통량: {traffic}
- 총 통행수입: {revenue}
- 사고 발생 건수: {accidents}
- 특이사항: {notes}
"""

                response = client.responses.create(
                    model="gpt-5.2",
                    input=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                )

                result = response.output_text.strip()

                st.subheader("📄 생성 결과")
                st.markdown(result)

                # 다운로드 버튼
                st.download_button(
                    "📥 텍스트로 저장",
                    data=result,
                    file_name=f"{period}_운영실적보고.txt",
                    mime="text/plain"
                )

            except Exception as e:
                st.error("API 오류 발생")
                st.code(str(e))
