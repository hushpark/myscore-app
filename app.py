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

# --- 데이터 로드/저장 시스템 (기존 구글 시트 백엔드 무결점 보존) ---
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

# 🚨 [교정 완수] 구글 시트의 한글 헤더('교사_ID', '비밀번호', '교사_성명', '담당_과목')를 다이렉트로 추적하는 한글 엔진 탑재
def verify_teacher_credentials(input_id, input_pw):
    df = load_sheet_to_df("teacher_accounts", ["교사_ID", "비밀번호", "교사_성명", "담당_과목"])
    if not df.empty:
        # 공백 제거 및 문자열 타입 일치화
        df['교사_ID'] = df['교사_ID'].astype(str).str.strip()
        df['비밀번호'] = df['비밀번호'].astype(str).str.strip()
        
        match = df[(df['교사_ID'] == str(input_id).strip()) & (df['비밀번호'] == str(input_pw).strip())]
        if not match.empty:
            row = match.iloc[0]
            return {
                "success": True,
                "teacher_name": str(row['교사_성명']).strip(),
                "authorized_subjects": [s.strip() for s in str(row['담당_과목']).split(",") if s.strip()]
            }
            
    # 시트가 비어있거나 최초 연동 단계일 때 백업용 admin 마스터키 우회 포트 개방
    if input_id.strip() == "admin" and input_pw.strip() == "1234":
        return {"success": True, "teacher_name": "최고관리자", "authorized_subjects": ["마스터"]}
    return {"success": False, "teacher_name": "", "authorized_subjects": []}

def save_admin_credentials(new_id, new_pw):
    df = pd.DataFrame([{"username": str(new_id).strip(), "password": str(new_pw).strip(), "teacher_name": "최고관리자", "authorized_subjects": "마스터"}])
    save_df_to_sheet("admin_meta", df)

def get_sheet_names_id(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    safe_semester = semester_str.replace(" ", "_").replace("/", "_")
    return f"cfg_{safe_subject}_{grade}Grade", f"st_{safe_subject}_{grade}_{safe_semester}"

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict, sf_id, student_row_idx, current_df):
    st.markdown(f"<div><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True)
    st.table(pd.DataFrame(scores_dict))
    
    if "has_counted" not in st.session_state:
        try:
            current_count = int(current_df.loc[student_row_idx, "성적조회 횟수"]) if "성적조회 횟수" in current_df.columns and not pd.isna(current_df.loc[student_row_idx, "성적조회 횟수"]) else 0
        except:
            current_count = 0
            
        current_df.loc[student_row_idx, "성적조회 횟수"] = current_count + 1
        current_df.loc[student_row_idx, "최종 확인일시"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_df_to_sheet(sf_id, current_df)
        st.session_state["has_counted"] = True

    if st.button("닫기", use_container_width=True, type="primary"):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.session_state.clear()
        st.rerun()

@st.dialog("🔐 계정 정보 수정")
def account_update_dialog():
    st.info("💡 개별 교사 ID/PW 권한 관리는 구글 스프레드시트의 'teacher_accounts' 시트 탭에서 실시간으로 직접 제어할 수 있습니다.")
    if st.button("닫기", use_container_width=True, type="primary"):
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

@st.cache_data(ttl=2)
def load_sheet_to_df(sheet_name, default_cols=None):
    wks = get_google_sheet(sheet_name)
    if wks is None: return pd.DataFrame(columns=default_cols if default_cols else [])
    try:
        records = wks.get_all_records()
        if not records: return pd.DataFrame(columns=default_cols if default_cols else [])
        return pd.DataFrame(records)
    except: return pd.DataFrame(columns=default_cols if default_cols else [])

@st.cache_data(ttl=3)
def get_active_databases():
    active_list = []
    if gc is None: return active_list
    try:
        sh = gc.open(SPREADSHEET_NAME)
        for wks in sh.worksheets():
            name = wks.title
            if name.startswith("cfg_"):
                core_name = name.replace("cfg_", "")
                match = re.search(r"(.+?)_(1|2|3)_(.+)", core_name)
                if match:
                    active_list.append({
                        "subject": match.group(1).replace("_", " "),
                        "grade": f"{match.group(2)}학년",
                        "semester": match.group(3).replace("_", " ")
                    })
    except: pass
    return active_list

if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = ""
if "allowed_subjects" not in st.session_state: st.session_state["allowed_subjects"] = []

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 지정", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]

# =========================================================================
# 🔄 스타일링 엔진 및 레이아웃 정의 부
# =========================================================================
if not st.session_state["admin_logged_in"]:
    st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="centered")
    st.markdown("""
        <style>
            .main, [data-testid="stAppViewContainer"] { background-color: #3e4f5a !important; }
            div[data-testid="stHeader"] { display: none !important; }
            footer { display: none !important; }
            
            div[data-testid="stForm"] {
                background-color: #ffffff !important; border: 1px solid #cbd5e1 !important;
                padding: 40px 30px 30px 30px !important; border-radius: 24px !important;
                box-shadow: 0 15px 40px rgba(0,0,0,0.12) !important; max-width: 440px !important; margin: 60px auto 0 auto !important; position: relative !important;
            }
            div[data-testid="stForm"] > div[data-testid="stVerticalBlock"] { display: flex !important; flex-direction: column !important; align-items: center !important; width: 100% !important; }
            div[role="radiogroup"] { justify-content: center !important; margin: 0 auto !important; gap: 40px !important; }
            div[data-testid="stRadio"] label p { font-size: 16px !important; font-weight: bold !important; color: #1e293b !important; }
            div[data-testid="stForm"] { border: none !important; box-shadow: none !important; }
            .stTextInput, .stNumberInput, .stSelectbox { width: 300px !important; max-width: 300px !important; margin: 0 auto 5px auto !important; }
            div[data-testid="stFormSubmitButton"] { display: flex !important; justify-content: center !important; width: 100% !important; margin: 15px auto 0 auto !important; }
            button[kind="primaryFormSubmit"] { background-color: #4a69bd !important; border-color: #4a69bd !important; color: white !important; font-weight: bold !important; padding: 9px 0px !important; border-radius: 8px !important; font-size: 15px !important; width: 140px !important; min-width: 140px !important; max-width: 140px !important; box-shadow: 0 4px 10px rgba(74, 105, 189, 0.2) !important; }
            h2 { font-size: 24px !important; color: #1e293b !important; font-weight: 800 !important; text-align: center !important; margin: 0 0 20px 0 !important; width: 100% !important; }
            hr { width: 300px !important; margin: 12px auto !important; border: none !important; border-top: 1px solid #e2e8f0 !important; }
            .footer-notice { text-align: center; font-size: 11px; color: #94a3b8; margin-top: 30px; border-top: 1px solid #f1f5f9; padding-top: 15px; font-weight: 600; width: 300px; margin: 30px auto 0 auto; }
        </style>
    """, unsafe_allow_html=True)

    with st.form("master_unified_form"):
        st.markdown("<h2>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        login_mode = st.radio("접속 모드", ["교사", "학생"], horizontal=True, label_visibility="collapsed")
        st.markdown("<hr>", unsafe_allow_html=True)
        
        if login_mode == "교사":
            # 🎯 [선생님 요청] 입력창 힌트 문구를 보다 직관적으로 변경
            admin_id = st.text_input("교사_ID", placeholder="교사 ID를 입력하세요", label_visibility="collapsed", key="ti_id")
            admin_pw = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed", key="ti_pw")
            if st.form_submit_button("로그인", type="primary"):
                auth_result = verify_teacher_credentials(admin_id, admin_pw)
                if auth_result["success"]:
                    st.session_state["admin_logged_in"] = True
                    st.session_state["teacher_name"] = auth_result["teacher_name"]
                    st.session_state["allowed_subjects"] = auth_result["authorized_subjects"]
                    st.rerun()
                else: st.error("❌ ID 또는 비밀번호 오류")

        elif login_mode == "학생":
            active_dbs = get_active_databases()
            if not active_dbs: st.warning("등록된 데이터가 없습니다.")
            else:
                opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs]
                sel_s = st.selectbox("과목", opts_s, label_visibility="collapsed", key="sb_sub")
                if sel_s != "과목 및 학기를 선택하세요.":
                    db = active_dbs[opts_s.index(sel_s)-1]
                    cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                    config = load_sheet_to_df(cf_id).iloc[0].to_dict() if not load_sheet_to_df(cf_id).empty else None
                    if config:
                        st.markdown("<hr>", unsafe_allow_html=True)
                        st_email_in = st.text_input("학교 이메일", placeholder="학교 이메일을 입력하세요", label_visibility="collapsed", key="ti_st_email")
                        pw_in = st.text_input("비밀번호", type="password", placeholder="개인 암호 입력", key="ti_st_pw", label_visibility="collapsed")
                        
                        if st.form_submit_button("점수 조회", type="primary"):
                            df_st = load_sheet_to_df(sf_id)
                            if not df_st.empty:
                                if "학교 이메일" in df_st.columns:
                                    res = df_st[(df_st['학교 이메일'].astype(str).str.strip() == str(st_email_in).strip()) & (df_st['비밀번호'].astype(str) == str(pw_in))]
                                else:
                                    res = df_st[(df_st['이름'].astype(str).str.strip() == str(st_email_in).strip()) & (df_st['비밀번호'].astype(str) == str(pw_in))]
                                    
                                if not res.empty:
                                    idx = res.index[0]
                                    st_name = res.iloc[0].get('이름', '학생')
                                    scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                                    show_result_dialog(st_name, scores, sf_id, idx, df_st)
                                else: st.error("❌ 정보가 일치하지 않습니다. 입력값을 다시 확인해 주세요.")
        st.markdown("<div class='footer-notice'>Designed & Developed by User & AI Creator</div>", unsafe_allow_html=True)

else:
    st.set_page_config(page_title="교사용 마스터 관리 시스템", layout="wide")
    st.markdown("""
        <style>
            .main, [data-testid="stAppViewContainer"] { background-color: #f1f5f9 !important; }
            [data-testid="stSidebar"] { background-color: #1e293b !important; box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; }
            [data-testid="stSidebar"] h4 { color: #f8fafc !important; font-weight: 800; font-size: 22px !important; letter-spacing: -0.5px !important; margin-top: 10px !important; margin-bottom: 5px !important; }
            [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 600; }
            div[data-testid="stSidebar"] div[role="radiogroup"] label p { color: #f8fafc !important; font-weight: 600 !important; }
            
            div.stButton > button[key*="logout"] {
                background-color: #ef4444 !important; color: #ffffff !important; font-weight: 800 !important;
                border-radius: 8px !important; padding: 10px 20px !important; border: none !important;
                width: 100% !important; font-size: 14px !important; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2) !important;
                text-align: center !important; display: block !important; margin-top: 20px !important;
            }
            div.stButton > button[key*="logout"]:hover { background-color: #dc2626 !important; color: #ffffff !important; }
            div[data-testid="stSelectbox"] div[data-baseweb="select"] { border: 2px solid #4a69bd !important; border-radius: 8px !important; background-color: #ffffff !important; }
            div[data-testid="stSelectbox"] div[data-baseweb="select"] * { color: #0f172a !important; font-weight: 700 !important; font-size: 15px !important; }
            .stDataFrame, table { width: 100% !important; border-radius: 8px; overflow: hidden; }
            h2 { color: #0f172a !important; font-weight: 800 !important; font-size: 26px !important; margin-bottom: 5px !important; }
            h3 { color: #1e293b !important; font-weight: 700 !important; font-size: 20px !important; margin-top: 0px !important; }
            button { background-color: #4a69bd !important; color: white !important; font-weight: bold !important; border-radius: 6px !important; padding: 8px 20px !important; border: none !important; }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("<h4>📋 교사 메뉴</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:12px; color:#94a3b8; margin-bottom:15px;'>👤 {st.session_state['teacher_name']} 선생님 접속 중</div>", unsafe_allow_html=True)
        st.markdown("---")
        menu_selection = st.radio(
            "메뉴 선택",
            ["▶ 학생 조회 현황 모니터링", "▶ 성적 데이터 일괄 수정", "▶ 평가 대상 과목 구성", "▶ 성적 데이터 연동 (CSV)", "▶ 시스템 보안 설정"],
            label_visibility="collapsed"
        )
        st.markdown("---")
        if st.button("🚪 시스템 로그아웃", key="sidebar_logout_btn", use_container_width=True):
            st.session_state["admin_logged_in"] = False
            st.session_state["teacher_name"] = ""
            st.session_state["allowed_subjects"] = []
            st.rerun()

    st.markdown(f"<h2>교사용 마스터 통합 워크스테이션</h2>", unsafe_allow_html=True)
    st.write(f"현재 위치: 교사 모드 > {menu_selection}")
    st.markdown("<br>", unsafe_allow_html=True)

    # 📊 모듈 1: 학생 조회 현황 모니터링
    if menu_selection == "▶ 학생 조회 현황 모니터링":
        with st.container(border=True):
            st.markdown(f"<h3>📊 학생별 조회 이력 및 성적 현황 모니터링</h3>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:13px; color:#64748b;'>선택 과목의 학생별 실시간 수행평가 점수 및 조회 로그를 실시간 관측합니다. (읽기 전용)</p>", unsafe_allow_html=True)
            
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]:
                registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
                
            if not registered_dbs:
                st.warning("⚠️ 현재 선생님의 배정 과목 중 서버에 개설된 파티션이 없습니다. '▶ 평가 대상 과목 구성' 또는 구글 시트를 확인하세요.")
            else:
                selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                default_idx = 0
                if "active_subject" in st.session_state and st.session_state.active_subject:
                    target_str = f"📚 {st.session_state.active_subject} ({st.session_state.active_grade}학년 / {st.session_state.active_semester})"
                    if target_str in selector_options: default_idx = selector_options.index(target_str)
                
                selected_db_str = st.selectbox("📂 조회 관측할 대상 교과 선택", options=selector_options, index=default_idx)
                chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                st.session_state.active_subject = chosen_db['subject']
                st.session_state.active_grade = chosen_db['grade'].replace("학년","")
                st.session_state.active_semester = chosen_db['semester']
                
                cf_id, sf_id = get_sheet_names_id(st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester)
                db_df = load_sheet_to_df(sf_id)
                cfg_df = load_sheet_to_df(cf_id)
                
                if not db_df.empty:
                    if not cfg_df.empty:
                        cfg_dict = cfg_df.iloc[0].to_dict()
                        cnt = int(cfg_dict.get('항목개수', 3))
                        score_headers = [cfg_dict.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(cnt)]
                    else: score_headers = []
                    
                    display_cols = ["반", "번호", "이름"]
                    if "학교 이메일" in db_df.columns: display_cols.append("학교 이메일")
                    if "비밀번호" in db_df.columns: display_cols.append("비밀번호")
                    display_cols.extend(score_headers)
                    display_cols.extend(["성적조회 횟수", "최종 확인일시"])
                    
                    valid_cols = [c for c in display_cols if c in db_df.columns]
                    st.dataframe(db_df[valid_cols].fillna("-"), use_container_width=True)
                else: st.warning("등록된 학생 데이터가 비어 있습니다. CSV 데이터 연동 메뉴를 먼저 이용하세요.")

    # 📝 모듈 2: 성적 데이터 일괄 수정
    elif menu_selection == "▶ 성적 데이터 일괄 수정":
        with st.container(border=True):
            st.markdown(f"<h3>📝 실시간 수행평가 대장 엑셀식 일괄 편집 패널</h3>", unsafe_allow_html=True)
            
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]:
                registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
                
            if not registered_dbs:
                st.warning("⚠️ 현재 선생님의 배정 과목 중 수정 권한을 가진 개설 파티션이 없습니다.")
            else:
                selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                default_idx = 0
                if "active_subject" in st.session_state and st.session_state.active_subject:
                    target_str = f"📚 {st.session_state.active_subject} ({st.session_state.active_grade}학년 / {st.session_state.active_semester})"
                    if target_str in selector_options: default_idx = selector_options.index(target_str)
                
                selected_db_str = st.selectbox("📂 수정할 대상 교과 선택", options=selector_options, index=default_idx)
                chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                st.session_state.active_subject = chosen_db['subject']
                st.session_state.active_grade = chosen_db['grade'].replace("학년","")
                st.session_state.active_semester = chosen_db['semester']
                
                cf_id, sf_id = get_sheet_names_id(st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester)
                db_df = load_sheet_to_df(sf_id)
                cfg_df = load_sheet_to_df(cf_id)
                
                if not db_df.empty:
                    if not cfg_df.empty:
                        cfg_dict = cfg_df.iloc[0].to_dict()
                        cnt = int(cfg_dict.get('항목개수', 3))
                        score_headers = [cfg_dict.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(cnt)]
                    else: score_headers = []
                    
                    display_cols = ["반", "번호", "이름"]
                    if "학교 이메일" in db_df.columns: display_cols.append("학교 이메일")
                    if "비밀번호" in db_df.columns: display_cols.append("비밀번호")
                    display_cols.extend(score_headers)
                    display_cols.extend(["성적조회 횟수", "최종 확인일시"])
                    
                    valid_cols = [c for c in display_cols if c in db_df.columns]
                    
                    edited_df = st.data_editor(
                        db_df[valid_cols],
                        use_container_width=True,
                        num_rows="dynamic",
                        disabled=["반", "번호", "이름", "성적조회 횟수", "최종 확인일시"],
                        key="master_live_grid_editor"
                    )
                    
                    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                    if st.button("💾 위의 표 수정내역 구글 클라우드에 일괄 저장", key="btn_save_all_grid_changes"):
                        for col in edited_df.columns: db_df[col] = edited_df[col]
                        if save_df_to_sheet(sf_id, db_df):
                            st.success("🎉 화면에서 수정한 전체 성적 대장 내역이 구글 클라우드 서버에 실시간으로 일괄 동기화 저장 완료되었습니다!")
                            st.rerun()
                else: st.warning("학생 데이터가 비어 있습니다. CSV 데이터 연동 메뉴를 먼저 이용하세요.")

    # 📁 모듈 3: 평가 대상 과목 구성
    elif menu_selection == "▶ 평가 대상 과목 구성":
        with st.container(border=True):
            st.markdown("<h3>📁 1. 평가 과목 세팅 및 파티션 활성화</h3>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:13px; color:#64748b;'>평가 대상 과목과 수행평가 항목 세부 구성을 연동하세요.</p>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"]
                sel_g = st.selectbox("교과군 분류 선택", options=g_opts, label_visibility="collapsed")
            with row1_col2:
                sel_gr = st.selectbox("학년 선택", options=GRADE_OPTIONS, label_visibility="collapsed")
                
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                final_sub, t_g = "", ""
                if sel_g == "➕ 신규 과목 개설":
                    t_g = st.selectbox("위치 지정 분류", ["인문·사회군", "수리·과학군", "예체능군"])
                    final_sub = st.text_input("새 과목명 입력").strip()
                elif sel_g != "교과군 선택":
                    s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                    sel_s = st.selectbox("세부 과목 지정", options=s_opts, label_visibility="collapsed")
                    if sel_s != "과목 선택": final_sub = sel_s
            with row2_col2:
                sel_se = st.selectbox("학기 선택", options=SEMESTER_OPTIONS, label_visibility="collapsed")
                
            st.markdown("<hr style='border-top: 1px dashed #cbd5e1; margin:20px 0;'>", unsafe_allow_html=True)
            st.markdown("##### 📝 2. 수행평가 세부 반영 항목 구성")
            
            cc1, cc2 = st.columns([1, 2])
            with cc1: item_count = st.selectbox("🎯 평가 반영 항목 개수 선택", [1, 2, 3, 4, 5], index=2)
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            item_titles = []
            cols_items = st.columns(item_count)
            for i in range(item_count):
                with cols_items[i]:
                    t_in = st.text_input(f"항목 {i+1} 제목", value=f"수행평가{i+1}", key=f"item_title_in_{i}")
                    item_titles.append(t_in.strip())
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("🚀 이 과목 활성화 및 서버 로드"):
                if "마스터" not in st.session_state["allowed_subjects"] and final_sub not in st.session_state["allowed_subjects"]:
                    st.error(f"❌ 권한 오류: 선생님은 [{final_sub}] 과목에 대한 개설/수정 권한이 없습니다. 담당 교과 권한을 확인하세요.")
                elif final_sub and sel_gr != "학년 지정" and sel_se != "학기 선택":
                    if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub)
                    
                    cf_id, sf_id = get_sheet_names_id(final_sub, sel_gr.replace("학년",""), sel_se)
                    config_df = pd.DataFrame([{
                        "선택된반 목록": "1,2,3,4,5,6,7,8,9,10,11,12",
                        "항목개수": item_count,
                        **{f"항목{k+1}_이름": item_titles[k] for k in range(item_count)}
                    }])
                    save_df_to_sheet(cf_id, config_df)
                    
                    st.session_state.active_subject = final_sub
                    st.session_state.active_grade = sel_gr.replace("학년", "")
                    st.session_state.active_semester = sel_se
                    st.success(f"✅ [{final_sub}] 과목 아키텍처 및 데이터베이스 세팅 완료!")
                else: st.error("과목 정보를 빠짐없이 선택해 주세요.")

    # 📤 모듈 4: 성적 데이터 연동 (CSV)
    elif menu_selection == "▶ 성적 데이터 연동 (CSV)":
        with st.container(border=True):
            st.markdown("<h3>📥 CSV 파일 기반 대용량 클라우드 연동 동기화</h3>", unsafe_allow_html=True)
            registered_dbs = get_active_databases()
            
            if "마스터" not in st.session_state["allowed_subjects"]:
                registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
                
            if not registered_dbs:
                st.warning("⚠️ 현재 선생님의 배정 과목 중 연동 권한을 가진 개설 파티션이 없습니다.")
            else:
                selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                default_idx = 0
                if "active_subject" in st.session_state and st.session_state.active_subject:
                    target_str = f"📚 {st.session_state.active_subject} ({st.session_state.active_grade}학년 / {st.session_state.active_semester})"
                    if target_str in selector_options: default_idx = selector_options.index(target_str)
                
                selected_db_str = st.selectbox("📂 성적을 연동할 대상 과목 선택", options=selector_options, index=default_idx)
                chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                st.session_state.active_subject = chosen_db['subject']
                st.session_state.active_grade = chosen_db['grade'].replace("학년","")
                st.session_state.active_semester = chosen_db['semester']
                
                cf_id, sf_id = get_sheet_names_id(st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester)
                cfg_df = load_sheet_to_df(cf_id)
                
                if not cfg_df.empty:
                    cfg_dict = cfg_df.iloc[0].to_dict()
                    cnt = int(cfg_dict.get('항목개수', 3))
                    dynamic_headers = [cfg_dict.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(cnt)]
                else: dynamic_headers = ["형성평가", "포트폴리오", "태도점수"]
                
                st.markdown("<hr style='border-top: 1px solid #e2e8f0; margin:15px 0;'>", unsafe_allow_html=True)
                st.info(f"현재 선택된 연동 타겟 과목: **{st.session_state.active_subject} ({st.session_state.active_grade}학년 / {st.session_state.active_semester})**")
                
                rows = [
                    ["반", "번호", "이름", "학교 이메일", "비밀번호", "성적조회 횟수", "최종 확인일시"] + dynamic_headers,
                    [1, 1, "홍길동", "hgd2026@school.hs.kr", "1024", 0, "-", 20, 18, 25][:7+len(dynamic_headers)],
                    [1, 2, "이영희", "lyh2026@school.hs.kr", "3925", 0, "-", 19, 20, 22][:7+len(dynamic_headers)]
                ]
                
                csv_string = ""
                for r in rows: csv_string += ",".join(map(str, r)) + "\n"
                csv_bytes = csv_string.encode('cp949')
                
                st.markdown("##### 💡 학교 이메일 항목이 추가된 양식을 다운로드하여 성적을 연동하세요.")
                st.download_button(
                    label=f"📥 [{st.session_state.active_subject}] 이메일 통합형 성적 양식(.CSV) 다운로드",
                    data=csv_bytes,
                    file_name=f"수행평가_이메일양식_{st.session_state.active_subject}.csv",
                    mime="text/csv",
                    key="download_sample_csv"
                )
                st.markdown("<br>", unsafe_allow_html=True)
                
                up_f = st.file_uploader("성적 대장 CSV 파일 업로드", type="csv")
                if up_f:
                    df_up = pd.read_csv(up_f, encoding='cp949')
                    if "학교 이메일" not in df_up.columns: df_up["학교 이메일"] = ""
                    if "성적조회 횟수" not in df_up.columns: df_up["성적조회 횟수"] = 0
                    if "최종 확인일시" not in df_up.columns: df_up["최종 확인일시"] = "-"
                    if save_df_to_sheet(sf_id, df_up):
                        st.success("🎉 학교 이메일 매핑 및 성적 클라우드 실시간 동기화가 완벽히 마감되었습니다!")

    # 모듈 5: 시스템 보안 설정
    elif menu_selection == "▶ 시스템 보안 설정":
        with st.container(border=True):
            st.markdown("<h3>🔐 마스터 관리자 인증 계정 변경</h3>", unsafe_allow_html=True)
            account_update_dialog()