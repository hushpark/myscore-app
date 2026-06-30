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

# 🚨 [레이아웃 원상복구] 최상단 배치 규칙 엄수 - 순정 와이드 레이아웃 및 타이틀 고정
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="wide")

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

def verify_teacher_credentials(input_id, input_pw):
    df = load_sheet_to_df("teacher_accounts", ["교사_ID", "비밀번호", "교사_성명", "담당_과목"])
    if not df.empty:
        df['교사_ID'] = df['교사_ID'].astype(str).str.strip()
        df['비밀번호'] = df['비밀번호'].astype(str).str.strip()
        
        match = df[(df['교사_ID'] == str(input_id).strip()) & (df['비밀번호'] == str(input_pw).strip())]
        if not match.empty:
            row = match.iloc[0]
            return {
                "success": True,
                "teacher_id": str(row['교사_ID']).strip(),
                "teacher_name": str(row['교사_성명']).strip(),
                "authorized_subjects": [s.strip() for s in str(row['담당_과목']).split(",") if s.strip()]
            }
            
    if input_id.strip() == "admin" and input_pw.strip() == "1234":
        return {"success": True, "teacher_id": "admin", "teacher_name": "최고관리자", "authorized_subjects": ["마스터"]}
    return {"success": False, "teacher_name": "", "authorized_subjects": []}

def get_sheet_names_id(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    safe_semester = semester_str.replace(" ", "_").replace("/", "_")
    return f"cfg_{safe_subject}_{grade}Grade", f"st_{safe_subject}_{grade}_{semester_str}"

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

@st.dialog("🔐 내 정보 수정")
def account_update_dialog():
    teacher_id_target = st.session_state.get("logged_teacher_id", "")
    teacher_name_target = st.session_state.get("teacher_name", "교사")
    
    st.markdown(f"##### 👤 **{teacher_name_target}** 선생님의 보안 정보 수정")
    df_teachers = load_sheet_to_df("teacher_accounts", ["교사_ID", "비밀번호", "교사_성명", "담당_과목"])
    
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
            if st.button("💾 변경사항 클라우드 시트에 즉시 반영", use_container_width=True, type="primary"):
                if new_pw and new_sub:
                    df_teachers.loc[idx, "비밀번호"] = new_pw.strip()
                    df_teachers.loc[idx, "담당_과목"] = new_sub.strip()
                    if save_df_to_sheet("teacher_accounts", df_teachers):
                        st.session_state["allowed_subjects"] = [s.strip() for s in new_sub.split(",") if s.strip()]
                        st.session_state["show_update_success_msg"] = True 
                        st.rerun()
                else: st.error("빈 칸을 남겨둘 수 없습니다.")
        else: st.error("계정 매핑 인덱스를 찾을 수 없습니다. 로그아웃 후 다시 시도해 주세요.")
    else:
        st.warning("최고관리자(admin) 계정은 마스터 권한 고정이므로 시트 수정이 필요 없습니다.")

@st.dialog("➕ 학생 개별 추가")
def student_individual_add_dialog(db_df, sf_id, score_headers):
    st.markdown("##### 📝 신규 누락 학생 1명 개별 등록")
    st.write("아래 인적사항을 입력하시면 현재 성적부 하단에 즉시 추가됩니다.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    ac1, ac2 = st.columns(2)
    with ac1: add_b = st.number_input("반", min_value=1, max_value=30, value=1)
    with ac2: add_n = st.number_input("번호", min_value=1, max_value=60, value=1)
    
    add_name = st.text_input("학생 이름", placeholder="성명 입력")
    add_email = st.text_input("학교 이메일", placeholder="아이디@도메인.hs.kr")
    add_pw = st.text_input("개인 비밀번호", placeholder="학생 전용 조회 암호")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 학생 추가 등록", use_container_width=True, type="primary"):
        if add_name and add_email and add_pw:
            new_student_row = {
                "반": int(add_b), "번호": int(add_n), "이름": str(add_name).strip(),
                "school_email": str(add_email).strip(), "비밀번호": str(add_pw).strip(),
                "성적조회 횟수": 0, "최종 확인일시": "-"
            }
            for h in score_headers: new_student_row[h] = 0
            
            updated_master_df = pd.concat([db_df, pd.DataFrame([new_student_row])], ignore_index=True)
            if save_df_to_sheet(sf_id, updated_master_df):
                st.success(f"✅ [{add_b}반 {add_n}번 {add_name}] 학생이 클라우드 성적 대장에 안전하게 추가 등록 완료되었습니다!")
                st.rerun()
        else:
            st.error("학생의 이름, 이메일, 비밀번호를 빠짐없이 채워주세요.")

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
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = ""
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = ""
if "allowed_subjects" not in st.session_state: st.session_state["allowed_subjects"] = []

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 지정", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]

# =========================================================================
# 🔄 전역 테마 스타일 개조 부 (본문 축소 및 사이드바 가로 폭 축소 인프라)
# =========================================================================
st.markdown("""
    <style>
        /* 우측 본문 전체 배경색 연회색 고정 */
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { 
            background-color: #f1f5f9 !important; 
        }
        div[data-testid="stHeader"] { display: none !important; }
        
        /* 사이드바 자체 가로 폭 너비를 깔끔하고 날씬하게 강제 리사이징 축소 조치 */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] {
            min-width: 260px !important;
            max-width: 260px !important;
            background-color: #1e293b !important;
            box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important;
        }
        [data-testid="stAppViewContainer"] {
            margin-left: 0px !important;
        }

        /* 사이드바 기본 텍스트 테마 고정 */
        [data-testid="stSidebar"] h4 { color: #ffffff !important; font-weight: 800; font-size: 24px !important; margin-top: 10px !important; }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 700 !important; font-size: 16px !important; }
        div[data-testid="stSidebar"] div[role="radiogroup"] label p { color: #f8fafc !important; font-weight: 700 !important; font-size: 16px !important; }

        /* 과목 구성 설정 컴팩트 다운사이징 (높이 축소) */
        div.stVBlock > div { gap: 0.4rem !important; }
        .stElementContainer { margin-bottom: 0.3rem !important; }
        div[data-testid="stBlock"] { padding: 0.6rem 1rem !important; }

        /* 셀렉트박스 공통 테두리 스타일 */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] { border: 2px solid #4a69bd !important; border-radius: 8px !important; background-color: #ffffff !important; }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] * { color: #0f172a !important; font-weight: 700 !important; font-size: 15px !important; }
        .stDataFrame, table { width: 100% !important; border-radius: 8px; overflow: hidden; }
        
        h2 { color: #0f172a !important; font-weight: 800 !important; font-size: 26px !important; margin-bottom: 3px !important; margin-top: 0px !important; }
        h3 { color: #1e293b !important; font-weight: 700 !important; font-size: 20px !important; margin-top: 0px !important; margin-bottom: 5px !important; }
        
        /* 수행평가 항목 입력 텍스트 박스 테두리 상시 활성화 */
        div[data-testid="stTextInput"] div[data-baseweb="input"], div[data-testid="stNumberInput"] div[data-baseweb="input"] {
            border: 2px solid #cbd5e1 !important;
            border-radius: 6px !important;
            background-color: #ffffff !important;
        }

        /* 로그인 화면 폼 내부 전용 버튼 스타일 지정 */
        div[data-testid="stForm"] button[data-testid="baseButton-secondary"] {
            background-color: #4a69bd !important;
            color: #ffffff !important;
            font-weight: bold !important;
            border: none !important;
            width: 100% !important;
            padding: 0.6rem 0 !important;
            border-radius: 8px !important;
            font-size: 16px !important;
            box-shadow: 0 4px 10px rgba(74, 105, 189, 0.2) !important;
        }
        
        div.stButton > button[key="btn_save_all_grid_changes"] { background-color: #3b82f6 !important; color: white !important; font-weight: bold !important; border: none !important; }
        div.stButton > button[key="btn_trigger_student_dialog"] { background-color: #10b981 !important; color: white !important; font-weight: bold !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# 세션 팅김 방지용 역방향 온클릭 리스너 분기 매핑
def sidebar_logout_callback():
    st.session_state["admin_logged_in"] = False
    st.session_state["logged_teacher_id"] = ""
    st.session_state["teacher_name"] = ""
    st.session_state["allowed_subjects"] = []

if "open_profile_popup" not in st.session_state:
    st.session_state["open_profile_popup"] = False

if st.session_state["open_profile_popup"]:
    st.session_state["open_profile_popup"] = False
    account_update_dialog()

if not st.session_state["admin_logged_in"]:
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
        </style>
    """, unsafe_allow_html=True)
    
    with st.form("master_unified_form"):
        st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        login_mode = st.radio("접속 모드", ["교사", "학생"], horizontal=True, label_visibility="collapsed")
        st.markdown("<h4 style='height: 10px; border:none;'></h4>", unsafe_allow_html=True)
        
        if login_mode == "교사":
            admin_id = st.text_input("교사_ID", placeholder="교사 ID를 입력하세요", label_visibility="collapsed", key="ti_id")
            admin_pw = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed", key="ti_pw")
            if st.form_submit_button("로그인"):
                auth_result = verify_teacher_credentials(admin_id, admin_pw)
                if auth_result["success"]:
                    st.session_state["admin_logged_in"] = True
                    st.session_state["logged_teacher_id"] = auth_result["teacher_id"]
                    st.session_state["teacher_name"] = auth_result["teacher_name"]
                    st.session_state["allowed_subjects"] = auth_result["authorized_subjects"]
                    st.rerun()
                else: st.error("❌ ID 또는 비밀번호 오류")

        elif login_mode == "학생":
            active_dbs = get_active_databases()
            if not active_dbs: st.warning("등록된 데이터가 없습니다.")
            else:
                opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in active_dbs]
                sel_s = st.selectbox("과목", opts_s, label_visibility="collapsed", key="sb_sub")
                if sel_s != "과목 및 학기를 선택하세요.":
                    db = active_dbs[opts_s.index(sel_s)-1]
                    cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                    config = load_sheet_to_df(cf_id).iloc[0].to_dict() if not load_sheet_to_df(cf_id).empty else None
                    if config:
                        st.markdown("<h4 style='height: 5px; border:none;'></h4>", unsafe_allow_html=True)
                        st_email_in = st.text_input("학교 이메일", placeholder="학교 이메일을 입력하세요", label_visibility="collapsed", key="ti_st_email")
                        st_pw = st.text_input("비밀번호", type="password", placeholder="개인 암호 입력", label_visibility="collapsed", key="ti_st_pw")
                        
                        if st.form_submit_button("점수 조회"):
                            df_st = load_sheet_to_df(sf_id)
                            if not df_st.empty:
                                if "school_email" in df_st.columns:
                                    res = df_st[(df_st['school_email'].astype(str).str.strip() == str(st_email_in).strip()) & (df_st['비밀번호'].astype(str) == str(st_pw))]
                                else:
                                    res = df_st[(df_st['이름'].astype(str).str.strip() == str(st_email_in).strip()) & (df_st['비밀번호'].astype(str) == str(st_pw))]
                                    
                                if not res.empty:
                                    idx = res.index[0]
                                    st_name = res.iloc[0].get('이름', '학생')
                                    scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                                    show_result_dialog(st_name, scores, sf_id, idx, df_st)
                                else: st.error("❌ 정보가 일치하지 않습니다. 입력값을 다시 확인해 주세요.")
        st.markdown("<div style='text-align:center; font-size:11px; color:#94a3b8; margin-top:30px;'>Designed & Developed by User & AI Creator</div>", unsafe_allow_html=True)

else:
    with st.sidebar:
        # 🚨 [하드웨어 ID 타겟 고정 패치] 버튼 인스턴스 ID 규칙을 완전 격리하여 마스킹 오염 완전 무력화
        st.markdown("""
            <style>
                div[data-testid="stSidebar"] button[id*="account_pure_btn"],
                div[data-testid="stSidebar"] button[id*="logout_pure_btn"],
                div[data-testid="stSidebar"] button {
                    background-color: #2b3a4a !important;
                    color: #ffffff !important;
                    border: 2px solid #3f5164 !important;
                    border-radius: 6px !important;
                    padding: 10px 16px !important;
                    font-weight: 700 !important;
                    font-size: 14px !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                    width: 100% !important;
                    display: block !important;
                    text-align: center !important;
                }
                
                div[data-testid="stSidebar"] button[id*="account_pure_btn"]:hover,
                div[data-testid="stSidebar"] button[id*="logout_pure_btn"]:hover,
                div[data-testid="stSidebar"] button:hover {
                    background-color: #3f5164 !important;
                    border-color: #52667a !important;
                    color: #ffffff !important;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("<h4>📋 교사 메뉴</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:12px; color:#94a3b8; margin-bottom:15px;'>👤 {st.session_state['teacher_name']} 선생님 접속 중</div>", unsafe_allow_html=True)
        st.markdown("---")
        menu_selection = st.radio(
            "메뉴 선택",
            ["▶ 학생 조회 현황 모니터링", "▶ 개인별 성적 입력", "▶ 평가 대상 과목 구성", "▶ 성적 전체 일괄 업로드(CSV)"],
            label_visibility="collapsed"
        )
        st.markdown("---")
        
        # 순정 UI를 유지하면서 튕김을 막는 콜백 리스너 연동형 버튼 기동
        if st.button("🔐 내 정보 수정", key="account_pure_btn", use_container_width=True):
            st.session_state["open_profile_popup"] = True
            st.rerun()
            
        st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)
        st.button("🚪 시스템 로그아웃", key="logout_pure_btn", use_container_width=True, on_click=sidebar_logout_callback)

    # 교사 대시보드 타이틀 고정
    st.markdown(f"<h2>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
    st.write(f"현재 위치: 교사 모드 > {menu_selection}")
    st.markdown("<div style='text-align:center; height: 5px;'></div>", unsafe_allow_html=True)

    # 다이얼로그 내부가 아닌, 안전하게 격리된 본문 프레임에 성공 메시지를 뿜어 오염 방지
    if "show_update_success_msg" in st.session_state and st.session_state["show_update_success_msg"]:
        del st.session_state["show_update_success_msg"]
        st.success("🎉 교사 정보 및 과목 권한이 데이터베이스에 실시간으로 일괄 동기화 완료되었습니다!")

    # 📊 모듈 1: 학생 조회 현황 모니터링
    if menu_selection == "▶ 학생 조회 현황 모니터링":
        with st.container(border=True):
            st.markdown(f"<h3>📊 학생별 조회 이력 및 성적 현황 모니터링</h3>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:13px; color:#64748b; margin-bottom: 5px;'>과목과 반을 선택하여 학생들의 실시간 조회 상태 및 점수를 모니터링합니다. (읽기 전용)</p>", unsafe_allow_html=True)
            
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]:
                registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
                
            if not registered_dbs:
                st.warning("⚠️ 현재 선생님의 배정 과목 중 서버에 개설된 파티션이 없습니다.")
            else:
                col_sub, col_class = st.columns(2)
                with col_sub:
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
                
                with col_class:
                    class_options = ["전체 학급 보기"]
                    if not db_df.empty and "반" in db_df.columns:
                        try:
                            class_options = ["전체 학급 보기"] + [f"{int(x)}반" for x in sorted(db_df['반'].unique())]
                        except:
                            class_options = ["전체 학급 보기"] + [f"{x}반" for x in sorted(db_df['반'].unique())]
                    selected_class = st.selectbox("🎯 필터링할 학급(반) 선택", options=class_options, key="sb_filter_class_monitor")
                
                if not db_df.empty:
                    render_df = db_df.copy()
                    if selected_class != "전체 학급 보기":
                        render_df = render_df[render_df['반'].astype(int) == int(selected_class.replace("반",""))]
                        
                    if not cfg_df.empty:
                        cfg_dict = cfg_df.iloc[0].to_dict()
                        cnt = int(cfg_dict.get('항목개수', 3))
                        score_headers = [cfg_dict.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(cnt)]
                    else: score_headers = []
                    
                    display_cols = ["반", "번호", "이름"]
                    if "school_email" in render_df.columns: display_cols.append("school_email")
                    if "비밀번호" in render_df.columns: display_cols.append("비밀번호")
                    display_cols.extend(score_headers)
                    display_cols.extend(["성적조회 횟수", "최종 확인일시"])
                    
                    valid_cols = [c for c in display_cols if c in render_df.columns]
                    st.dataframe(render_df[valid_cols].fillna("-"), use_container_width=True, hide_index=True)
                else: st.warning("등록된 데이터가 없습니다. 성적 전체 일괄 업로드 메뉴를 이용하세요.")

    # 📝 모듈 2: 개인별 성적 입력
    elif menu_selection == "▶ 개인별 성적 입력":
        with st.container(border=True):
            st.markdown(f"<h3>📝 개인별 성적 데이터 편집</h3>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:13px; color:#64748b;'>학급별 필터링을 통해 시트 내부 셀을 엑셀처럼 더블클릭하여 바로 수정하실 수 있습니다.</p>", unsafe_allow_html=True)
            
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]:
                registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
                
            if not registered_dbs:
                st.warning("⚠️ 현재 선생님의 배정 과목 중 수정 권한을 가진 개설 파티션이 없습니다.")
            else:
                col_sub_ed, col_class_ed = st.columns(2)
                with col_sub_ed:
                    selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                    selected_db_str = st.selectbox("📂 관리할 교과 선택", options=selector_options)
                    chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                    st.session_state.active_subject = chosen_db['subject']
                    st.session_state.active_grade = chosen_db['grade'].replace("학년","")
                    st.session_state.active_semester = chosen_db['semester']
                
                cf_id, sf_id = get_sheet_names_id(st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester)
                db_df = load_sheet_to_df(sf_id)
                cfg_df = load_sheet_to_df(cf_id)
                
                with col_class_ed:
                    class_options_ed = ["전체"]
                    if not db_df.empty and "반" in db_df.columns:
                        class_options_ed = ["전체"] + [f"{x}반" for x in sorted(db_df['반'].unique())]
                    selected_class_ed = st.selectbox("👥 수정할 대상 학반 필터링", options=class_options_ed, key="sb_filter_class_editor")
                
                if not db_df.empty:
                    if not cfg_df.empty:
                        cfg_dict = cfg_df.iloc[0].to_dict()
                        cnt = int(cfg_dict.get('항목개수', 3))
                        score_headers = [cfg_dict.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(cnt)]
                    else: score_headers = []
                    
                    display_cols = ["반", "번호", "이름"]
                    if "school_email" in db_df.columns: display_cols.append("school_email")
                    if "비밀번호" in db_df.columns: display_cols.append("비밀번호")
                    display_cols.extend(score_headers)
                    display_cols.extend(["성적조회 횟수", "최종 확인일시"])
                    
                    valid_cols = [c for c in display_cols if c in db_df.columns]
                    
                    if selected_class_ed != "전체":
                        target_class_num_ed = int(selected_class_ed.replace("반", ""))
                        filtered_idx = db_df[db_df["반"].astype(int) == target_class_num_ed].index
                        edit_target_df = db_df.loc[filtered_idx, valid_cols]
                    else:
                        filtered_idx = db_df.index
                        edit_target_df = db_df[valid_cols]
                    
                    edited_df = st.data_editor(
                        edit_target_df, use_container_width=True, num_rows="dynamic",
                        disabled=["반", "번호", "이름", "성적조회 횟수", "최종 확인일시"],
                        key="master_live_grid_editor", hide_index=True
                    )
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_col3, btn_col1, btn_col2 = st.columns([4.2, 0.9, 0.9])
                    
                    with btn_col3:
                        st.write("")
                    with btn_col1:
                        if st.button("➕ 학생 개별 추가", key="btn_trigger_student_dialog", use_container_width=True):
                            student_individual_add_dialog(db_df, sf_id, score_headers)
                    with btn_col2:
                        if st.button("💾 수정 사항 저장", key="btn_save_all_grid_changes", use_container_width=True):
                            for idx_pos, row_idx in enumerate(filtered_idx):
                                for col in edited_df.columns:
                                    db_df.loc[row_idx, col] = edited_df.iloc[idx_pos][col]
                            if save_df_to_sheet(sf_id, db_df):
                                st.success("🎉 수행평가 성적 수정 사항이 성공적으로 클라우드 서버와 일괄 저장 동기화되었습니다!")
                                st.rerun()
                else: st.warning("현재 업로드된 성적 대장이 비어 있습니다. 아래 성적 전체 일괄 업로드 메뉴를 이용하세요.")

    # 📁 모듈 3: 평가 대상 과목 구성
    elif menu_selection == "▶ 평가 대상 과목 구성":
        with st.container(border=True):
            st.markdown("<h3>⚙️ 1. 평가 과목 설정</h3>", unsafe_allow_html=True)
            
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"]
                sel_g = st.selectbox("교과군 분류 선택", options=g_opts, label_visibility="collapsed")
            with row1_col2:
                sel_gr = st.selectbox("학년 선택", options=GRADE_OPTIONS, label_visibility="collapsed")
                
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
                
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown("<h3>🎯 2. 수행평가 항목 구성</h3>", unsafe_allow_html=True)
            
            ic_col, _ = st.columns([1, 2])
            with ic_col: item_count = st.selectbox("🎯 평가 반영 항목 개수 선택", [1, 2, 3, 4, 5], index=2)
            
            item_titles = []
            cols_items = st.columns(item_count)
            for i in range(item_count):
                with cols_items[i]:
                    t_in = st.text_input(f"항목 {i+1} 제목", placeholder="수행평가 항목 입력", key=f"item_title_in_{i}", label_visibility="collapsed")
                    item_titles.append(t_in.strip())
            
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            
            col_space, col_btn = st.columns([4.8, 1.2])
            with col_space: st.write("")
            with col_btn:
                if st.button("기본 설정 저장", type="primary", use_container_width=True, key="btn_save_evaluation_config"):
                    if final_sub and sel_gr != "학년 지정" and sel_se != "학기 선택":
                        if "마스터" not in st.session_state["allowed_subjects"] and final_sub not in st.session_state["allowed_subjects"]:
                            st.error(f"❌ 권한 오류: 선생님은 [{final_sub}] 과목에 대한 권한이 없습니다.")
                        else:
                            if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub)
                            cf_id, sf_id = get_sheet_names_id(final_sub, sel_gr.replace("학년",""), sel_se)
                            config_df = pd.DataFrame([{
                                "선택된반 목록": "1,2,3,4,5,6,7,8,9,10,11,12",
                                "항목개수": item_count,
                                **{f"항목{k+1}_이름": item_titles[k] for k in range(item_count)}
                            }])
                            save_df_to_sheet(cf_id, config_df)
                            st.success(f"✅ 기본 설정이 안전하게 저장 완료되었습니다!")
                    else: st.error("과목 정보를 빠짐없이 선택해 주세요.")

    # 📤 모듈 4: 성적 전체 일괄 업로드(CSV)
    elif menu_selection == "▶ 성적 전체 일괄 업로드(CSV)":
        with st.container(border=True):
            st.markdown("<h3>📥 전체 일괄 성적 입력</h3>", unsafe_allow_html=True)
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
                
                selected_db_str = st.selectbox("📂 성적 연동 과목 선택", options=selector_options, index=default_idx)
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
                st.info(f"현재 선택된 연동 과목: **{st.session_state.active_subject} ({st.session_state.active_grade}학년 / {st.session_state.active_semester})**")
                
                rows = [
                    ["반", "번호", "이름", "school_email", "비밀번호", "성적조회 횟수", "최종 확인일시"] + dynamic_headers,
                    [1, 1, "홍길동", "hgd2026@school.hs.kr", "1024", 0, "-", 20, 18, 25][:7+len(dynamic_headers)]
                ]
                
                csv_string = ""
                for r in rows: csv_string += ",".join(map(str, r)) + "\n"
                csv_bytes = csv_string.encode('cp949')
                
                st.markdown("##### 💡 양식을 다운로드하여 성적을 업로드하세요.")
                st.download_button(
                    label=f"📥 [{st.session_state.active_subject}] 일괄 업로드용 성적 양식(.CSV) 다운로드",
                    data=csv_bytes,
                    file_name=f"수행평가_양식_{st.session_state.active_subject}.csv",
                    mime="text/csv",
                    key="download_sample_csv"
                )
                st.markdown("<br>", unsafe_allow_html=True)
                
                up_f = st.file_uploader("성적 파일 CSV파일 업로드", type="csv")
                if up_f:
                    df_up = pd.read_csv(up_f, encoding='cp949')
                    if "school_email" not in df_up.columns: df_up["school_email"] = ""
                    if "성적조회 횟수" not in df_up.columns: df_up["성적조회 횟수"] = 0
                    if "최종 확인일시" not in df_up.columns: df_up["최종 확인일시"] = "-"
                    if save_df_to_sheet(sf_id, df_up):
                        st.success("🎉 구글 스프레드시트 클라우드 서버와 실시간 일괄 동기화 마감 완료!")