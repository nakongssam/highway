st.title("고속도로 사고 보고서 자동 생성기")

accident_type = st.selectbox("사고 유형", ["추돌", "낙하물", "차량 고장"])
location = st.text_input("위치")
time = st.text_input("발생 시간")
details = st.text_area("특이사항")

if st.button("보고서 생성"):
    # GPT API 호출
    st.write(response)
