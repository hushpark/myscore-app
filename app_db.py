# =========================================================================
# ➕ [에러 해결 완결판] 다이얼로그 팝업창 모듈 (격자 테두리 & 가운데 정렬 주입)
# =========================================================================
@st.dialog("🎉 실시간 성적표 대장")
def show_result_dialog(student_data, subject_name):
    # 💡 [피드백 완벽 반영] 교과명이 동적으로 치고 들어오는 명확한 헤드라인 가이드라인 설정
    st.markdown(f"<div><b>{student_data['이름']}</b> 학생의 <b>{subject_name}</b> 실시간 성적 내역입니다.</div><br>", unsafe_allow_html=True)
    
    sc1 = int(student_data.get('수행평가1', 0))
    sc2 = int(student_data.get('수행평가2', 0))
    sc3 = int(student_data.get('수행평가3', 0))
    total_score = sc1 + sc2 + sc3
    
    # ⬜ [테두리 격자 잠금] 해석 에러가 전혀 없는 순정 데이터프레임 빌드
    score_table_df = pd.DataFrame({
        "평가 항목": ["수행평가 1차", "수행평가 2차", "수행평가 3차", "📊 총점 합계"],
        "취득 점수": [f"{sc1} 점", f"{sc2} 점", f"{sc3} 점", f"{total_score} 점"]
    })
    
    # 💡 [피드백 완벽 반영] column_config를 활용해 평가 항목과 취득 점수 모두 칼같이 가운데 정렬!
    st.dataframe(
        score_table_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "평가 항목": st.column_config.TextColumn(alignment="center"),
            "취득 점수": st.column_config.TextColumn(alignment="center")
        }
    )
    st.markdown("<br>", unsafe_allow_html=True)
    
    if "has_counted" not in st.session_state:
        new_count = int(student_data.get("성적조회 횟수", 0)) + 1
        supabase.table(student_table).update({
            "성적조회 횟수": new_count, 
            "최종 확인일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).eq("subject_key", student_data["subject_key"]).eq("school_email", student_data["school_email"]).execute()
        st.session_state["has_counted"] = True
    
    # 💡 닫기 버튼은 하얀 상자 바로 밑에 모바일 너비에 맞춰 깔끔하게 배치
    if st.button("닫기", type="secondary", use_container_width=True):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.rerun()
