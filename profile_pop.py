import streamlit as st

def render_isolated_dialog(load_sheet_func, save_sheet_func):
    # 🚨 세션 변수에만 의존하지 않고, 현재 로그인된 정보를 한 번 더 안전하게 정제
    teacher_id_target = st.session_state.get("logged_teacher_id", "").strip()
    teacher_name_target = st.session_state.get("teacher_name", "교사").strip()
    
    # 만약 세션이 순간적으로 비어있거나 admin으로 오인된 경우를 대비한 철벽 방어선
    if teacher_id_target == "admin" and teacher_name_target != "최고관리자":
        # 사이드바 성명을 기준으로 ID 역추적 복구
        df_teachers = load_sheet_func("teacher_accounts", ["교사_ID", "교사_성명"])
        if not df_teachers.empty:
            match = df_teachers[df_teachers['교사_성명'].astype(str).str.strip() == teacher_name_target]
            if not match.empty:
                teacher_id_target = str(match.iloc[0]['교사_ID']).strip()

    st.markdown(f"##### 👤 **{teacher_name_target}** 선생님의 보안 정보 수정")
    
    # 최고관리자 진짜 계정 판정
    if teacher_id_target == "admin" or teacher_name_target == "최고관리자":
        st.warning("최고관리자(admin) 계정은 마스터 권한 고정이므로 시트 수정이 필요 없습니다.")
        return

    # 일반 교사 계정 로직 실시간 가동
    df_teachers = load_sheet_func("teacher_accounts", ["교사_ID", "비밀번호", "교사_성명", "담당_과목"])
    if not df_teachers.empty and teacher_id_target != "":
        df_teachers['교사_ID'] = df_teachers['교사_ID'].astype(str).str.strip()
        target_idx = df_teachers[df_teachers['교사_ID'] == teacher_id_target].index
        
        if target_idx.empty and teacher_name_target != "":
            # ID로 못 찾으면 성명으로 인덱스 재탐색 (2중 안심 메커니즘)
            target_idx = df_teachers[df_teachers['교사_성명'].astype(str).str.strip() == teacher_name_target].index

        if not target_idx.empty:
            idx = target_idx[0]
            curr_pw = str(df_teachers.loc[idx, "비밀번호"]).strip()
            curr_sub = str(df_teachers.loc[idx, "담당_과목"]).strip()
            
            new_pw = st.text_input("새 비밀번호 변경", value=curr_pw, type="password", key="pop_pw_input")
            new_sub = st.text_input("담당 과목 변경 (여러 과목은 콤마 분리)", value=curr_sub, key="pop_sub_input")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("""
                <style>
                    div.stButton > button {
                        background-color: #ef4444 !important;
                        color: #ffffff !important;
                        font-weight: 800 !important;
                        border: none !important;
                        border-radius: 6px !important;
                        padding: 12px 0 !important;
                        font-size: 15px !important;
                        width: 100% !important;
                        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2) !important;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            if st.button("💾 변경사항 클라우드 시트에 즉시 반영", key="isolated_popup_submit_concrete_btn"):
                if new_pw and new_sub:
                    df_teachers.loc[idx, "비밀번호"] = new_pw.strip()
                    df_teachers.loc[idx, "담당_과목"] = new_sub.strip()
                    if save_sheet_func("teacher_accounts", df_teachers):
                        st.session_state["allowed_subjects"] = [s.strip() for s in new_sub.split(",") if s.strip()]
                        st.session_state["show_update_success_msg"] = True 
                        st.rerun()
                else: st.error("빈 칸을 남겨둘 수 없습니다.")
        else:
            st.error("계정 매핑 인덱스를 찾을 수 없습니다. 로그아웃 후 다시 시도해 주세요.")