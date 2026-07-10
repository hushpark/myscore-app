import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import time
import io
import re
from supabase import create_client, Client

# 🚨 [최상단 규칙 엄수] 와이드 레이아웃 설정
st.set_page_config(page_title="수행평가 점수 확인 시스템 (Supabase)", layout="wide")

# =========================================================================
# 🎨 [디자인 관통 패치] 브라우저 스크롤 바 차단 및 한 화면 고정 스케일 CSS
# =========================================================================
st.markdown("""
    <style>
        /* 브라우저 전체 우측 스크롤바 원천 차단 및 한 화면 고정 */
        html, body, [data-testid="stAppViewContainer"], .main {
            overflow: hidden !important;
            height: 100vh !important;
        }
        
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        [data-testid="stAppViewContainer"] { margin-left: 0px !important; }
        
        /* 사이드바 구성 패치 */
        .stSidebar, section[data-testid="stSidebar"] { min-width: 280px !important; max-width: 280px !important; background-color: #1e293b !important; box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; }
        [data-testid="stSidebar"] .stRadio label p, [data-testid="stSidebar"] .stRadio label span, [data-testid="stSidebar"] .stRadio label div, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[role="radiogroup"] * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; opacity: 1 !important; }
        
        /* 메뉴 폰트 크기 큰 상태(17px) 유지 및 상단 정렬 복귀 */
        [data-testid="stSidebar"] div[role="radiogroup"] { margin-top: 0px !important; } 
        [data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 17px !important; font-weight: 700 !important; line-height: 2.3 !important; } 
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover * { color: #60a5fa !important; -webkit-text-fill-color: #60a5fa !important; }
        
        /* 메뉴들과 최하단 버튼 사이의 공백 밀기 장치 */
        .sidebar-spacer {
            height: 120px !important;
        }
        
        .sidebar-title { font-size: 24px !important; font-weight: 800 !important; margin-bottom: 5px !important; display: block; }
        .user-info { color: #38bdf8 !important; -webkit-text-fill-color: #38bdf8 !important; font-size: 14px !important; font-weight: 600 !important; margin-bottom: 25px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 12px 0 !important; width: 100% !important; display: block !important; margin-bottom: 8px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] *, [data-testid="stSidebar"] button[kind="secondary"] p { color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; font-size: 15px !important; font-weight: 700 !important; }
        
        /* 마스터 푸른색 계열 버튼 규격화 */
        div.stButton > button[kind="primary"], button[data-testid="stFormSubmitButton"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; padding: 8px 16px !important; }
        div.stButton > button[kind="primary"]:hover, button[data-testid="stFormSubmitButton"]:hover { background-color: #2563eb !important; }
        div.stButton > button[kind="secondary"] { background-color: #ffffff !important; color: #0f172a !important; font-weight: 700 !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
        
        /* 로그인 화면 */
        div[data-testid="stForm"] div[data-testid="stRadio"] { padding-left: 95px !important; margin-bottom: 25px !important; width: 100% !important; }
        div[data-testid="stForm"] div[role="radiogroup"] { display: flex !important; gap: 35px !important; align-items: center !important; }
        
        div[data-testid="InputInstructions"] { display: none !important; }
        div[data-testid="stSelectbox"] label p, div[data-testid="stTextInput"] label p { font-weight: 800 !important; color: #1e293b !important; font-size: 15px !important; }
        div[data-testid="stTextInput"] > div, div[data-testid="stSelectbox"] > div { background-color: #ffffff !important; border: 1px solid #94a3b8 !important; border-radius: 6px !important; }
        div[data-testid="stTextInput"] input { background-color: #ffffff !important; color: #0f172a !important; padding: 8px 12px !important; }
        div[data-testid="stTextInput"] > div:focus-within, div[data-testid="stSelectbox"] > div:focus-within { border: 2px solid #3b82f6 !important; outline: none !important; }
        
        div[data-testid="stForm"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; padding: 45px 40px !important; border-radius: 24px !important; max-width: 440px !important; margin: 70px auto 0 auto !important; box-shadow: 0 10px 25 rgba(0,0,0,0.05) !important; }
        div[data-testid="stForm"] h2 { font-size: 26px !important; text-align: center !important; font-weight: 800 !important; color: #0f172a !important; }
        
        /* 타이틀 영역 구조 */
        .header-title-main { font-size: 32px !important; font-weight: 800 !important; color: #1e293b !important; letter-spacing: -0.5px !important; margin-bottom: 5px !important; }
        .header-nav-sub { font-size: 18px !important; font-weight: 700 !important; color: #1e293b !important; margin-bottom: 25px !important; }
        .menu-title-container { border-bottom: 2px solid #cbd5e1 !important; padding-bottom: 12px !important; margin-bottom: 25px !important; }
        
        /* 안내 가이드라인 박스 */
        .menu-guide-inline { font-size: 14px !important; font-weight: 600 !important; color: #475569 !important; background-color: #f8fafc !important; padding: 8px 16px !important; border-left: 4px solid #3b82f6 !important; border-radius: 4px !important; margin: 0 0 15px 0 !important; width: 100% !important; box-sizing: border-box !important; }

        .sync-giant-title { font-size: 24px !important; font-weight: 800 !important; color: #0f172a !important; margin-bottom: 10px !important; }
        .stButton button { white-space: nowrap !important; word-break: keep-all !important; }

        /* 모든 에러/성공/알림 메시지 폰트 일괄 통일 */
        div[data-testid="stAlert"] * {
            font-size: 14px !important;
            font-weight: 600 !important;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 🔑 [Supabase 원격 데이터베이스 연결 체계 주입]
# =========================================================================
SUPABASE_URL = "https://jwkvojfmhorndnnhscwl.supabase.co"
SUPABASE_KEY = "sb_publishable_6--SHGogHaHSEVO7g3rNjQ_FOHO-XlN"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

master_student_table = "all_students" 
student_table = "student_scores" 
teacher_table = "teacher_accounts"
config_table = "subject_configs"

# 교과군 과목 매핑 딕셔너리
SUBJECT_MAP = {
    "인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"], 
    "수리·과학군": ["수학", "과학", "기술·가정", "정보"], 
    "예체능군": ["음악", "미술", "체육"]
}

def load_db_df(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

def get_active_databases():
    cfg_df = load_db_df(config_table)
    active_list = []
    if not cfg_df.empty and "subject_key" in cfg_df.columns:
        for _, row in cfg_df.iterrows():
            subj_key = str(row["subject_key"])
            parts = subj_key.split("_")
            if len(parts) >= 3:
                subj = parts[0]
                grade = parts[1]
                sem = "_".join(parts[2:])
                active_list.append({"subject": subj, "grade": grade, "semester": sem.replace("_", " "), "key": subj_key})
    return active_list

def get_subject_item_names(subject_key):
    cfg_df = load_db_df(config_table)
    if not cfg_df.empty and "subject_key" in cfg_df.columns:
        match = cfg_df[cfg_df["subject_key"] == subject_key]
        if not match.empty:
            row = match.iloc[0]
            count = int(row.get("item_count", 3))
            titles = [row.get("item1_name", "수행평가1"), row.get("item2_name", "수행평가2"), row.get("item3_name", "수행평가3"), row.get("item4_name", "수행평가4"), row.get("item5_name", "수행평가5")]
            return count, titles
    return 3, ["수행평가1", "수행평가2", "수행평가3", "수행평가4", "수행평가5"]

# =========================================================================
# ➕ [다이얼로그 팝업창 모듈]
# =========================================================================
@st.dialog("➕ 담당 교사 개별 추가")
def show_add_teacher_dialog():
    st.markdown("새로 임용/등록할 선생님의 권한 정보를 입력해 주세요.")
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
                    time.sleep(0.3); st.rerun()
                except Exception as e: st.error(f"❌ 등록 실패: {e}")

@st.dialog("➕ 학적 변동 학생 추가 (마스터 매칭)")
def show_add_student_dialog(subject_key):
    st.markdown("전입/학적 변동 학생의 정보를 입력하면 마스터 대장에서 계정을 자동 매칭합니다.")
    with st.form("add_student_form", border=False):
        c1, c2, c3 = st.columns(3)
        with c1: ban = st.text_input("반", placeholder="예: 1")
        with c2: num = st.text_input("번호", placeholder="예: 15")
        with c3: name = st.text_input("이름", placeholder="예: 홍길동")
        if st.form_submit_button("💾 해당 학생 이 과목에 배정하기", use_container_width=True):
            if ban and num and name:
                mst = supabase.table(master_student_table).select("school_email").eq("반", int(ban)).eq("번호", int(num)).eq("이름", name.strip()).execute().data
                if mst:
                    email = mst[0]["school_email"]
                    supabase.table(student_table).upsert({"subject_key": subject_key, "반": int(ban), "번호": int(num), "이름": name.strip(), "school_email": email, "수행평가1": 0, "수행평가2": 0, "수행평가3": 0, "수행평가4": 0, "수행평가5": 0, "성적조회 횟수": 0, "최종 확인일시": "-"}).execute()
                    st.success("🎉 과목 배정 완료!"); time.sleep(0.5); st.rerun()
                else: st.error("❌ 오류: 전교생 마스터 대장에 해당 학생이 존재하지 않습니다. 최고관리자에게 마스터 등록을 먼저 요청하세요.")

# 세션 제어 상태 초기화
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "student_logged_in" not in st.session_state: st.session_state["student_logged_in"] = False
if "logged_student_id" not in st.session_state: st.session_state["logged_student_id"] = ""
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = False

df = load_db_df(student_table)

# =========================================================================
# 🔓 [1단계] 로그인 시스템
# =========================================================================
if not st.session_state["admin_logged_in"] and not st.session_state["student_logged_in"]:
    with st.container():
        with st.form("master_unified_form"):
            st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
            login_mode = st.radio("접속 모드", ["학생", "교사"], horizontal=True, label_visibility="collapsed")
            user_id_input = st.text_input("ID / 이메일", placeholder="ID 또는 이메일을 입력하세요", label_visibility="collapsed")
            user_pw_input = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed")
            
            b_col2 = st.columns([1.0, 1.8, 1.0])[1]
            submit_active = b_col2.form_submit_button("로그인", use_container_width=True)
            
            if submit_active:
                clean_id = str(user_id_input).strip()
                clean_pw = str(user_pw_input).strip()
                if login_mode == "학생":
                    res = supabase.table(master_student_table).select("*").eq("school_email", clean_id).eq("password", clean_pw).execute().data
                    if res:
                        st.session_state["student_logged_in"] = True
                        st.session_state["logged_student_id"] = clean_id
                        st.session_state["student_info"] = res[0]
                        st.rerun()
                    else: st.error("❌ 학생 로그인 정보가 올바르지 않습니다.")
                elif login_mode == "교사":
                    if clean_id == "admin" and clean_pw == "1234":
                        st.session_state["admin_logged_in"] = True
                        st.session_state["logged_teacher_id"] = "admin"
                        st.session_state["teacher_name"] = "최고관리자"
                        st.session_state["allowed_subjects"] = ["마스터"]
                        st.session_state["current_menu"] = "학생 조회 현황 모니터링"
                        st.rerun()
                    else:
                        df_tc = load_db_df(teacher_table)
                        id_match = df_tc[df_tc['교사_ID'] == clean_id] if not df_tc.empty else pd.DataFrame()
                        if not id_match.empty and str(id_match.iloc[0]['비밀번호']) == clean_pw:
                            row = id_match.iloc[0]
                            st.session_state["admin_logged_in"] = True
                            st.session_state["logged_teacher_id"] = clean_id
                            st.session_state["teacher_name"] = str(row['교사_성명']).strip()
                            st.session_state["allowed_subjects"] = [s.strip() for s in str(row['담당_과목']).split(",") if s.strip()]
                            st.session_state["current_menu"] = "학생 조회 현황 모니터링"
                            st.rerun()
                        else: st.error("❌ 교사 로그인 실패")

# =========================================================================
# 🎓 [2단계-A] 학생 화면 (통합 마스터 조인 연동)
# =========================================================================
elif st.session_state["student_logged_in"]:
    st.markdown(f"<h2>수행평가 점수 확인 시스템 (학생 모드)</h2>", unsafe_allow_html=True)
    if st.button("🚪 로그아웃"): st.session_state.clear(); st.rerun()
    active_dbs = get_active_databases()
    if not active_dbs: st.warning("현재 활성화된 과목 데이터베이스가 없습니다.")
    else:
        opts_s = ["과목을 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in active_dbs]
        sel_s = st.selectbox("조회할 교과과정 선택", opts_s)
        if sel_s != "과목을 선택하세요." and st.button("🚀 나의 수행평가 성적 실시간 검증", type="primary", use_container_width=True):
            chosen_db = active_dbs[opts_s.index(sel_s)-1]
            res = supabase.table(student_table).select("*").eq("subject_key", chosen_db['key']).eq("school_email", st.session_state["logged_student_id"]).execute().data
            if res:
                st.success(f"🔍 {st.session_state['student_info']['이름']} 학생의 성적이 성공적으로 조회되었습니다.")
                st.json(res[0])
            else: st.error("❌ 해당 과목에 배정된 성적 데이터가 아직 없습니다.")

# =========================================================================
# 🔒 [2단계-B] 교사 화면
# =========================================================================
elif st.session_state["admin_logged_in"]:
    menus = ["학생 조회 현황 모니터링", "수행 평가 성적 입력", "학생 기본 정보 관리", "평가 대상 과목 구성"]
    if st.session_state["logged_teacher_id"] == "admin": 
        menus.append("👑 전교생 마스터 관리 대장") # 최고관리자 메뉴 신설
        menus.append("👑 교사 계정 관리 대장")
        
    if "current_menu" not in st.session_state or st.session_state["current_menu"] not in menus:
        st.session_state["current_menu"] = menus[0]

    with st.sidebar:
        st.markdown('<span class="sidebar-title">📋 교사 메뉴</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="user-info">👤 {st.session_state["teacher_name"]} 선생님 접속 중</div>', unsafe_allow_html=True)
        st.markdown("---")
        menu_selection = st.radio("메뉴 선택", menus, index=menus.index(st.session_state["current_menu"]), label_visibility="collapsed")
        if menu_selection != st.session_state["current_menu"]:
            st.session_state["current_menu"] = menu_selection
            st.rerun()
        st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
        if st.sidebar.button("🚪 로그아웃", type="secondary", use_container_width=True): st.session_state.clear(); st.rerun()

    st.markdown(f"""
        <div class="header-title-main">수행평가 점수 확인 시스템</div>
        <div class="header-nav-sub" style="border-bottom: 2px solid #cbd5e1; padding-bottom: 12px; margin-bottom: 25px;">
            📍 현재 위치: 교사 모드 > <span style="color: #3b82f6;">📂 {menu_selection}</span>
        </div>
    """, unsafe_allow_html=True)

    if not df.empty and "반" in df.columns and "번호" in df.columns: df = df.sort_values(by=["반", "번호"])
    layout_left, layout_right = st.columns([3.5, 6.5])

    # ---------------------------------------------------------------------
    # 1번 메뉴: 학생 조회 현황 모니터링
    # ---------------------------------------------------------------------
    if menu_selection == "학생 조회 현황 모니터링":
        registered_dbs = get_active_databases()
        if "마스터" not in st.session_state["allowed_subjects"]:
            registered_dbs = [d for d in registered_dbs if d['subject'].strip() in st.session_state["allowed_subjects"]]
        
        if not registered_dbs:
            with layout_left: st.info("📢 현재 개설되었거나 권한이 연결된 과목이 없습니다.")
        else:
            with layout_left:
                selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                selected_db_str = st.selectbox("교과 선택", options=selector_options, label_visibility="collapsed", key="mon_sub")
                chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                df = pd.DataFrame(supabase.table(student_table).select("*").eq("subject_key", chosen_db['key']).execute().data)
                class_options = ["전체 학급 보기"]
                if not df.empty and "반" in df.columns: class_options += [f"{x}반" for x in sorted(df['반'].unique())]
                selected_class = st.selectbox("학급 선택", options=class_options)
                
            with layout_right:
                if df.empty: st.info("📢 데이터가 없습니다.")
                else:
                    r_df = df.copy()
                    if selected_class != "전체 학급 보기": r_df = r_df[r_df['반'].astype(int) == int(selected_class.replace("반",""))]
                    item_count, item_titles = get_subject_item_names(chosen_db['key'])
                    disp_cols = ["반", "번호", "이름", "school_email"]
                    rename_map = {"school_email": "학교 이메일"}
                    for idx in range(item_count):
                        disp_cols.append(f"수행평가{idx+1}")
                        rename_map[f"수행평가{idx+1}"] = item_titles[idx]
                    disp_cols += ["성적조회 횟수", "최종 확인일시"]
                    st.dataframe(r_df[disp_cols].rename(columns=rename_map), use_container_width=True, hide_index=True, height=650)

    # ---------------------------------------------------------------------
    # 2번 메뉴: 수행 평가 성적 입력 (💡 마스터 자동 결합 및 여백 4 정렬 완료)
    # ---------------------------------------------------------------------
    elif menu_selection == "수행 평가 성적 입력":
        registered_dbs = get_active_databases()
        if "마스터" not in st.session_state["allowed_subjects"]:
            registered_dbs = [d for d in registered_dbs if d['subject'].strip() in st.session_state["allowed_subjects"]]

        if not registered_dbs:
            with layout_left: st.info("📢 권한이 연결된 과목이 없습니다.")
        else:
            with layout_left:
                selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                selected_db_str = st.selectbox("교과 선택", options=selector_options, label_visibility="collapsed")
                chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                item_count, item_titles = get_subject_item_names(chosen_db['key'])
                
                df_base = pd.DataFrame(supabase.table(student_table).select("*").eq("subject_key", chosen_db['key']).execute().data)
                class_options_ed = ["전체 학급 보기"]
                if not df_base.empty and "반" in df_base.columns: class_options_ed += [f"{x}반" for x in sorted(df_base['반'].unique())]
                selected_class_ed = st.selectbox("학급 선택", options=class_options_ed)
                
                st.markdown("<hr style='margin: 15px 0; border: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)
                st.markdown("💡 **양식을 다운로드하여 성적을 일괄 업로드하세요.**")
                template_df = pd.DataFrame({"반": [1, 1], "번호": [1, 2], "이름": ["홍길동", "이영희"]})
                for col in item_titles[:item_count]: template_df[col] = [20, 18]
                st.download_button("📥 성적 일괄 업로드 양식 받기", data=template_df.to_csv(index=False).encode('utf-8-sig'), file_name="수행성적업로드양식.csv", mime="text/csv", use_container_width=True)
                
                up_f = st.file_uploader("엑셀 파일 올리기", type=["csv", "xlsx"], label_visibility="collapsed")
                excel_loaded_df = None
                if up_f:
                    try:
                        df_up = pd.read_csv(up_f) if up_f.name.endswith(".csv") else pd.read_excel(up_f)
                        df_up.columns = [c.strip() for c in df_up.columns]
                        for idx_t, title in enumerate(item_titles[:item_count]):
                            if title in df_up.columns: df_up[f"수행평가{idx_t+1}"] = df_up[title]
                        excel_loaded_df = df_up
                        st.caption("✅ 파일 로드 성공! 오른쪽 표에 가동 매칭되었습니다.")
                    except Exception as e: st.error(f"❌ 해석 실패: {e}")
                    
                for _ in range(4): st.write("")
                save_trigger = st.button("💾 성적 저장하기", type="primary", use_container_width=True, key="original_left_save_btn")

            with layout_right:
                st.markdown('<p class="menu-guide-inline">💡 개인별 점수를 수정한 후, 왼쪽 패널 하단의 [💾 성적 저장하기] 버튼을 누르시면 안전하게 저장됩니다.</p>', unsafe_allow_html=True)
                df = excel_loaded_df.copy() if excel_loaded_df is not None else df_base.copy()
                
                if df.empty: st.info("📢 데이터가 없습니다. 학생 기본 정보 관리를 통해 이 과목에 학생을 먼저 배정해 주세요.")
                else:
                    if selected_class_ed != "전체 학급 보기": f_idx = df[df["반"].astype(int) == int(selected_class_ed.replace("반", ""))].index
                    else: f_idx = df.index
                    
                    target_cols = ["반", "번호", "이름"]
                    rename_map = {}
                    df["합계"] = 0
                    for idx in range(item_count):
                        db_col = f"수행평가{idx+1}"
                        if db_col not in df.columns: df[db_col] = 0
                        df[db_col] = df[db_col].fillna(0).astype(int)
                        target_cols.append(db_col)
                        rename_map[db_col] = item_titles[idx]
                        df["합계"] += df[db_col]
                    target_cols.append("합계")
                    
                    sub_df = df.loc[f_idx, target_cols].rename(columns=rename_map)
                    edited_df = st.data_editor(sub_df, use_container_width=True, disabled=["반", "번호", "이름", "합계"], hide_index=True, height=600)
                    
                    if save_trigger:
                        try:
                            for _pos in range(len(edited_df)):
                                vr = edited_df.iloc[_pos]
                                orig_idx = f_idx[_pos]
                                # 💡 마스터 구조 바인딩: 마스터 테이블에서 학적 이메일 자동 탐색 주입
                                email = df.loc[orig_idx, "school_email"] if "school_email" in df.columns else supabase.table(master_student_table).select("school_email").eq("반", int(vr["반"])).eq("번호", int(vr["번호"])).eq("이름", str(vr["이름"]).strip()).execute().data[0]["school_email"]
                                
                                sc_record = {"subject_key": chosen_db['key'], "반": int(vr["반"]), "번호": int(vr["번호"]), "이름": str(vr["이름"]), "school_email": email}
                                for idx_c in range(item_count):
                                    sc_record[f"수행평가{idx_c+1}"] = int(vr[item_titles[idx_c]])
                                supabase.table(student_table).upsert(sc_record).execute()
                            st.success("🎉 수행 평가 점수가 성공적으로 원격 DB에 저장되었습니다!"); time.sleep(0.5); st.rerun()
                        except Exception as e: st.error(f"❌ 저장 실패: {e}")

    # ---------------------------------------------------------------------
    # 3번 메뉴: 학생 기본 정보 관리 (💡 학적 변동 대응용 컴팩트 대장)
    # ---------------------------------------------------------------------
    elif menu_selection == "학생 기본 정보 관리":
        registered_dbs = get_active_databases()
        if "마스터" not in st.session_state["allowed_subjects"]:
            registered_dbs = [d for d in registered_dbs if d['subject'].strip() in st.session_state["allowed_subjects"]]
            
        if not registered_dbs:
            with layout_left: st.info("📢 개설된 과목이 없습니다.")
        else:
            with layout_left:
                selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                selected_db_str = st.selectbox("교과 선택", options=selector_options, key="inf_sub")
                chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                df = pd.DataFrame(supabase.table(student_table).select("*").eq("subject_key", chosen_db['key']).execute().data)
                class_opts = ["전체"]
                if not df.empty and "반" in df.columns: class_opts += [f"{x}반" for x in sorted(df['반'].unique())]
                sel_c = st.selectbox("학반 필터링", options=class_opts)
                
                for _ in range(15): st.write("")
                if st.button("➕ 전입/학적변동 학생 추가", use_container_width=True): show_add_student_dialog(chosen_db['key'])
                save_info_trigger = st.button("💾 이 과목 학생 명단 저장", type="primary", use_container_width=True)

            with layout_right:
                if df.empty: st.info("📢 배정된 명단이 없습니다. 전입생 추가 기능이나 최고관리자의 마스터 연동 기능을 이용해 명단을 세팅하세요.")
                else:
                    f_idx = df[df["반"].astype(int) == int(sel_c.replace("반", ""))].index if sel_c != "전체" else df.index
                    edited_df = st.data_editor(df.loc[f_idx, ["반", "번호", "이름"]], use_container_width=True, hide_index=True, height=650)
                    if save_info_trigger:
                        for _pos in range(len(edited_df)):
                            vr = edited_df.iloc[_pos]
                            orig_r = df.loc[f_idx[_pos]].to_dict()
                            orig_r["반"], orig_r["번호"], orig_r["이름"] = int(vr["반"]), int(vr["번호"]), str(vr["이름"])
                            supabase.table(student_table).upsert(orig_r).execute()
                        st.success("🎉 과목 학적 정보 저장 완료!"); st.rerun()

    # ---------------------------------------------------------------------
    # 4번 메뉴: 평가 대상 과목 구성
    # ---------------------------------------------------------------------
    elif menu_selection == "평가 대상 과목 구성":
        main_col1, main_col2 = layout_left, layout_right
        with main_col1:
            with st.container(border=True):
                st.markdown('<div class="sync-giant-title">⚙️ 1. 평가 과목 설정</div>', unsafe_allow_html=True)
                allowed_trimmed = [str(x).strip() for x in st.session_state.get("allowed_subjects", [])]
                is_admin = (st.session_state.get("logged_teacher_id") == "admin" or "마스터" in allowed_trimmed)
                
                if not is_admin and len(allowed_trimmed) == 1:
                    single_subject = allowed_trimmed[0]
                    detected_group = "인문·사회군"
                    for g_name, sub_list in SUBJECT_MAP.items():
                        if single_subject in sub_list: detected_group = g_name; break
                    st.text_input("교과군 (자동지정)", value=detected_group, disabled=True)
                    st.text_input("세부 과목 (자동지정)", value=single_subject, disabled=True)
                    sel_g, final_sub = detected_group, single_subject
                    sel_se = st.selectbox("학기 선택", options=["학기를 선택하세요.", "2026학년도 1학기", "2026학년도 2학기"])
                    sel_gr = st.selectbox("학년 지정", options=["학년을 선택하세요.", "1학년", "2학년", "3학년"])
                else:
                    sel_g = st.selectbox("교과군 선택", options=["교과군을 선택하세요.", "인문·사회군", "수리·과학군", "예체능군"])
                    raw_subs = SUBJECT_MAP.get(sel_g, []) if sel_g != "교과군을 선택하세요." else []
                    filtered_subs = raw_subs if is_admin else [s for s in raw_subs if s in allowed_trimmed]
                    final_sub = st.selectbox("세부 과목", options=["과목을 선택하세요."] + filtered_subs)
                    sel_se = st.selectbox("학기 선택", options=["학기를 선택하세요.", "2026학년도 1학기", "2026학년도 2학기"])
                    sel_gr = st.selectbox("학년 지정", options=["학년을 선택하세요.", "1학년", "2학년", "3학년"])

        if sel_g != "교과군을 선택하세요." and final_sub != "과목을 선택하세요." and sel_gr != "학년을 선택하세요." and sel_se != "학기를 선택하세요.":
            with main_col2:
                subject_key = f"{final_sub}_{sel_gr}_{sel_se}".replace(" ", "_")
                cfg_df = load_db_df(config_table)
                db_match = cfg_df[cfg_df["subject_key"] == subject_key] if not cfg_df.empty else pd.DataFrame()
                init_count = int(db_match.iloc[0]["item_count"]) if not db_match.empty else 3
                
                with st.container(border=True):
                    st.markdown('<div class="sync-giant-title">🎯 2. 수행평가 항목 구성</div>', unsafe_allow_html=True)
                    item_count = st.selectbox("평가 항목 개수", [1,2,3,4,5], index=init_count-1)
                    item_titles = []
                    for i in range(item_count):
                        t_in = st.text_input(f"항목 {i+1} 제목", value=f"수행평가{i+1}", key=f"cfg_t_{i}")
                        item_titles.append(t_in.strip())
                    if st.button("💾 과목 설정 저장", type="primary", use_container_width=True):
                        rec = {"subject_key": subject_key, "item_count": item_count}
                        for idx_c in range(5): rec[f"item{idx_c+1}_name"] = item_titles[idx_c] if idx_c < len(item_titles) else "-"
                        supabase.table(config_table).upsert(rec).execute()
                        st.success("🎉 과목 구성 완료!"); time.sleep(0.3); st.rerun()

    # ---------------------------------------------------------------------
    # 5번 메뉴: 👑 전교생 마스터 관리 대장 (✨ 완벽 통합 가동)
    # ---------------------------------------------------------------------
    elif menu_selection == "👑 전교생 마스터 관리 대장" and st.session_state["logged_teacher_id"] == "admin":
        with layout_left:
            st.markdown("📂 **전교생 마스터 명단 일괄 가져오기**")
            st.caption("나이스 학적 데이터를 학년, 반, 번호, 이름, school_email, password 구조로 업로드하세요.")
            mst_f = st.file_uploader("전교생 마스터 엑셀 파일 업로드", type=["csv", "xlsx"])
            if mst_f:
                try:
                    df_mst = pd.read_csv(mst_f) if mst_f.name.endswith(".csv") else pd.read_excel(mst_f)
                    if st.button("🚀 전교생 마스터 원격 동기화 실행", type="primary", use_container_width=True):
                        supabase.table(master_student_table).delete().neq("반", 0).execute()
                        for _, r in df_mst.iterrows():
                            supabase.table(master_student_table).upsert({"학년": int(r.get("학년", 1)), "반": int(r["반"]), "번호": int(r["번호"]), "이름": str(r["이름"]).strip(), "school_email": str(r["school_email"]).strip(), "password": str(r.get("password", "1234")).strip()}).execute()
                        st.success("🎉 전교생 마스터 대장 업로드 세이브 완료!"); time.sleep(0.5); st.rerun()
                except Exception as e: st.error(f"❌ 해석 실패: {e}")
        with layout_right:
            df_mst_view = load_db_df(master_student_table)
            if not df_mst_view.empty: df_mst_view = df_mst_view.sort_values(by=["학년", "반", "번호"]).reset_index(drop=True)
            st.data_editor(df_mst_view, use_container_width=True, hide_index=True, height=650)

    # ---------------------------------------------------------------------
    # 6번 메뉴: 교사 계정 관리 대장
    # ---------------------------------------------------------------------
    elif menu_selection == "👑 교사 계정 관리 대장" and st.session_state["logged_teacher_id"] == "admin":
        df_tc = load_db_df(teacher_table)
        with layout_left:
            if st.button("👨‍🏫 교사 개별 신규 추가", use_container_width=True): show_add_teacher_dialog()
            save_tc_trigger = st.button("💾 교사 정보 원격 저장", type="primary", use_container_width=True)
        with layout_right:
            edited_tc_df = st.data_editor(df_tc, use_container_width=True, num_rows="fixed", hide_index=True, key="master_tc_editor", height=650)
            if save_tc_trigger:
                for record in edited_tc_df.to_dict(orient="records"):
                    if record.get("교사_ID"): supabase.table(teacher_table).upsert(record).execute()
                st.success("🎉 교사 권한 원격 세이브 완료!"); st.rerun()
