import streamlit as st

def render_isolated_dialog(load_sheet_func, save_sheet_func):
    teacher_id_target = st.session_state.get("logged_teacher_id", "")
    teacher_name_target = st.session_state.get("teacher_name", "교사")
    
    st.markdown(f"##### 👤 **{teacher_name_target}** 선생님의 보안 정보 수정")
    df_teachers = load_sheet_func("teacher_accounts", ["교사_ID", "비밀번호", "교사_성명", "담당_과목"])
    
    if not df_teachers.empty and teacher_id_target != "admin" and teacher_id_target != "":
        df_teachers['교사_ID'] = df_teachers['교사_ID'].astype(str).str.strip()
        target_idx = df_teachers[df_teachers['교사_ID'] == str(teacher_id_target).strip()].index
        
        if not target_idx.empty:
            idx = target_idx[0]
            curr_pw = str(df_teachers.loc[idx, "비밀번호"]).strip()
            curr_sub = str(df_teachers.loc[idx, "담당_과목"]).strip()
            
            new_pw = st.text_input("새 비밀번호 변경", value=curr_pw, type="password")
            new_sub = st.text_input("담당 과목 변경 (여러 과목은 콤마 분리)", value=curr_sub)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 🚨 메인 사이드바를 절대 침범하지 못하도록 격리된 순수 오리지널 빨간색 단추
            st.markdown("""
                <style>
                    div[data-testid="stFormSubmitButton"] > button, 
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
            
            if st.button("💾 변경사항 클라우드 시트에 즉시 반영", use_container_width=True):
                if new_pw and new_sub:
                    df_teachers.loc[idx, "비밀번호"] = new_pw.strip()
                    df_teachers.loc[idx, "담당_과목"] = new_sub.strip()
                    if save_sheet_func("teacher_accounts", df_teachers):
                        st.session_state["allowed_subjects"] = [s.strip() for s in new_sub.split(",") if s.strip()]
                        st.session_state["show_update_success_msg"] = True 
                        st.rerun()
                else: st.error("빈 칸을 남겨둘 수 없습니다.")
        else: st.error("계정 매핑 인덱스를 찾을 수 없습니다.")
    else:
        st.warning("최고관리자(admin) 계정은 마스터 권한 고정이므로 수정이 필요 없습니다.")