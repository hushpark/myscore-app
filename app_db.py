import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import io
import re
from supabase import create_client, Client

# 🚨 [최상단 규칙 엄수] 와이드 레이아웃 설정
st.set_page_config(page_title="수행평가 점수 확인 시스템 (Supabase)", layout="wide")

# =========================================================================
# 🎨 [디자인 가시성 패치] 콤팩트 50% 반토막 레이아웃 및 세로 정렬 가공 CSS
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        [data-testid="stAppViewContainer"] { margin-left: 0px !important; }
        [data-testid="stSidebar"], section[data-testid="stSidebar"] { min-width: 280px !important; max-width: 280px !important; background-color: #1e293b !important; box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; }
        [data-testid="stSidebar"] .stRadio label p, [data-testid="stSidebar"] .stRadio label span, [data-testid="stSidebar"] .stRadio label div, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[role="radiogroup"] * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; opacity: 1 !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 15px !important; font-weight: 700 !important; line-height: 2.0 !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover * { color: #60a5fa !important; -webkit-text-fill-color: #60a5fa !important; }
        .sidebar-title { font-size: 24px !important; font-weight: 800 !important; margin-bottom: 5px !important; display: block; }
        .user-info { color: #38bdf8 !important; -webkit-text-fill-color: #38bdf8 !important; font-size: 14px !important; font-weight: 600 !important; margin-bottom: 25px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 12px 0 !important; width: 100% !important; display: block !important; margin-bottom: 8px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] *, [data-testid="stSidebar"] button[kind="secondary"] p { color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; font-size: 15px !important; font-weight: 700 !important; }
        
        /* 일반 화면 primary 버튼 */
        div.stButton > button[kind="primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #2563eb !important; }
        
        /* 입력 폼 가시성 패치 */
        div[data-testid="InputInstructions"] { display: none !important; }
        div[data-testid="stSelectbox"] label p, div[data-testid="stTextInput"] label p { font-weight: 800 !important; color: #1e293b !important; font-size: 15px !important; }
        div[data-testid="stTextInput"] > div, div[data-testid="stSelectbox"] > div { background-color: #ffffff !important; border: 1px solid #94a3b8 !important; border-radius: 6px !important; }
        div[data-testid="stTextInput"] input { background-color: #ffffff !important; color: #0f172a !important; padding: 8px 12px !important; }
        
        /* 로그인 화면 서식 */
        div[data-testid="stForm"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; padding: 45px 40px 45px 40px !important; border-radius: 24px !important; box-shadow: 0 15px 40px rgba(0,0,0,0.06) !important; max-width: 440px !important; margin: 70px auto 0 auto !important; }
        div[data-testid="stForm"] h2 { font-size: 26px !important; text-align: center !important; font-weight: 800 !important; color: #0f172a !important; }
        h3 { color: #1e293b !important; font-weight: 700 !important; font-size: 20px !important; margin-top: 0px !important; margin-bottom: 12px !important; }
        
        /* 🔥 [핵심 요청 반영] 드롭다운 및 텍스트 박스 길이를 기존의 절반(50%)으로 축소 고정 */
        .compact-half-width div[data-testid="stSelectbox"], 
        .compact-half-width div[data-testid="stTextInput"] {
            max-width: 50% !important;
        }
        
        /* 버튼 글자 잘림 방지 */
        .stButton button {
            white-space: nowrap !important;
            word-break: keep-all !important;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 🔑 [Supabase 원격 데이터베이스 연결 체계]
# =========================================================================
SUPABASE_URL = "https://jwkvojfmhorndnnhscwl.supabase.co"
SUPABASE_KEY = "sb_publishable_6--SHGogHaHSEVO7g3rNjQ_FOHO-XlN"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

student_table = "st_info_2_2026_1"
teacher_table = "teacher_accounts"
config_table = "subject_configs"

def load_db_df(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

def get_subject_item_names(subject_key):
    cfg_df = load_db_df(config_table)
    if not cfg_df.empty and "subject_key" in cfg_df.columns:
        match = cfg_df[cfg_df["subject_key"] == subject_key]
        if not match.empty:
            row = match.iloc[0]
            count = int(row.get("item_count", 3))
            titles = [
                row.get("item1_name", "수행평가1"), 
                row.get("item2_name", "수행평가2"), 
                row.get("item3_name", "수행평가3"),
                row.get("item4_name", "수행평가4"),
                row.get("item5_name", "수행평가5")
            ]
            return count, titles
    return 3, ["수행평가1", "수행평가2", "수행평가3", "수행평가4", "수행평가5"]

# =========================================================================
# ➕ [다이얼로그 팝업창 모듈]
# =========================================================================
@st.dialog("➕ 담당 교사 개별 추가")
def show_add_teacher_dialog():
    st.markdown("새로 등록할 선생님의 권한 정보를 입력해 주세요.")
    with st.form("add_teacher_form", border=False):
        t_id = st.text_input("교사 전용 ID", placeholder="예: info_teacher")
        t_name = st.text_input("교사 성명", placeholder="예: 박디몬")
        t_pw = st.text_input("초기 임시 비밀번호", placeholder="예: 1234")
        t_subs = st.text_input("담당 과목 권한 지정 (쉼표 분리)", placeholder="예: 정보, 수학")
        submit_btn = st.form_submit_button("💾 이 교사 계정 활성화하기", use_container_width=True)
        if submit_btn:
            if not t_id or not t_name or not t_pw or not t_subs: st.error("❌ 모든 항목을 입력해야 합니다.")
            else:
                try:
                    supabase.table(teacher_table).upsert({"교사_ID": t_id.strip(), "교사_성명": t_name.strip(), "비밀번호": t_pw.strip(), "담당_과목": t_subs.strip()}).execute()
                    st.success("🎉 교사 계정이 활성화되었습니다!")
                    st.rerun()
                except: st.error("❌ 등록 실패")

@st.dialog("➕ 전학생 / 개별 학생 추가")
def show_add_student_dialog():
    st.markdown("새로 명단에 추가할 학생의 기본 정보를 입력해 주세요.")
    with st.form("add_student_form", border=False):
        c1, c2, c3 = st.columns(3)
        with c1: new_ban = st.number_input("반", min_value=1, max_value=15, step=1)
        with c2: new_num = st.number_input("번호", min_value=1, max_value=50, step=1)
        with c3: new_name = st.text_input("이름")
        c4, c5 = st.columns(2)
        with c4: new_email = st.text_input("학교 이메일")
        with c5: new_pw = st.text_input("초기 비밀번호")
        submit_btn = st.form_submit_button("💾 이 학생 명단에 추가하기", use_container_width=True)
        if submit_btn:
            if not new_name or not new_email or not new_pw: st.error("❌ 모든 항목을 빠짐없이 입력해 주세요.")
            else:
                try:
                    supabase.table(student_table).upsert({"반": int(new_ban), "번호": int(new_num), "이름": new_name.strip(), "학교 이메일": new_email.strip(), "비밀번호": int(new_pw), "수행평가1": 0, "수행평가2": 0, "수행평가3": 0, "성적조회 횟수": 0, "최종 확인일시": "-"}).execute()
                    st.success("🎉 학생 데이터가 주입되었습니다!")
                    st.rerun()
                except: st.error("❌ 학생 추가 실패")

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_data):
    st.markdown(f"<div><b>{student_data['이름']}</b> 학생의 실시간 성적 내역입니다.</div>", unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("📝 수행평가 1차", f"{int(student_data.get('수행평가1', 0))} 점")
    sc2.metric("📝 수행평가 2차", f"{int(student_data.get('수행평가2', 0))} 점")
    sc3.metric("📝 수행평가 3차", f"{int(student_data.get('수행평가3', 0))} 점")
    if "has_counted" not in st.session_state:
        new_count = int(student_data.get("성적조회 횟수", 0)) + 1
        supabase.table(student_table).upsert({"반": int(student_data["반"]), "번호": int(student_data["번호"]), "성적조회 횟수": new_count, "최종 확인일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).execute()
        st.session_state["has_counted"] = True
    if st.button("닫기", type="secondary", use_container_width=True):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.session_state.clear()
        st.rerun()

# ⚙️ [세션 제어 상태 초기화]
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "student_logged_in" not in st.session_state: st.session_state["student_logged_in"] = False
if "logged_student_id" not in st.session_state: st.session_state["logged_student_id"] = ""
if "logged_student_pw" not in st.session_state: st.session_state["logged_student_pw"] = ""
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = ""
if "logged_teacher_pw" not in st.session_state: st.session_state["logged_teacher_pw"] = ""
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = ""
if "allowed_subjects" not in st.session_state: st.session_state["allowed_subjects"] = []

df = load_db_df(student_table)

# =========================================================================
# 🔓 [1단계] 로그인 시스템
# =========================================================================
if not st.session_state["admin_logged_in"] and not st.session_state["student_logged_in"]:
    with st.container():
        with st.form("master_unified_form"):
            st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
            login_mode = st.radio("접속 모드", ["학생", "교사"], horizontal=True, label_visibility="collapsed")
            user_id_input = st.text_input("ID", placeholder="ID를 입력하세요", label_visibility="collapsed")
            user_pw_input = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed")
            
            b_col2 = st.columns([1.0, 1.8, 1.0])[1]
            submit_active = b_col2.form_submit_button("로그인", use_container_width=True)
            
            if submit_active:
                clean_id = str(user_id_input).strip()
                clean_pw = str(user_pw_input).strip()
                if login_mode == "학생":
                    if df.empty: st.error("❌ 등록된 성적 데이터셋이 존재하지 않습니다.")
                    else:
                        id_col = "학교 이메일" if "학교 이메일" in df.columns else "school_email"
                        id_match = df[df[id_col] == clean_id]
                        if id_match.empty: st.error("❌ 등록되지 않은 학생 정보입니다.")
                        else:
                            if str(id_match.iloc[0]["비밀번호"]) == clean_pw:
                                st.session_state["student_logged_in"] = True
                                st.session_state["logged_student_id"] = clean_id
                                st.session_state["logged_student_pw"] = clean_pw
                                st.rerun()
                            else: st.error("❌ 비밀번호 불일치")
                elif login_mode == "교사":
                    if clean_id == "admin" and clean_pw == "1234":
                        st.session_state["admin_logged_in"] = True
                        st.session_state["logged_teacher_id"] = "admin"
                        st.session_state["logged_teacher_pw"] = "1234"
                        st.session_state["teacher_name"] = "최고관리자"
                        st.session_state["allowed_subjects"] = ["마스터"]
                        st.rerun()
                    else:
                        df_tc = load_db_df(teacher_table)
                        if df_tc.empty: st.error("❌ 일반 교사 계정이 비어있습니다.")
                        else:
                            id_match = df_tc[df_tc['교사_ID'] == clean_id]
                            if not id_match.empty and str(id_match.iloc[0]['비밀번호']) == clean_pw:
                                row = id_match.iloc[0]
                                st.session_state["admin_logged_in"] = True
                                st.session_state["logged_teacher_id"] = clean_id
                                st.session_state["logged_teacher_pw"] = clean_pw
                                st.session_state["teacher_name"] = str(row['교사_성명']).strip()
                                st.session_state["allowed_subjects"] = [s.strip() for s in str(row['담당_과목']).split(",") if s.strip()]
                                st.rerun()
                            else: st.error("❌ 교사 로그인 실패")

# =========================================================================
# 🎓 [2단계-A] 학생 화면
# =========================================================================
elif st.session_state["student_logged_in"]:
    st.markdown(f"<h2>수행평가 점수 확인 시스템 (학생 모드)</h2>", unsafe_allow_html=True)
    if st.button("🚪 로그아웃"): st.session_state.clear(); st.rerun()
    if st.button("🚀 나의 수행평가 성적 실시간 검증", type="primary", use_container_width=True):
        id_col = "학교 이메일" if "학교 이메일" in df.columns else "school_email"
        res = df[(df[id_col] == st.session_state["logged_student_id"]) & (df['비밀번호'].astype(str) == st.session_state["logged_student_pw"])]
        if not res.empty: show_result_dialog(res.iloc[0].to_dict())

# =========================================================================
# 🔒 [2단계-B] 교사 화면
# =========================================================================
elif st.session_state["admin_logged_in"]:
    with st.sidebar:
        st.markdown('<span class="sidebar-title">📋 교사 메뉴</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="user-info">👤 {st.session_state["teacher_name"]} 선생님 접속 중</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        menus = ["▶ 학생 조회 현황 모니터링", "▶ 개인별 성적 입력", "▶ 학생 정보 관리", "▶ 평가 대상 과목 구성", "▶ 성적 일괄 업로드 (CSV / Excel)"]
        if st.session_state["logged_teacher_id"] == "admin": 
            menus.append("👑 교사 계정 관리 대장")
            
        menu_selection = st.radio("메뉴 선택", menus, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.sidebar.button("🚪 로그아웃", type="secondary", use_container_width=True): st.session_state.clear(); st.rerun()

    if not df.empty and "반" in df.columns and "번호" in df.columns: df = df.sort_values(by=["반", "번호"])

    # ---------------------------------------------------------------------
    # 그림1: 학생 조회 현황 모니터링 (원래 대형 화면 구성 유지)
    # ---------------------------------------------------------------------
    if menu_selection == "▶ 학생 조회 현황 모니터링":
        with st.container(border=True):
            st.markdown("<h3>🔍 조회 관측할 대상 교과 선택</h3>", unsafe_allow_html=True)
            f_group = st.selectbox("교과군 선택", ["수리·과학군", "인문·사회군", "예체능군"], key="mon_g")
            f_sub = st.selectbox("세부 과목", ["정보", "국어", "수학", "영어"], key="mon_s")
            f_grade = st.selectbox("학년 지정", ["2학년", "1학년", "3학년"], key="mon_gr")
            f_term = st.selectbox("학기 선택", ["2026학년도 1학기", "2026학년도 2학기"], key="mon_t")
            
            subject_key = f"{f_sub}_{f_grade}_{f_term}".replace(" ", "_")
            item_count, item_titles = get_subject_item_names(subject_key)

        with st.container(border=True):
            if df.empty: st.info("📢 현재 데이터베이스가 비어있습니다.")
            else:
                sel_c = st.selectbox("🎯 학급 선택", options=["전체 학급 보기"] + [f"{x}반" for x in sorted(df['반'].unique())])
                r_df = df.copy()
                if sel_c != "전체 학급 보기": r_df = r_df[r_df['반'].astype(int) == int(sel_c.replace("반",""))]
                
                display_cols = ["반", "번호", "이름", "학교 이메일"]
                rename_map = {}
                for idx in range(item_count):
                    db_col = f"수행평가{idx+1}"
                    view_title = item_titles[idx]
                    if db_col in r_df.columns:
                        display_cols.append(db_col)
                        rename_map[db_col] = view_title
                display_cols += ["성적조회 횟수", "최종 확인일시"]
                
                final_view_df = r_df[display_cols].rename(columns=rename_map)
                st.dataframe(final_view_df.fillna("-"), use_container_width=True, hide_index=True)

    # ---------------------------------------------------------------------
    # 그림2: 개인별 성적 입력 (원래 대형 화면 구성 유지)
    # ---------------------------------------------------------------------
    elif menu_selection == "▶ 개인별 성적 입력":
        with st.container(border=True):
            st.markdown("<h3>🔍 성적을 입력할 대상 교과 선택</h3>", unsafe_allow_html=True)
            f_group = st.selectbox("교과군 선택", ["수리·과학군", "인문·사회군", "예체능군"], key="edt_g")
            f_sub = st.selectbox("세부 과목", ["정보", "국어", "수학", "영어"], key="edt_s")
            f_grade = st.selectbox("학년 지정", ["2학년", "1학년", "3학년"], key="edt_gr")
            f_term = st.selectbox("학기 선택", ["2026학년도 1학기", "2026학년도 2학기"], key="edt_t")
            
            subject_key = f"{f_sub}_{f_grade}_{f_term}".replace(" ", "_")
            item_count, item_titles = get_subject_item_names(subject_key)

        with st.container(border=True):
            if df.empty: st.info("등록된 학생 데이터가 없습니다.")
            else:
                sel_c = st.selectbox("👥 학반 필터링", options=["전체"] + [f"{x}반" for x in sorted(df['반'].unique())])
                f_idx = df[df["반"].astype(int) == int(sel_c.replace("반", ""))].index if sel_c != "전체" else df.index
                
                target_cols = ["반", "번호", "이름"]
                rename_map = {}
                db_cols_ordered = []
                for idx in range(item_count):
                    db_col = f"수행평가{idx+1}"
                    db_cols_ordered.append(db_col)
                    target_cols.append(db_col)
                    rename_map[db_col] = item_titles[idx]
                
                sub_df = df.loc[f_idx, target_cols].rename(columns=rename_map)
                edited_df = st.data_editor(sub_df, use_container_width=True, disabled=["반", "번호", "이름"], hide_index=True)
                
                if st.button("💾 성적 저장하기", type="primary", use_container_width=True):
                    for idx_pos, r_idx in enumerate(f_idx):
                        for idx_c, db_col in enumerate(db_cols_ordered):
                            view_title = item_titles[idx_c]
                            df.loc[r_idx, db_col] = edited_df.iloc[idx_pos][view_title]
                        supabase.table(student_table).upsert(df.loc[r_idx].to_dict()).execute()
                    st.success("🎉 변경된 수행 점수가 안전하게 저장되었습니다!"); st.rerun()

    # ---------------------------------------------------------------------
    # 그림3: 학생 정보 관리 (원래 대형 화면 구성 유지)
    # ---------------------------------------------------------------------
    elif menu_selection == "▶ 학생 정보 관리":
        with st.container(border=True):
            st.markdown("<h3>🔍 학생 신적 정보를 필터링할 교과 선택</h3>", unsafe_allow_html=True)
            f_group = st.selectbox("교과군 선택", ["수리·과학군", "인문·사회군", "예체능군"], key="inf_g")
            f_sub = st.selectbox("세부 과목", ["정보", "국어", "수학", "영어"], key="inf_s")
            f_grade = st.selectbox("학년 지정", ["2학년", "1학년", "3학년"], key="inf_gr")
            f_term = st.selectbox("학기 선택", ["2026학년도 1학기", "2026학년도 2학기"], key="inf_t")

        with st.container(border=True):
            if df.empty:
                st.info("현재 등록된 학생이 없습니다.")
                if st.button("➕ 첫 학생 개별 추가", type="primary"): show_add_student_dialog()
            else:
                sel_c = st.selectbox("👥 학반 필터링", options=["전체"] + [f"{x}반" for x in sorted(df['반'].unique())])
                f_idx = df[df["반"].astype(int) == int(sel_c.replace("반", ""))].index if sel_c != "전체" else df.index
                edited_df = st.data_editor(df.loc[f_idx, ["반", "번호", "이름", "학교 이메일", "비밀번호"]], use_container_width=True, hide_index=True)
                c1, c2 = st.columns([4.8, 1.2])
                with c1:
                    if st.button("➕ 학생 개별 추가"): show_add_student_dialog()
                with c2:
                    if st.button("💾 학생 정보 저장", type="primary", use_container_width=True):
                        for idx_pos, r_idx in enumerate(f_idx):
                            for col in edited_df.columns: df.loc[r_idx, col] = edited_df.iloc[idx_pos][col]
                            supabase.table(student_table).upsert(df.loc[r_idx].to_dict()).execute()
                        st.success("🎉 인적사항이 동기화되었습니다!"); st.rerun()

    # ---------------------------------------------------------------------
    # 🔥 그림4: 평가 대상 과목 구성 (요청 반영: 완벽 세로 정렬 및 50% 너비 축소)
    # ---------------------------------------------------------------------
    elif menu_selection == "▶ 평가 대상 과목 구성":
        st.markdown("<h2>🎯 평가 대상 과목 및 항목 관리</h2>", unsafe_allow_html=True)
        
        # [상단 배치] 1단계 카드
        with st.container(border=True):
            st.markdown("<h3>⚙️ 1. 평가 과목 설정</h3>", unsafe_allow_html=True)
            # CSS 클래스를 주입하여 드롭다운 상자 길이를 50% 반토막으로 압축
            st.markdown('<div class="compact-half-width">', unsafe_allow_html=True)
            sel_g = st.selectbox("교과군 선택", options=["수리·과학군", "인문·사회군", "예체능군"])
            final_sub = st.selectbox("세부 과목", options=["정보", "국어", "수학", "영어"])
            sel_gr = st.selectbox("학년 지정", options=["2학년", "1학년", "3학년"])
            sel_se = st.selectbox("학기 선택", options=["학기를 선택하세요.", "2026학년도 1학기", "2026학년도 2학기"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            subject_key = f"{final_sub}_{sel_gr}_{sel_se}".replace(" ", "_")

        # [마법사 흐름] 학기를 선택하면 우측이 아니라 '바로 아래(세로)'에 2단계 카드가 생성됨
        if sel_se != "학기를 선택하세요.":
            cfg_df = load_db_df(config_table)
            db_match = cfg_df[cfg_df["subject_key"] == subject_key] if not cfg_df.empty else pd.DataFrame()
            
            if not db_match.empty:
                saved_info = db_match.iloc[0]
                init_count = int(saved_info.get("item_count", 3))
                init_titles = [
                    saved_info.get("item1_name", "수행평가1"), 
                    saved_info.get("item2_name", "수행평가2"), 
                    saved_info.get("item3_name", "수행평가3"),
                    saved_info.get("item4_name", "수행평가4"),
                    saved_info.get("item5_name", "수행평가5")
                ]
            else:
                init_count = 3
                init_titles = ["수행평가1", "수행평가2", "수행평가3", "수행평가4", "수행평가5"]

            # 세로로 이어지는 2단계 카드
            with st.container(border=True):
                st.markdown("<h3>🎯 2. 수행평가 항목 구성</h3>", unsafe_allow_html=True)
                
                st.markdown('<div class="compact-half-width">', unsafe_allow_html=True)
                # 반영 항목 개수를 4개 또는 5개로 늘릴 수 있는 드롭박스 (너비 50% 제한)
                item_count = st.selectbox("평가 반영 항목 개수 선택", [1, 2, 3, 4, 5], index=(init_count - 1))
                
                st.markdown("<div style='margin-top:15px; margin-bottom:5px;'><b>📝 각 항목의 제목을 입력하세요:</b></div>", unsafe_allow_html=True)
                
                # 선택한 항목 개수만큼 입력상자가 실시간 세로로 동적 나열됨 (너비 50% 제한)
                item_titles = []
                for i in range(item_count):
                    default_val = init_titles[i] if i < len(init_titles) else f"수행평가_{i+1}"
                    t_in = st.text_input(f"항목 {i+1} 제목", value=default_val, key=f"v_item_title_{i}")
                    item_titles.append(t_in.strip())
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("<hr style='border: 1px dashed #cbd5e1; margin: 20px 0;'>", unsafe_allow_html=True)
                
                # 저장 버튼은 입력창들의 흐름에 맞춰 단정하게 배치
                c_btn1, c_btn2 = st.columns([3.8, 1.2])
                with c_btn2:
                    if st.button("💾 이 과목 설정 저장하기", type="primary", use_container_width=True):
                        config_record = {
                            "subject_key": subject_key,
                            "item_count": item_count,
                            "item1_name": item_titles[0] if item_count >= 1 else "-",
                            "item2_name": item_titles[1] if item_count >= 2 else "-",
                            "item3_name": item_titles[2] if item_count >= 3 else "-",
                            "item4_name": item_titles[3] if item_count >= 4 else "-",
                            "item5_name": item_titles[4] if item_count >= 5 else "-"
                        }
                        supabase.table(config_table).upsert(config_record).execute()
                        st.success("🎉 수행평가 구조 설정이 안전하게 실시간 저장되었습니다!")
                        st.rerun()
        else:
            st.info("💡 위의 **[학기 선택]** 영역을 지정하시면, 바로 아래에 수행평가 반영 항목 구성을 위한 관리 창이 나타납니다.")

    # ---------------------------------------------------------------------
    # 나머지 메뉴 기본 인프라 유지
    # ---------------------------------------------------------------------
    elif menu_selection == "▶ 성적 일괄 업로드 (CSV / Excel)":
        with st.container(border=True):
            st.markdown("<h3>📥 학생 성적 데이터 전체 초기화 및 파일 업로드</h3>", unsafe_allow_html=True)
            up_f = st.file_uploader("명단 파일 선택", type=["csv", "xlsx"])
            if up_f: st.success("파일 업로드 성공 (로직 대기)")

    elif menu_selection == "👑 교사 계정 관리 대장" and st.session_state["logged_teacher_id"] == "admin":
        with st.container(border=True):
            st.markdown("<h3>👑 교사 계정 관리 관제 센터</h3>", unsafe_allow_html=True)
            df_tc = load_db_df(teacher_table)
            st.dataframe(df_tc, use_container_width=True, hide_index=True)
