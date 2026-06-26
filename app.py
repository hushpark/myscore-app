import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import glob
import re
import gspread
from google.oauth2.service_account import Credentials
import csv

# 파일 경로 정의
CONFIG_FILE_MAIN = "master_subjects.csv"
META_FILE = "admin_meta.csv"

# --- 🎯 화면 전체가 절대 옆으로 퍼지지 않도록 centered 고정 ---
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="centered")

# --- 데이터 로드/저장 시스템 (기존 구글 시트 엔진 로직 100% 보존) ---
def load_master_subjects():
    default_structure = {
        "인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"],
        "수리·과학군": ["수학", "과학", "기술·가정", "정보"],
        "예체능군": ["음악", "미술", "체육"]
    }
    df = load_sheet_to_df("master_subjects", ["교과군", "과목명"])
    if not df.empty:
        for _, row in df.iterrows():
            group = str(row['교과군']).strip()
            sub = str(row['과목명']).strip()
            if group in default_structure and sub not in default_structure[group]:
                default_structure[group].append(sub)
    return default_structure

def save_new_subject_to_master(group, subject):
    df = load_sheet_to_df("master_subjects", ["교과군", "과목명"])
    if not ((df['교과군'] == group) & (df['과목명'] == subject)).any():
        new_row = pd.DataFrame([{"교과군": group, "과목명": subject}])
        df = pd.concat([df, new_row], ignore_index=True)
        save_df_to_sheet("master_subjects", df)

@st.cache_data(ttl=10)
def load_admin_credentials():
    df = load_sheet_to_df("admin_meta", ["username", "password"])
    if not df.empty:
        username = str(df.iloc[0].get('username', 'admin')).strip()
        password = str(df.iloc[0].get('password', '1234')).strip()
        return username, password
    return "admin", "1234"

def save_admin_credentials(new_id, new_pw):
    df = pd.DataFrame([{"username": str(new_id).strip(), "password": str(new_pw).strip()}])
    save_df_to_sheet("admin_meta", df)

def get_sheet_names_id(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    safe_semester = semester_str.replace(" ", "_").replace("/", "_")
    return f"cfg_{safe_subject}_{grade}Grade", f"st_{safe_subject}_{grade}_{safe_semester}"

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict):
    st.markdown(f"<div><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True)
    st.table(pd.DataFrame(scores_dict))
    if st.button("닫기", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()

@st.dialog("🔐 계정 정보 수정")
def account_update_dialog():
    curr_id, curr_pw = load_admin_credentials()
    new_id = st.text_input("새 관리자 ID", value=curr_id)
    new_pw = st.text_input("새 암호", type="password")
    confirm_pw = st.text_input("새 암호 확인", type="password")
    if st.button("변경 저장", use_container_width=True, type="primary"):
        if new_id and new_pw == confirm_pw:
            save_admin_credentials(new_id, new_pw)
            st.success("변경 완료!")
            st.rerun()

@st.cache_resource
def init_google_sheet_client():
    try:
        credentials_info = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        return gspread.authorize(creds)
    except: return None

gc = init_google_sheet_client()
SPREADSHEET_NAME = "수행평가_데이터베이스"

def get_google_sheet(sheet_name):
    if gc is None: return None
    try:
        sh = gc.open(SPREADSHEET_NAME)
        try: return sh.worksheet(sheet_name)
        except: return sh.add_worksheet(title=sheet_name, rows="100", cols="20")
    except: return None

def save_df_to_sheet(sheet_name, df):
    wks = get_google_sheet(sheet_name)
    if wks is None: return False
    try:
        wks.clear()
        data = [df.fillna("").columns.tolist()] + df.fillna("").values.tolist()
        wks.update(range_name="A1", values=data)
        return True
    except: return False

@st.cache_data(ttl=5)
def load_sheet_to_df(sheet_name, default_cols=None):
    wks = get_google_sheet(sheet_name)
    if wks is None: return pd.DataFrame(columns=default_cols if default_cols else [])
    try:
        records = wks.get_all_records()
        if not records: return pd.DataFrame(columns=default_cols if default_cols else [])
        return pd.DataFrame(records)
    except: return pd.DataFrame(columns=default_cols if default_cols else [])

@st.cache_data(ttl=15)
def get_active_databases():
    active_list = []
    if gc is None: return active_list
    try:
        sh = gc.open(SPREADSHEET_NAME)
        for wks in wks in sh.worksheets():
            name = wks.title
            if name.startswith("cfg_"):
                core_name = name.replace("cfg_", "")
                match = re.search(r"(.+?)_(1|2|3)_(.+)", core_name)
                if match:
                    active_list.append({"subject": match.group(1).replace("_", " "), "grade": f"{match.group(2)}학년", "semester": match.group(3).replace("_", " ")})
    except: pass
    return active_list

if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 선택", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]
CURRENT_ADMIN_ID, CURRENT_ADMIN_PW = load_admin_credentials()

# =========================================================================
# 🎯 [디자인 대수술 CSS] 스트림릿 내장 Form 전용 암막 강제 해제 및 정중앙 정렬
# =========================================================================
st.markdown("""
    <style>
        /* 배경 전체 테마 다크 네이비 고정 */
        .main, [data-testid="stAppViewContainer"] { background-color: #3e4f5a !important; }
        div[data-testid="stHeader"] { display: none !important; }
        footer { display: none !important; }
        
        /* 가로 380px 수첩 크기 아담한 컴팩트 상자 틀 지정 */
        div[data-testid="stForm"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            padding: 35px 25px 25px 25px !important;
            border-radius: 20px !important;
            box-shadow: 0 15px 40px rgba(0,0,0,0.12) !important;
            max-width: 380px !important;
            margin: 80px auto 0 auto !important;
        }
        
        /* 🎯 [교정 ①] 라디오 버튼 묶음 컨테이너를 상자 정중앙으로 강제 수평 정렬 */
        div[data-testid="stRadio"] {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
        }
        div[data-testid="stRadio"] > div {
            flex-direction: row !important;
            justify-content: center !important;
            align-items: center !important;
            gap: 40px !important;
            margin: 5px 0 10px 0 !important;
        }
        div[data-testid="stRadio"] label p { font-size: 15px !important; font-weight: bold !important; color: #1e293b !important; }
        div[data-testid="stForm"] { border: none !important; padding: 0px !important; box-shadow: none !important; }
        
        /* 입력창 너비 슬림 조절 및 정중앙 정렬 패키지 */
        .stTextInput, .stNumberInput, .stSelectbox {
            max-width: 290px !important;
            margin: 0 auto 5px auto !important;
        }
        .stTextInput input, .stNumberInput input, .stSelectbox div {
            text-align: left !important;
        }
        
        /* 🎯 [교정 ② + ③] 스트림릿 내장 Form 제출 버튼을 정확히 조준하여 정중앙 배치 및 이쁜 인디고 블루 도색 */
        div[data-testid="stFormSubmitButton"] {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            margin-top: 15px !important;
        }
        /* 🚨 !important를 떡칠하여 스트림릿 순정 회색 단추를 완벽하게 파괴하고 예쁜 색상을 강제 주입합니다. */
        button[data-testid="stFormSubmitButton"] {
            background-color: #4a69bd !important; /* 선생님 요청: 바탕색과 찰떡인 인디고 예쁜 색상 */
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            padding: 10px 0px !important;
            border-radius: 8px !important;
            font-size: 15px !important;
            width: 290px !important; /* 입력창 가로 크기와 칼같이 일치시켜 완벽 대칭 구조화 */
            min-width: 290px !important;
            box-shadow: 0 4px 12px rgba(74, 105, 189, 0.25) !important;
            transition: background-color 0.2s !important;
        }
        button[data-testid="stFormSubmitButton"]:hover {
            background-color: #3b54b1 !important;
        }
        
        h2 { font-size: 21px !important; color: #1e293b !important; font-weight: 800 !important; text-align: center !important; margin: 0 0 15px 0 !important; }
        h4 { display: none !important; } 
        
        .footer-notice {
            text-align: center; font-size: 11px; color: #94a3b8; margin-top: 25px; border-top: 1px solid #f1f5f9; padding-top: 12px; font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)


# =========================================================================
# 🔄 일체형 폼 구동 컨트롤러
# =========================================================================
if not st.session_state["admin_logged_in"]:
    
    with st.form("master_unified_form"):
        st.markdown("<h2>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        
        # 교사 / 학생 선택 단추 (가운데 정렬 반영 완료)
        login_mode = st.radio("접속 모드", ["교사", "학생"], label_visibility="collapsed")
        st.markdown("<hr style='max-width: 290px; margin: 10px auto 15px auto; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        
        # 👨‍🏫 1. 교사 모드 입력 컴포넌트
        if login_mode == "교사":
            admin_id = st.text_input("ID", placeholder="아이디를 입력하세요", label_visibility="collapsed", key="ti_id")
            admin_pw = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed", key="ti_pw")
            
            if st.form_submit_button("로그인"):
                if admin_id.strip() == CURRENT_ADMIN_ID and admin_pw == CURRENT_ADMIN_PW:
                    st.session_state["admin_logged_in"] = True
                    st.rerun()
                else:
                    st.error("❌ ID 또는 비밀번호 오류")

        # 🎒 2. 학생 모드 입력 컴포넌트
        elif login_mode == "학생":
            active_dbs = get_active_databases()
            if not active_dbs:
                st.warning("등록된 평가 데이터가 없습니다.")
            else:
                opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs]
                sel_s = st.selectbox("과목", opts_s, label_visibility="collapsed", key="sb_sub")
                
                if sel_s != "과목 및 학기를 선택하세요.":
                    db = active_dbs[opts_s.index(sel_s)-1]
                    cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                    config = load_sheet_to_df(cf_id).iloc[0].to_dict() if not load_sheet_to_df(cf_id).empty else None
                    
                    if config:
                        st.markdown("<hr style='max-width: 290px; margin: 12px auto;'>", unsafe_allow_html=True)
                        classes = [f"{x.strip()}반" for x in str(config.get('선택된반 목록', '1')).split(",") if x.strip()]
                        
                        # 컴팩트 크기로 묶인 학생 3단 컬럼 배치
                        c_frame = st.container()
                        with c_frame:
                            c1, c2, c3 = st.columns(3)
                            with c1: b_in = st.selectbox("반", classes, key="sb_class", label_visibility="collapsed")
                            with n_in = st.number_input("번호", 1, 50, 1, key="ni_num", label_visibility="collapsed")
                            with c3: name_in = st.text_input("이름", placeholder="이름", key="ti_name", label_visibility="collapsed")
                        
                        pw_in = st.text_input("비밀번호", type="password", placeholder="학생 개인 암호 입력", key="ti_st_pw", label_visibility="collapsed")
                        
                        if st.form_submit_button("점수 조회"):
                            df_st = load_sheet_to_df(sf_id)
                            if not df_st.empty:
                                res = df_st[(df_st['반'].astype(int)==int(b_in.replace("반",""))) & (df_st['번호'].astype(int)==n_in) & (df_st['이름'].astype(str)==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                                if not res.empty:
                                    idx = res.index[0]
                                    scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                                    show_result_dialog(name_in, scores)
                                else:
                                    st.error("❌ 일치하는 학생 정보가 없습니다.")
                                    
        st.markdown("<div class='footer-notice'>Designed & Developed by User & AI Creator</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 교사용 관리자 제어판
# -------------------------------------------------------------------------
else:
    with st.form("teacher_dashboard_form"):
        st.markdown("<h2>⚙️ 마스터 제어판</h2>", unsafe_allow_html=True)
        
        btn_c1, btn_col2 = st.columns(2)
        with btn_c1:
            if st.form_submit_button("🔐 계정 정보 수정"): password_update_dialog()
        with btn_col2:
            if st.form_submit_button("🎒 로그아웃"):
                st.session_state["admin_logged_in"] = False
                st.rerun()
                
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        
        g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"]
        sel_g = st.selectbox("교과군 분류", options=g_opts, label_visibility="collapsed")
        
        final_sub, t_g = "", ""
        if sel_g == "➕ 신규 과목 개설":
            t_g = st.selectbox("위치 지정", ["인문·사회군", "수리·과학군", "예체능군"])
            final_sub = st.text_input("새 과목명").strip()
        elif sel_g != "교과군 선택":
            s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
            sel_s = st.selectbox("세부 과목", options=s_opts, label_visibility="collapsed")
            if sel_s != "과목 선택": final_sub = sel_s
            
        c_gr, c_se = st.columns(2)
        with c_gr: sel_gr = st.selectbox("학년 지정", options=GRADE_OPTIONS)
        with c_se: sel_se = st.selectbox("학기 선택", options=SEMESTER_OPTIONS)
        
        if st.form_submit_button("🚀 이 과목 활성화 및 저장") and final_sub and sel_gr != "학년 선택" and sel_se != "학기 선택":
            if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub)
            st.session_state.active_subject = final_sub
            st.session_state.active_grade = sel_gr.replace("학년", "")
            st.session_state.active_semester = sel_se
            st.success(f"✅ 활성화 완료!")

        if "active_subject" in st.session_state and st.session_state.active_subject:
            sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
            cf_id, sf_id = get_sheet_names_id(sub, grd, sem)
            
            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            up_f = st.file_uploader("CSV 파일 업로드", type="csv", label_visibility="collapsed")
            if up_f:
                df_up = pd.read_csv(up_f, encoding='cp949')
                if save_df_to_sheet(sf_id, df_up):
                    st.success("🎉 클라우드 동기화 완료!")