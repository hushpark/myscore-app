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

# =========================================================================
# 🔐 [구글 시트 API 연동 설정] secrets.toml 기반 안전 접속 엔진
# =========================================================================
@st.cache_resource
def init_google_sheet_client():
    try:
        credentials_info = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes) [cite: 1, 2]
        return gspread.authorize(creds) [cite: 2]
    except Exception as e:
        return None [cite: 2]

gc = init_google_sheet_client() [cite: 2]
SPREADSHEET_NAME = "수행평가_데이터베이스"  # 👈 구글 드라이브 파일명 [cite: 2]

def get_google_sheet(sheet_name):
    if gc is None: return None [cite: 2]
    try:
        sh = gc.open(SPREADSHEET_NAME) [cite: 2]
        try:
            return sh.worksheet(sheet_name) [cite: 2]
        except gspread.exceptions.WorksheetNotFound:
            return sh.add_worksheet(title=sheet_name, rows="1000", cols="30") [cite: 2, 3]
    except:
        return None [cite: 3]

def load_sheet_to_df(sheet_name, default_cols=None):
    wks = get_google_sheet(sheet_name) [cite: 3]
    if wks is None: return pd.DataFrame(columns=default_cols if default_cols else []) [cite: 3]
    try:
        records = wks.get_all_records() [cite: 3]
        if not records: return pd.DataFrame(columns=default_cols if default_cols else []) [cite: 3]
        return pd.DataFrame(records) [cite: 3]
    except:
        return pd.DataFrame(columns=default_cols if default_cols else []) [cite: 3, 4]

def save_df_to_sheet(sheet_name, df):
    wks = get_google_sheet(sheet_name) [cite: 4]
    if wks is None: return False [cite: 4]
    try:
        wks.clear() [cite: 4]
        df_filled = df.fillna("").astype(str) [cite: 4]
        wks.update([df_filled.columns.values.tolist()] + df_filled.values.tolist()) [cite: 4]
        return True [cite: 4]
    except:
        return False [cite: 4]

# ⚡ [회색 화면 해결의 핵심]: 글자 타이핑할 때마다 구글 서버를 무한 조회하여 렉 유발하던 원인을 원천 차단!
@st.cache_data(ttl=30)
def get_active_databases():
    active_list = [] [cite: 42]
    if gc is None: return active_list [cite: 42, 43]
    try:
        sh = gc.open(SPREADSHEET_NAME) [cite: 43]
        for wks in sh.worksheets(): [cite: 43]
            name = wks.title [cite: 43]
            if name.startswith("cfg_"): [cite: 43]
                core_name = name.replace("cfg_", "") [cite: 43]
                match = re.search(r"(.+?)_(1|2|3)_(.+)", core_name) [cite: 43]
                if match: [cite: 44]
                    sub_name = match.group(1).replace("_", " ") [cite: 44]
                    grd_name = f"{match.group(2)}학년" [cite: 44]
                    sem_name = match.group(3).replace("_", " ") [cite: 44]
                    active_list.append({"subject": sub_name, "grade": grd_name, "semester": sem_name}) [cite: 45]
    except: pass [cite: 45]
    return active_list [cite: 45]

def remove_subject_completely_from_disk(sub_name):
    df_m = load_sheet_to_df("master_subjects", ["교과군", "과목명"]) [cite: 45]
    if not df_m.empty: [cite: 45]
        df_m = df_m[df_m["과목명"] != sub_name] [cite: 45]
        save_df_to_sheet("master_subjects", df_m) [cite: 45]
    if gc is None: return [cite: 45]
    try:
        sh = gc.open(SPREADSHEET_NAME) [cite: 45]
        safe_sub = sub_name.replace(" ", "_") [cite: 45]
        for wks in sh.worksheets(): [cite: 45]
            if safe_sub in wks.title and (wks.title.startswith("cfg_") or wks.title.startswith("st_")): [cite: 46]
                sh.del_worksheet(wks) [cite: 46]
    except: pass [cite: 46]

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict):
    st.markdown(f"<div style='margin-bottom:15px;'><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True) [cite: 46]
    st.table(pd.DataFrame(scores_dict)) [cite: 46]
    if st.button("확인 후 닫기", use_container_width=True, type="primary"): [cite: 46]
        st.session_state.clear() [cite: 46]
        st.rerun() [cite: 46]

@st.dialog("🔐 관리자 암호 수정")
def password_update_dialog():
    st.markdown("<div style='padding: 5px;'></div>", unsafe_allow_html=True) [cite: 46]
    new_pw = st.text_input("새 암호 입력", type="password", key="dialog_new_pw") [cite: 46, 47]
    confirm_pw = st.text_input("2. 새 암호 확인", type="password", key="dialog_confirm_pw") [cite: 47]
    is_valid, msg = is_strong_password(new_pw) [cite: 47]
    if new_pw: [cite: 47]
        if new_pw == confirm_pw and is_valid: [cite: 47]
            st.markdown("<div style='background-color:#E8F5E9; border-radius:4px; padding:10px; color:#2E7D32; font-weight:500; margin-bottom:10px;'>✅ 두 암호가 완벽하게 일치합니다.</div>", unsafe_allow_html=True) [cite: 47]
        elif confirm_pw and new_pw != confirm_pw: [cite: 47]
            st.error("❌ 암호 확인 칸이 일치하지 않습니다.") [cite: 47]
        else: [cite: 48]
            st.warning(msg) [cite: 48]
    st.markdown("""<div style="font-size: 13px; color: #57606a; line-height: 1.6; background: #f8f9fa; padding: 15px; border-radius: 8px;">
    <b>[안전 암호 규칙]</b><br>- 최소 12자 이상 필수<br>- 영문 + 숫자 + 특수기호 조합
    </div>""", unsafe_allow_html=True) [cite: 48]
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True) [cite: 48]
    can_submit = is_valid and (new_pw == confirm_pw) [cite: 48]
    b_col1, b_col2 = st.columns(2) [cite: 48]
    with b_col1: [cite: 48]
        if st.button("저장 후 적용", disabled=not can_submit, use_container_width=True, type="primary"): [cite: 48]
            save_admin_password(new_pw); st.toast("🎉 암호가 변경되었습니다!"); st.rerun() [cite: 49]
    with b_col2: [cite: 49]
        if st.button("수정 취소", use_container_width=True): st.rerun() [cite: 49]

def reset_all_data():
    st.cache_resource.clear() [cite: 4]
    st.cache_data.clear()
    keep_keys = {
        "page_status": st.session_state.get("page_status", "teacher_main"), [cite: 4]
        "admin_logged_in": st.session_state.get("admin_logged_in", True), [cite: 5]
        "sel_group_idx": st.session_state.get("sel_group_idx", 0), [cite: 5]
        "sel_sub_idx": st.session_state.get("sel_sub_idx", 0), [cite: 5]
        "sel_grade_idx": st.session_state.get("sel_grade_idx", 0), [cite: 5]
        "sel_semester_idx": st.session_state.get("sel_semester_idx", 0), [cite: 5]
        "active_subject": st.session_state.get("active_subject", None), [cite: 5]
        "active_grade": st.session_state.get("active_grade", None), [cite: 5]
        "active_semester": st.session_state.get("active_semester", None) [cite: 5]
    }
    st.session_state.clear() [cite: 5]
    for k, v in keep_keys.items(): [cite: 5]
        st.session_state[k] = v [cite: 5]
    st.session_state["saved_items_count"] = 0 [cite: 6]
    st.session_state["just_saved_success"] = False [cite: 6]
    st.success("🎉 현재 구역의 입력 데이터가 깨끗하게 초기화되었습니다!") [cite: 6]
    st.rerun() [cite: 6]

# --- 🎯 layout 설정을 centered로 고정하여 기본 프레임 최적화 ---
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="centered") [cite: 6]

# =========================================================================
# 🎯 [CSS 최종 완결판] 데이터 삭제 버튼 단독 레드 조준 및 내부 탭 스타일링
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; } [cite: 6, 7]
        div[data-testid="stHeader"] { display: none !important; background: transparent !important; } [cite: 7, 8]
        footer { display: none !important; } [cite: 8, 9]
        .block-container { padding-top: 2.5rem !important; padding-bottom: 0.5rem !important; } [cite: 9, 10]
        
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #e2e8f0 !important; [cite: 10]
            padding: 20px 25px 30px 25px !important; [cite: 11]
            border-radius: 12px !important; [cite: 11]
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; [cite: 11]
            background-color: #ffffff !important; [cite: 12]
            max-width: 1450px !important; [cite: 12]
            margin: 0px auto !important; [cite: 12]
        } [cite: 13]
        div[data-testid="stForm"] { border: none !important; padding: 0px !important; box-shadow: none !important; } [cite: 13]
        background-color: transparent !important; } [cite: 14]
        h2 { font-size: 22px !important; color: #0f172a !important; } [cite: 14]
        font-weight: 800 !important; margin: 5px 0 10px 0 !important; white-space: nowrap !important; text-align: center; [cite: 15]
        } [cite: 16]
        h4 { font-size: 14px !important; font-weight: 700 !important; color: #475569 !important; } [cite: 16]
        margin-top: 0px !important; margin-bottom: 2px !important; white-space: nowrap !important; } [cite: 17]
        
        div.stButton > button[key="outer_teacher_btn"],
        div.stButton > button[key="outer_student_btn"],
        div.stButton > button[key="outer_logout_btn"],
        div.stButton > button[key="outer_pw_btn"] {
            width: fit-content !important; [cite: 17]
            min-width: auto !important; padding: 3px 12px !important; font-size: 12px !important; border-radius: 6px !important; border: 1px solid #cbd5e1 !important; [cite: 18]
            color: #475569 !important; background-color: #ffffff !important; white-space: nowrap !important; [cite: 19]
        }
        div[data-testid="stHorizontalBlock"] div.stButton button { white-space: nowrap !important; } [cite: 19]
        word-break: keep-all !important; } [cite: 20]
        div[data-testid="stVerticalBlock"] > div:has(div.stButton), div[data-testid="stVerticalBlock"] > div:has(div.stSelectbox) { padding-bottom: 0px !important; } [cite: 20]
        margin-bottom: -4px !important; } [cite: 21]
        div.stButton button { margin: 0px auto !important; } [cite: 21]
        padding-top: 5px !important; padding-bottom: 5px !important; transition: all 0.15s ease-in-out !important; [cite: 22]
        } [cite: 23]
        
        div.stButton > button[key='side_toggle_delete_btn'] p, div.stButton > button[key='side_toggle_delete_btn'] span {
            color: #ef4444 !important; [cite: 23]
            text-decoration: underline !important; text-decoration-color: #ef4444 !important; text-underline-offset: 5px !important; font-weight: 700 !important; [cite: 24]
        } [cite: 25]
        div[data-testid="stTabs"] button[aria-selected="true"] p { color: #ef4444 !important; font-weight: bold !important; } [cite: 25]
        } [cite: 26]
        div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] { background-color: #ef4444 !important; } [cite: 26]
        } [cite: 27]
        div.stDownloadButton, div.stDownloadButton button, div.stDownloadButton button * { font-size: 11px !important; } [cite: 27]
        white-space: nowrap !important; word-break: keep-all !important; } [cite: 28]
        div.stDownloadButton button { padding: 4px 6px !important; } [cite: 28]
        } [cite: 29]
        div.stDownloadButton { margin-bottom: -15px !important; } [cite: 29]
        } [cite: 30]
        div.compact-upload-box { padding: 6px 10px !important; margin-top: 2px !important; margin-bottom: 2px !important; } [cite: 30]
        } [cite: 31]
        div[data-testid="stFileUploader"] { padding-top: 0px !important; margin-top: -10px !important; } [cite: 31]
        } [cite: 32]
        div[data-testid="stFileUploader"] section small { white-space: normal !important; word-break: break-all !important; } [cite: 32]
        display: block !important; line-height: 1.3 !important; color: #64748b !important; } [cite: 33]
        
        div.custom-guide-bar {
            background-color: #eff6ff !important; [cite: 33]
            border: 2px dashed #93c5fd !important; padding: 10px !important; border-radius: 8px !important; margin-top: 15px !important; margin-bottom: 10px !important; color: #1e3a8a !important; [cite: 34]
            font-size: 14px !important; text-align: center !important; font-weight: 500 !important; white-space: nowrap !important; [cite: 35]
        } [cite: 36]
        div.next-step-box {
            background-color: #f0fdf4 !important; [cite: 36]
            border: 2px solid #bbf7d0 !important; padding: 15px !important; border-radius: 10px !important; margin-top: 15px !important; margin-bottom: 15px !important; color: #166534 !important; [cite: 37]
            font-size: 14px !important; line-height: 1.6 !important; [cite: 38]
        }
        div.monitor-table table th, div.monitor-table table td { text-align: center !important; } [cite: 38]
        } [cite: 39]
    </style>
""", unsafe_allow_html=True)

def is_strong_password(pw):
    if len(pw) < 12: return False, "❌ 최소 12자리 이상이어야 합니다."
    if not re.search("[a-zA-Z]", pw): return False, "❌ 영문자가 포함되어야 합니다."
    if not re.search("[0-9]", pw): return False, "❌ 숫자가 포함되어야 합니다."
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", pw): return False, "❌ 특수문자가 포함되어야 합니다."
    return True, "✅ 사용 가능한 안전한 암호 조건입니다." [cite: 40]

def load_master_subjects():
    default_structure = {
        "인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"],
        "수리·과학군": ["수학", "과학", "기술·가정", "정보"],
        "예체능군": ["음악", "미술", "체육"]
    }
    df = load_sheet_to_df("master_subjects", ["교과군", "과목명"]) [cite: 40]
    if not df.empty: [cite: 40]
        for _, row in df.iterrows(): [cite: 40]
            group = str(row['교과군']).strip() [cite: 40]
            sub = str(row['과목명']).strip() [cite: 41]
            if group in default_structure and sub not in default_structure[group]: [cite: 41]
                default_structure[group].append(sub) [cite: 41]
    return default_structure [cite: 41]

def save_new_subject_to_master(group, subject):
    df = load_sheet_to_df("master_subjects", ["교과군", "과목명"]) [cite: 41]
    if not ((df['교과군'] == group) & (df['과목명'] == subject)).any(): [cite: 41]
        new_row = pd.DataFrame([{"교과군": group, "과목명": subject}]) [cite: 41]
        df = pd.concat([df, new_row], ignore_index=True) [cite: 41]
        save_df_to_sheet("master_subjects", df) [cite: 42]

def load_admin_password():
    df = load_sheet_to_df("admin_meta", ["password"]) [cite: 42]
    if not df.empty: [cite: 42]
        return str(df.iloc[0]['password']).strip() [cite: 42]
    return "1234" [cite: 42]

def save_admin_password(new_pw):
    df = pd.DataFrame([{"password": str(new_pw).strip()}]) [cite: 42]
    save_df_to_sheet("admin_meta", df) [cite: 42]

def get_sheet_names_id(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_") [cite: 42]
    safe_semester = semester_str.replace(" ", "_").replace("/", "_") [cite: 42]
    return f"cfg_{safe_subject}_{grade}_{safe_semester}", f"st_{safe_subject}_{grade}_{safe_semester}" [cite: 42]

def get_active_databases():
    active_list = [] [cite: 42]
    if gc is None: return active_list [cite: 43]
    try:
        sh = gc.open(SPREADSHEET_NAME) [cite: 43]
        for wks in sh.worksheets(): [cite: 43]
            name = wks.title [cite: 43]
            if name.startswith("cfg_"): [cite: 43]
                core_name = name.replace("cfg_", "") [cite: 43]
                match = re.search(r"(.+?)_(1|2|3)_(.+)", core_name) [cite: 43]
                if match: [cite: 44]
                    sub_name = match.group(1).replace("_", " ") [cite: 44]
                    grd_name = f"{match.group(2)}학년" [cite: 44]
                    sem_name = match.group(3).replace("_", " ") [cite: 44]
                    active_list.append({"subject": sub_name, "grade": grd_name, "semester": sem_name}) [cite: 45]
    except: pass [cite: 45]
    return active_list [cite: 45]

def remove_subject_completely_from_disk(sub_name):
    df_m = load_sheet_to_df("master_subjects", ["교과군", "과목명"]) [cite: 45]
    if not df_m.empty: [cite: 45]
        df_m = df_m[df_m["과목명"] != sub_name] [cite: 45]
        save_df_to_sheet("master_subjects", df_m) [cite: 45]
    if gc is None: return [cite: 45]
    try:
        sh = gc.open(SPREADSHEET_NAME) [cite: 45]
        safe_sub = sub_name.replace(" ", "_") [cite: 45]
        for wks in sh.worksheets(): [cite: 45]
            if safe_sub in wks.title and (wks.title.startswith("cfg_") or wks.title.startswith("st_")): [cite: 46]
                sh.del_worksheet(wks) [cite: 46]
    except: pass [cite: 46]

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict):
    st.markdown(f"<div style='margin-bottom:15px;'><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True) [cite: 46]
    st.table(pd.DataFrame(scores_dict)) [cite: 46]
    if st.button("확인 후 닫기", use_container_width=True, type="primary"): [cite: 46]
        st.session_state.clear() [cite: 46]
        st.rerun() [cite: 46]

@st.dialog("🔐 관리자 암호 수정")
def password_update_dialog():
    st.markdown("<div style='padding: 5px;'></div>", unsafe_allow_html=True) [cite: 46]
    new_pw = st.text_input("새 암호 입력", type="password", key="dialog_new_pw") [cite: 46, 47]
    confirm_pw = st.text_input("2. 새 암호 확인", type="password", key="dialog_confirm_pw") [cite: 47]
    is_valid, msg = is_strong_password(new_pw) [cite: 47]
    if new_pw: [cite: 47]
        if new_pw == confirm_pw and is_valid: [cite: 47]
            st.markdown("<div style='background-color:#E8F5E9; border-radius:4px; padding:10px; color:#2E7D32; font-weight:500; margin-bottom:10px;'>✅ 두 암호가 완벽하게 일치합니다.</div>", unsafe_allow_html=True) [cite: 47]
        elif confirm_pw and new_pw != confirm_pw: [cite: 47]
            st.error("❌ 암호 확인 칸이 일치하지 않습니다.") [cite: 47]
        else: [cite: 48]
            st.warning(msg) [cite: 48]
    st.markdown("""<div style="font-size: 13px; color: #57606a; line-height: 1.6; background: #f8f9fa; padding: 15px; border-radius: 8px;">
    <b>[안전 암호 규칙]</b><br>- 최소 12자 이상 필수<br>- 영문 + 숫자 + 특수기호 조합
    </div>""", unsafe_allow_html=True) [cite: 48]
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True) [cite: 48]
    can_submit = is_valid and (new_pw == confirm_pw) [cite: 48]
    b_col1, b_col2 = st.columns(2) [cite: 48]
    with b_col1: [cite: 48]
        if st.button("저장 후 적용", disabled=not can_submit, use_container_width=True, type="primary"): [cite: 48]
            save_admin_password(new_pw); st.toast("🎉 암호가 변경되었습니다!"); st.rerun() [cite: 49]
    with b_col2: [cite: 49]
        if st.button("수정 취소", use_container_width=True): st.rerun() [cite: 49]

if "page_status" not in st.session_state: st.session_state["page_status"] = "student_main" [cite: 49]
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False [cite: 49]
if "show_monitor_view" not in st.session_state: st.session_state["show_monitor_view"] = False [cite: 49]
if "show_delete_panel" not in st.session_state: st.session_state["show_delete_panel"] = False [cite: 49]
if "sel_group_idx" not in st.session_state: st.session_state.sel_group_idx = 0 [cite: 49]
if "sel_sub_idx" not in st.session_state: st.session_state.sel_sub_idx = 0 [cite: 49]
if "sel_grade_idx" not in st.session_state: st.session_state.sel_grade_idx = 0 [cite: 49]
if "sel_semester_idx" not in st.session_state: st.session_state.sel_semester_idx = 0 [cite: 49]

SUBJECT_MAP = load_master_subjects() [cite: 49]
GRADE_OPTIONS = ["학년 선택", "1학년", "2학년", "3학년"] [cite: 49]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]] [cite: 49, 50]
CURRENT_ADMIN_PW = load_admin_password() [cite: 50]

# ==========================================
# 🔄 화면 분기 구동 영역 
# ==========================================
if st.session_state["page_status"] == "student_main": [cite: 50]
    st.markdown("<style>div[data-testid='stVerticalBlockBorderWrapper'] { border: 1px solid #e2e8f0 !important; padding: 35px 40px !important; border-radius: 12px !important; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; background-color: #ffffff !important; max-width: 500px !important; margin: 0px auto 20px auto !important; }</style>", unsafe_allow_html=True) [cite: 50, 51, 52]
    col_empty, col_btn = st.columns([3, 1]) [cite: 52]
    with col_btn: [cite: 52]
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True) [cite: 52]
        if st.button("🔓 교사용 제어판", key="outer_teacher_btn"): st.session_state["page_status"] = "teacher_auth"; st.rerun() [cite: 52]
            
    active_dbs = get_active_databases() [cite: 52]
    with st.container(border=True): [cite: 52]
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 5px 0px;'>🎒 수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True) [cite: 52]
        st.markdown("<h4 style='text-align: center; margin: 0px 0px 10px 0px; color: #475569;'>📝 개인별 성적 조회</h4>", unsafe_allow_html=True) [cite: 53]
        st.markdown("<p style='text-align:center; font-size:14px; color:#64748b; margin-bottom:20px;'>과목과 해당 학기를 선택하고 정보를 입력해 주세요.</p>", unsafe_allow_html=True) [cite: 53]
        st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True) [cite: 53]
        
        if not active_dbs: [cite: 53]
            st.warning("현재 등록된 성적 데이터가 없습니다.") [cite: 53]
        else: [cite: 53]
            st.markdown("<div style='font-size:14px; font-weight:700; color:#0f172a; margin-bottom:8px;'>🎯 대상 과목 및 학기 선택</div>", unsafe_allow_html=True) [cite: 54, 55]
            opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs] [cite: 55]
            sel_s = st.selectbox("조회할 과목 선택", opts_s, label_visibility="collapsed", key="student_select_sub") [cite: 55]
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True) [cite: 55]
            
            if sel_s != "과목 및 학기를 선택하세요.": [cite: 55]
                db = active_dbs[opts_s.index(sel_s)-1] [cite: 56]
                cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester']) [cite: 56]
                
                df_load = load_sheet_to_df(cf_id) [cite: 56]
                config = df_load.iloc[0].to_dict() if not df_load.empty else None [cite: 56]
                
                if config: [cite: 57]
                    sub_title = config.get('교과명', config.get('과목명', '미정')) [cite: 57]
                    st.markdown(f"<div style='background:#f1f5f9; padding:12px 15px; border-radius:8px; margin-bottom:20px; font-size:14px;'><span style='font-weight:600; color:#475569;'>선택된 교과:</span> &nbsp;🧬 <b>{sub_title}</b> ({config.get('학기통합명','')})</div>", unsafe_allow_html=True) [cite: 57, 58]
                    
                    with st.form("login_form"): [cite: 58]
                        st.markdown("<div style='font-size:14px; font-weight:700; color:#0f172a; margin-bottom:8px;'>🔐 본인 인증 정보 입력</div>", unsafe_allow_html=True) [cite: 58]
                        classes = [f"{x.strip()}반" for x in str(config.get('선택된반 목록', '1')).split(",") if x.strip()] [cite: 59]
                        if not classes: classes = ["1반"] [cite: 59]
                        
                        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5]) [cite: 59, 60]
                        with c1: b_in = st.selectbox("반", classes) [cite: 60]
                        with c2: n_in = st.number_input("번호", 1, 50, 1) [cite: 60]
                        with c3: name_in = st.text_input("이름", placeholder="홍길동") [cite: 60]
                        with c4: pw_in = st.text_input("비밀번호", type="password", placeholder="****") [cite: 61]
                        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) [cite: 61]
                        
                        if st.form_submit_button("🔍 내 점수 확인하기", use_container_width=True, type="primary"): [cite: 61, 62]
                            df_st = load_sheet_to_df(sf_id) [cite: 62]
                            if df_st.empty: st.error("성적 데이터가 아직 연동되지 않은 교과입니다.") [cite: 62]
                            else: [cite: 62]
                                if '확인여부' in df_st.columns: df_st['확인여부'] = df_st['확인여부'].astype(str).replace(['nan', 'None', ''], '미확인') [cite: 63]
                                if '확인시간' in df_st.columns: df_st['확인시간'] = df_st['확인시간'].astype(str).replace(['nan', 'None', ''], '') [cite: 63]
                                res = df_st[(df_st['반'].astype(int)==int(b_in.replace("반",""))) & (df_st['번호'].astype(int)==n_in) & (df_st['이름'].astype(str)==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))] [cite: 64]
                                if not res.empty: [cite: 64]
                                    idx = res.index[0] [cite: 64]
                                    scores, total_sum = {}, 0 [cite: 65]
                                    for i in range(int(config['항목개수'])): [cite: 65]
                                        h_name = config.get(f'항목{i+1}_이름', f'항목{i+1}') [cite: 66]
                                        if h_name in df_st.columns: [cite: 66]
                                            val = df_st.loc[idx, h_name]; scores[h_name] = [val] [cite: 66, 67]
                                            try: [cite: 67]
                                                if pd.notna(val): total_sum += float(val) [cite: 67]
                                            except: pass [cite: 68]
                                    if float(total_sum).is_integer(): scores['합계'] = [int(total_sum)] [cite: 68]
                                    else: scores['합계'] = [round(total_sum, 2)] [cite: 69]
                                    
                                    df_st.loc[idx, '확인여부'] = str("확인 완료") [cite: 69]
                                    df_st.loc[idx, '확인시간'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) [cite: 70]
                                    save_df_to_sheet(sf_id, df_st) [cite: 70]
                                    show_result_dialog(name_in, scores) [cite: 71]
                                else: st.error("입력한 학생 정보 또는 비밀번호가 일치하지 않습니다.") [cite: 71]

elif st.session_state["page_status"] == "teacher_auth":
    st.markdown("<style>div[data-testid='stForm'] { border: 1px solid #e2e8f0 !important; padding: 35px 40px !important; border-radius: 12px !important; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; background-color: #ffffff !important; max-width: 450px !important; margin: 40px auto 20px auto !important; }</style>", unsafe_allow_html=True) [cite: 71, 72, 73]
    with st.form("admin_login_form"): [cite: 73]
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 5px 0px;'>⚙️ 교과 통합 관리자</h2>", unsafe_allow_html=True) [cite: 73]
        st.markdown("<hr style='margin: 15px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True) [cite: 73]
        st.markdown("<p style='text-align:center; font-size:14px; color:#64748b; margin-bottom:25px; line-height: 1.5;'>여러 교과와 학년별 성적 데이터베이스를<br>스위칭하며 관리하는 공간입니다.</p>", unsafe_allow_html=True) [cite: 73]
        st.markdown("<div style='font-size:13px; font-weight:600; color:#1e293b; margin-bottom:8px;'>관리자 인증 비밀번호를 입력하세요</div>", unsafe_allow_html=True) [cite: 73]
        admin_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력", label_visibility="collapsed") [cite: 73, 74]
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True) [cite: 74]
        if st.form_submit_button("로그인", use_container_width=True, type="primary"): [cite: 74]
            if admin_pw == CURRENT_ADMIN_PW: st.session_state["admin_logged_in"] = True; st.session_state["page_status"] = "teacher_main"; st.rerun() [cite: 74, 75]
            else: st.error("❌ 비밀번호가 틀렸습니다.") [cite: 75]
    col1, col2, col3 = st.columns([1, 2, 1]) [cite: 75]
    with col2: [cite: 75]
        if st.button("🎒 학생 화면으로 돌아가기", key="outer_student_btn", use_container_width=True): st.session_state["page_status"] = "student_main"; st.rerun() [cite: 75, 76]

elif st.session_state["page_status"] == "teacher_main":
    if not st.session_state["admin_logged_in"]: st.session_state["page_status"] = "teacher_auth"; st.rerun() [cite: 76, 77]
    col_empty, col_pw, col_logout = st.columns([5, 1.4, 1.4]) [cite: 77]
    with col_pw: [cite: 77]
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True) [cite: 77]
        if st.button("🔐 암호 변경", key="outer_pw_btn", use_container_width=True): password_update_dialog() [cite: 77]
    with col_logout: [cite: 77]
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True) [cite: 77]
        if st.button("🎒 학생 화면", key="outer_logout_btn", use_container_width=True): [cite: 77]
            st.session_state["page_status"] = "student_main"; st.session_state["admin_logged_in"] = False; st.session_state["show_monitor_view"] = False; st.session_state["show_delete_panel"] = False; st.rerun() [cite: 78]

    with st.container(border=True): [cite: 78]
        st.markdown("<h2>⚙️ 교과·학년 통합 제어 센터</h2>", unsafe_allow_html=True) [cite: 78]
        frame_left, frame_right = st.columns([1.4, 4.2]) [cite: 78]
        has_active = "active_subject" in st.session_state and st.session_state.active_subject [cite: 78]
        
        with frame_left: [cite: 78]
            st.markdown("<h4>📁 대상 과목 및 학기 선택</h4>", unsafe_allow_html=True) [cite: 78]
            g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"] [cite: 79]
            sel_g = st.selectbox("1단계: 교과군 분류", options=g_opts, index=st.session_state.sel_group_idx, label_visibility="collapsed") [cite: 79]
            
            final_sub, t_g = "", "" [cite: 79]
            if sel_g == "➕ 신규 과목 개설": [cite: 79]
                t_g = st.selectbox("추가 위치 지정", ["인문·사회군", "수리·과학군", "예체능군"]) [cite: 79]
                final_sub = st.text_input("✏️ 새 과목명 입력", placeholder="과목명 입력").strip() [cite: 80]
            elif sel_g != "교과군 선택": [cite: 80]
                s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g] [cite: 80]
                idx_s = st.session_state.sel_sub_idx if st.session_state.sel_sub_idx < len(s_opts) else 0 [cite: 80]
                sel_s = st.selectbox("2단계: 세부 과목 선택", options=s_opts, index=idx_s, label_visibility="collapsed") [cite: 81]
                if sel_s != "과목 선택": final_sub = sel_s [cite: 81]
            else: st.selectbox("2단계: 세부 과목 선택", ["과목 선택 대기"], disabled=True, label_visibility="collapsed") [cite: 81]
                
            sel_gr = st.selectbox("3단계: 관리 학년 지정", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx, label_visibility="collapsed") [cite: 81]
            final_gr = sel_gr.replace("학년", "") if sel_gr != "학년 선택" else "" [cite: 81, 82]
            sel_se = st.selectbox("4단계: 대상 학기 선택", options=SEMESTER_OPTIONS, index=st.session_state.sel_semester_idx, label_visibility="collapsed") [cite: 82]
            final_se = sel_se if sel_se != "학기 선택" else "" [cite: 82]
            
            if st.button("🚀 과목 활성화", use_container_width=True, key="side_activate_btn"): [cite: 82]
                if final_sub and final_gr and final_se: [cite: 82]
                    if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub) [cite: 83]
                    st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester = final_sub, final_gr, final_se [cite: 83]
                    st.session_state.sel_group_idx = g_opts.index(sel_g) [cite: 83]
                    if sel_g != "➕ 신규 과목 개설": st.session_state.sel_sub_idx = s_opts.index(final_sub) [cite: 83, 84]
                    st.session_state.sel_grade_idx = GRADE_OPTIONS.index(sel_gr) [cite: 84]
                    st.session_state.sel_semester_idx = SEMESTER_OPTIONS.index(sel_se) [cite: 84]
                    
                    cf_id, sf_id = get_sheet_names_id(final_sub, final_gr, final_se) [cite: 84]
                    df_init = load_sheet_to_df(cf_id) [cite: 85]
                    if not df_init.empty: [cite: 85]
                        r_dict = df_init.iloc[0].to_dict() [cite: 85]
                        st.session_state["saved_classes_list"] = r_dict.get('선택된반 목록', '') [cite: 85]
                        st.session_state["saved_items_count"] = int(r_dict.get('항목개수', 0)) [cite: 86]
                    else: [cite: 86]
                        st.session_state["saved_classes_list"] = '' [cite: 86]
                        st.session_state["saved_items_count"] = 0 [cite: 86]
                        
                    st.session_state["just_saved_success"] = False [cite: 87]
                    st.session_state["show_delete_panel"] = False; st.rerun() [cite: 87, 88]
                else: st.warning("과목, 학년, 학기 데이터를 누락 없이 모두 선택해 주세요.") [cite: 88]
            
            del_panel_label = "🚨 데이터 삭제 닫기" if st.session_state["show_delete_panel"] else "🚨 데이터 삭제" [cite: 88]
            if st.button(del_panel_label, key="side_toggle_delete_btn", use_container_width=True): [cite: 88]
                st.session_state["show_delete_panel"] = not st.session_state["show_delete_panel"] [cite: 88]
                if st.session_state["show_delete_panel"]: st.session_state["show_monitor_view"] = False [cite: 89]
                st.rerun() [cite: 89]
            
            monitor_label = "👀 학생 입력 확인 닫기" if st.session_state["show_monitor_view"] else "👥 학생 입력 확인" [cite: 89]
            if st.button(monitor_label, key="side_monitor_btn", disabled=not has_active): st.session_state["show_monitor_view"] = not st.session_state["show_monitor_view"]; st.rerun() [cite: 89, 90]
                
            if has_active: [cite: 90]
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester [cite: 90]
                cf_id, sf_id = get_sheet_names_id(sub, grd, sem) [cite: 90]
                
                n_current = st.session_state.get("num_items_input", 0) [cite: 92]
                live_item_names = [] [cite: 92]
                for idx in range(n_current): [cite: 92]
                    val_live = st.session_state.get(f"item_name_input_{sub}_{idx+1}", f"수행{idx+1}").strip() [cite: 92]
                    if not val_live: val_live = f"수행{idx+1}" [cite: 92]
                    live_item_names.append(val_live) [cite: 93]

                with st.container(border=True): [cite: 93]
                    st.markdown('<div class="compact-upload-box">', unsafe_allow_html=True) [cite: 93]
                    st.markdown("<div style='font-size:12px; font-weight:600; color:#475569; margin-bottom:6px;'>📁 성적 일괄 업로드 (클라우드 직송)</div>", unsafe_allow_html=True) [cite: 93]
                    
                    base_headers = ["반", "번호", "이름", "비밀번호", "확인여부", "확인시간"] [cite: 94]
                    final_headers = base_headers + live_item_names [cite: 94]
                    sample_row = ["1", "1", "홍길동", "1234", "미확인", ""] + ["0"] * len(live_item_names) [cite: 95]
                    
                    output = io.StringIO() [cite: 95]
                    writer = csv.writer(output) [cite: 95]
                    writer.writerow(final_headers) [cite: 95]
                    writer.writerow(sample_row) [cite: 96]
                    csv_data = output.getvalue().encode('utf-8-sig') [cite: 96]
                    
                    st.download_button(label="📥 예시 파일 다운로드", data=csv_data, file_name=f"sample_students_{sub}_{sem}.csv", mime="text/csv", key="btn_download_sample") [cite: 96]
                    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True) [cite: 97]
                    
                    up_f = st.file_uploader("성적 CSV 업로드", type="csv", label_visibility="collapsed", key="uploader_csv_file") [cite: 97]
                    if up_f: [cite: 97]
                        try: [cite: 97]
                            df_up = pd.read_csv(up_f, encoding='cp949') [cite: 98]
                            success = save_df_to_sheet(sf_id, df_up) [cite: 98]
                            if success: [cite: 98]
                                st.success("🎉 구글 시트로 성적 동기화 완벽 완료!") [cite: 99]
                                st.rerun() [cite: 99]
                            else: [cite: 99]
                                st.error("❌ 구글 시트 업로드 실패. 권한 및 파일명을 점검하세요.") [cite: 100, 101]
                        except: [cite: 101]
                            st.error("❌ 인코딩 포맷을 확인해 주세요. (EUC-KR 또는 CP949)") [cite: 101]
                    st.markdown('</div>', unsafe_allow_html=True) [cite: 101]
                        
            if st.button("🗑️ 시스템 초기화", key="side_reset_btn"): reset_all_data() [cite: 102]

        with frame_right: [cite: 102]
            show_del = st.session_state.get("show_delete_panel", False) [cite: 102]
            if show_del: [cite: 102]
                st.markdown("<h4 style='color: #ef4444; margin-top: 0px;'>⚙️ 데이터 삭제 및 청소 관리 센터</h4>", unsafe_allow_html=True) [cite: 102]
                tab_del_sem, tab_del_sub = st.tabs(["학기 및 학년별 삭제", "과목 일괄 삭제"]) [cite: 103]
                
                with tab_del_sem: [cite: 103]
                    existing_dbs = get_active_databases() [cite: 103]
                    if not existing_dbs: st.info("현재 구글 시트에 보관 중인 분기 데이터가 없습니다.") [cite: 103]
                    else: [cite: 104]
                        sem_opts = [f"📚 {d['subject']} | {d['grade']} | {d['semester']}" for d in existing_dbs] [cite: 104, 105]
                        selected_sem_str = st.selectbox("삭제 대상 선택", options=sem_opts, label_visibility="collapsed", key="sb_delete_target_sem") [cite: 105]
                        t_db = existing_dbs[sem_opts.index(selected_sem_str)] [cite: 105]
                        verify_code_sem = f"{t_db['subject']}_{t_db['grade'].replace('학년','')}_{t_db['semester'].replace('학년도','').replace(' ', '')}" [cite: 105]
                        
                        st.markdown(f"<div style='font-size:12px; margin-bottom:4px;'>인증코드 입력: <code style='color:#ef4444;'>{verify_code_sem}</code></div>", unsafe_allow_html=True) [cite: 106]
                        user_confirm_sem = st.text_input("인증코드 입력창", label_visibility="collapsed", key="ti_verify_sem_code") [cite: 106]
                        if st.button("🔒 선택 학기 데이터 영구 폐기 실행", disabled=(user_confirm_sem != verify_code_sem), type="primary", use_container_width=True): [cite: 106, 107]
                            cf_id, sf_id = get_sheet_names_id(t_db['subject'], t_db['grade'].replace("학년",""), t_db['semester']) [cite: 107]
                            if gc: [cite: 107]
                                try: [cite: 108]
                                    sh = gc.open(SPREADSHEET_NAME) [cite: 108]
                                    for n in [cf_id, sf_id]: sh.del_worksheet(sh.worksheet(n)) [cite: 108]
                                except: pass [cite: 109]
                            st.toast("🎉 선택하신 분기 데이터 클렌징 완료!"); st.rerun() [cite: 109, 110]

                with tab_del_sub: [cite: 110]
                    raw_subjects = load_master_subjects() [cite: 110]
                    flat_subs = sorted(list(set([sub for list_sub in raw_subjects.values() for sub in list_sub]))) [cite: 110]
                    if not flat_subs: st.info("등록 개설된 교과목 마스터 목록이 비어 있습니다.") [cite: 110]
                    else: [cite: 111]
                        selected_sub_to_del = st.selectbox("과목명 선택", options=flat_subs, label_visibility="collapsed", key="sb_delete_target_sub") [cite: 111]
                        user_confirm_sub = st.text_input(f"과목명 정확히 재입력 ({selected_sub_to_del})", label_visibility="collapsed", key="ti_verify_sub_code") [cite: 111]
                        if st.button("🚨 마스터 교과 일괄 파괴 실행", disabled=(user_confirm_sub != selected_sub_to_del), type="primary", use_container_width=True): [cite: 112]
                            remove_subject_completely_from_disk(selected_sub_to_del); st.toast("🎉 교과 소멸 완료!"); st.rerun() [cite: 112, 113]

            elif has_active: [cite: 113]
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester [cite: 113]
                
                # 🌟 [버그 원천 완치]: 에러를 내던 NameError 변수명을 sub, grd, sem 명칭으로 완벽 교정!
                cf_id, sf_id = get_sheet_names_id(sub, grd, sem) [cite: 90]
                
                df_load_main = load_sheet_to_df(cf_id) [cite: 113]
                conf = {} [cite: 114]
                if not df_load_main.empty: [cite: 114]
                    raw_dict = df_load_main.iloc[0].to_dict() [cite: 114]
                    conf['과목명'] = raw_dict.get('과목명', raw_dict.get('교과명', sub)) [cite: 114]
                    conf['학년'] = raw_dict.get('학년', grd) [cite: 114]
                    conf['학기통합명'] = raw_dict.get('학기통합명', sem) [cite: 115]
                    conf['선택된반 목록'] = raw_dict.get('선택된반 목록', '') [cite: 115]
                    conf['항목개수'] = raw_dict.get('항목개수', 0) [cite: 115]
                    for k, v in raw_dict.items(): [cite: 115]
                        if '항목' in k: conf[k] = v [cite: 116]
                
                st.markdown(f"<div style='background-color:#eff6ff; border:1px solid #bfdbfe; padding:8px 12px; border-radius:6px; margin-bottom:12px; text-align:center; font-size:13px; font-weight:600; color:#1e40af;'>📍 작업 구역: [{sub}] {grd}학년 ({sem})</div>", unsafe_allow_html=True) [cite: 116, 117]

                with st.container(border=True): [cite: 117]
                    saved_cl_str = st.session_state.get("saved_classes_list", str(conf.get('선택된반 목록', ''))) [cite: 117]
                    saved_cl = [] [cite: 117]
                    if saved_cl_str: [cite: 117]
                        saved_cl = [int(x) for x in str(saved_cl_str).replace("[","").replace("]","").split(",") if str(x).strip()] [cite: 118]
                    
                    default_items_count = st.session_state.get("saved_items_count", int(conf.get('항목개수', 0))) [cite: 118]

                    st.markdown("<div style='font-size:12px; font-weight:600; color:#475569;'>🏫 담당 학급(반) 지정</div>", unsafe_allow_html=True) [cite: 118]
                    sel_cl = [] [cite: 119]
                    cols_cl = st.columns(6) [cite: 119]
                    for i in range(1, 13): [cite: 119]
                        with cols_cl[(i-1)%6]: [cite: 119]
                            if st.checkbox(f"{i}반", value=i in saved_cl, key=f"chk_class_{i}"): sel_cl.append(i) [cite: 120]

                    st.markdown("<div style='margin-top:8px; font-size:12px; font-weight:600; color:#475569;'>✍️ 평가 항목 설정</div>", unsafe_allow_html=True) [cite: 120, 121]
                    n_item = st.number_input("평가 항목 개수", min_value=0, max_value=10, value=default_items_count, key="num_items_input") [cite: 121]
                    
                    item_names = [] [cite: 121]
                    if n_item > 0: [cite: 121]
                        for i in range(n_item): [cite: 122]
                            if i % 2 == 0: [cite: 122]
                                cols_i = st.columns(2) [cite: 122]
                                with cols_i[0]: [cite: 123]
                                    name = st.text_input(f"{i+1}번 항목명", value=conf.get(f'항목{i+1}_이름', ""), placeholder=f"예: 수행평가{i+1}", key=f"item_name_input_{sub}_{i+1}") [cite: 123]
                            else: [cite: 123]
                                with cols_i[1]: [cite: 124]
                                    name = st.text_input(f"{i+1}번 항목명", value=conf.get(f'항목{i+1}_이름', ""), placeholder=f"예: 수행평가{i+1}", key=f"item_name_input_{sub}_{i+1}") [cite: 124]
                            item_names.append(name.strip()) [cite: 125]

                        # 🌟 [동선 설계 복원]: 항목명 상자가 펼쳐지면 바로 밑줄에 저장 버튼 연동
                        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True) [cite: 125]
                        if st.button(f"💾 [{sub}] 과목 사양 최종 저장하기", type="primary", use_container_width=True, key="embedded_save_btn"): [cite: 125]
                            if sel_cl and all(item_names): [cite: 125]
                                classes_string = ",".join(map(str, sorted(sel_cl))) [cite: 126]
                                d = {
                                    "과목명": sub, "교과명": sub, "학년": grd, "학기통합명": sem, [cite: 126, 127]
                                    "선택된반 목록": classes_string, "항목개수": n_item [cite: 127]
                                }
                                for i, name_val in enumerate(item_names): d[f"항목{i+1}_이름"] = name_val [cite: 128]
                                
                                get_google_sheet(cf_id) [cite: 129]
                                save_df_to_sheet(cf_id, pd.DataFrame([d])) [cite: 129]
                                get_google_sheet(sf_id) [cite: 129]
                                
                                st.session_state["saved_classes_list"] = classes_string [cite: 130]
                                st.session_state["saved_items_count"] = n_item [cite: 130]
                                st.session_state["just_saved_success"] = True [cite: 131]
                                
                                st.toast("💾 설정이 구글 클라우드에 연동되었습니다!") [cite: 131]
                                st.rerun() [cite: 132]
                            else:
                                st.error("❌ 담당 학급(반)을 한 개 이상 선택하고, 항목명을 전부 완성해 주셔야 저장이 가능합니다.") [cite: 132]

                # 🌟 [동선 설계 복원]: 완료 후 안내 가이드 박스 표출
                if st.session_state.get("just_saved_success", False): [cite: 133]
                    st.markdown(f"""
                        <div class="next-step-box">
                            <b>✅ [{sub}] 과목 사양 설정 완료!</b><br> [cite: 133]
                            구글 클라우드에 테이블 방(cfg_...)이 완벽하게 개설되었습니다. 이제 다음 작업을 순서대로 이어가세요:<br> [cite: 134, 135]
                            <hr style='margin:8px 0; border:none; border-top:1px solid #bbf7d0;'> [cite: 135, 136]
                            1️⃣ 왼쪽 하단 서랍에 있는 <b>📥 예시 파일 다운로드</b> 버튼을 누릅니다.<br> [cite: 136]
                            2️⃣ 방금 다운로드된 따끈따끈한 맞춤형 CSV 양식을 열어 학생 인적 사항과 점수를 기입합니다.<br> [cite: 136]
                            3️⃣ 파일 선택 창에 완성된 성적 파일을 업로드하시면 실시간 성적 공시 엔진이 완벽하게 가동됩니다! [cite: 137]
                        </div> [cite: 138]
                    """, unsafe_allow_html=True)

                show_mon = st.session_state.get("show_monitor_view", False) [cite: 138]
                if show_mon: [cite: 138]
                    st.markdown("<h4 style='color: #0f172a;'>📊 실시간 데이터 연동 모니터 (구글 시트)</h4>", unsafe_allow_html=True) [cite: 138]
                    with st.container(border=True): [cite: 139]
                        df_monitor = load_sheet_to_df(sf_id) [cite: 139]
                        if not df_monitor.empty: [cite: 139]
                            st.markdown('<div class="monitor-table">', unsafe_allow_html=True) [cite: 139]
                            st.dataframe(df_monitor, use_container_width=True, hide_index=True) [cite: 140]
                            st.markdown('</div>', unsafe_allow_html=True) [cite: 140]
                        else: st.warning("⚠️ 해당 학기의 성적 데이터가 구글 시트에 아직 업로드되지 않았습니다.") [cite: 140]
            else:
                st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True) [cite: 141]
                st.info("👈 왼쪽 제어판에서 과목 사양을 선택한 뒤 [🚀 과목 활성화]를 눌러주세요.") [cite: 141]

        st.markdown("<div class='custom-guide-bar'>💡 <b>[🚀 과목 활성화]</b>를 누르시면 해당 구글 시트 데이터베이스를 원격 로드합니다.</div>", unsafe_allow_html=True) [cite: 141]