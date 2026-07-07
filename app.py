import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
from datetime import datetime
import io
import re
import gspread
from google.oauth2.service_account import Credentials
import csv

# 🚨 [최상단 규칙 엄수] 와이드 레이아웃 설정
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="wide")

# =========================================================================
# 🔄 [방탄 CSS] 드롭다운 완벽 테두리 적용 & 사이드바 텍스트 절대 관통
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        [data-testid="stAppViewContainer"] { margin-left: 0px !important; }

        /* 🚨 사이드바 배경 및 폭 고정 */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] { 
            min-width: 280px !important; 
            max-width: 280px !important; 
            background-color: #1e293b !important; 
            box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; 
        }
        
        /* 🚨 [사이드바 메뉴 텍스트 순백색 관통] */
        [data-testid="stSidebar"] .stRadio label p,
        [data-testid="stSidebar"] .stRadio label span,
        [data-testid="stSidebar"] .stRadio label div,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div[role="radiogroup"] *,
        [data-testid="stSidebar"] div[role="radiogroup"] label *,
        [data-testid="stSidebar"] div[role="radiogroup"] p,
        [data-testid="stSidebar"] div[role="radiogroup"] span {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 16px !important; font-weight: 700 !important; line-height: 2.2 !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover * { color: #60a5fa !important; -webkit-text-fill-color: #60a5fa !important; }
        
        .sidebar-title { font-size: 24px !important; font-weight: 800 !important; margin-bottom: 5px !important; display: block; }
        .user-info { color: #38bdf8 !important; -webkit-text-fill-color: #38bdf8 !important; font-size: 14px !important; font-weight: 600 !important; margin-bottom: 25px !important; }

        /* [사이드바 버튼 예외 처리] */
        [data-testid="stSidebar"] button[kind="secondary"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 12px 0 !important; width: 100% !important; display: block !important; margin-bottom: 8px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] *, [data-testid="stSidebar"] button[kind="secondary"] p { color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; font-size: 15px !important; font-weight: 700 !important; }
        [data-testid="stSidebar"] button[kind="secondary"]:hover { background-color: #f8fafc !important; border-color: #3b82f6 !important; }

        /* 메인 화면 버튼 디자인 */
        div.stButton > button[kind="primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2) !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #2563eb !important; }
        div.stButton > button[kind="secondary"] { background-color: #ffffff !important; color: #0f172a !important; font-weight: 700 !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
        div.stButton > button[kind="secondary"]:hover { background-color: #f8fafc !important; border-color: #3b82f6 !important; color: #2563eb !important; }

        /* 팝업 다이얼로그 전용 버튼 */
        [data-testid="stDialog"] button[kind="primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 800 !important; border: none !important; border-radius: 6px !important; padding: 12px 0 !important; font-size: 15px !important; width: 100% !important; }
        [data-testid="stDialog"] button[kind="secondary"] { background-color: #64748b !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; padding: 12px 0 !important; font-size: 15px !important; width: 100% !important; }

        div[data-testid="InputInstructions"] { display: none !important; }

        /* 🚨 [시인성 강화] 드롭다운 및 텍스트 입력창 제목(라벨) 굵고 뚜렷하게 */
        div[data-testid="stSelectbox"] label p, 
        div[data-testid="stTextInput"] label p { 
            font-weight: 800 !important; 
            color: #1e293b !important; 
            font-size: 15px !important; 
        }

        /* 🚨 [핵심 수정: Streamlit 방어막 관통] 평상시 뚜렷한 진회색 테두리 */
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-testid="stSelectbox"] div[data-baseweb="select"],
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div { 
            background-color: #ffffff !important; 
            border: 1px solid #94a3b8 !important; /* Base Web을 뚫고 무조건 진회색 표출 */
            border-radius: 6px !important; 
            transition: all 0.2s ease-in-out !important; 
            box-shadow: none !important; /* 기본 방어막 그림자 제거 */
        }
        
        /* 🎯 [클릭 시 파란색 애니메이션] */
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
            border: 2px solid #3b82f6 !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
        }

        div[data-testid="stTextInput"] div[data-baseweb="base-input"], div[data-testid="stTextInput"] input { background-color: transparent !important; }

        /* 로그인 박스 및 기타 설정 */
        div[data-testid="stForm"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; padding: 45px 40px 45px 40px !important; border-radius: 24px !important; box-shadow: 0 15px 40px rgba(0,0,0,0.06) !important; max-width: 440px !important; margin: 70px auto 0 auto !important; }
        div[data-testid="stForm"] h2 { font-size: 26px !important; white-space: nowrap !important; text-align: center !important; margin: 0 auto 20px auto !important; font-weight: 800 !important; color: #0f172a !important; }
        div[data-testid="stForm"] div[data-testid="stRadio"] { padding-left: 95px !important; margin-bottom: 25px !important; width: 100% !important; }
        div[data-testid="stForm"] div[role="radiogroup"] { display: flex !important; gap: 35px !important; align-items: center !important; }
        .footer-container { width: 100%; display: flex; justify-content: center; margin-top: 25px; }
        .footer-text { text-align: center; font-size: 12px; color: #94a3b8; font-weight: 500; }
        h3 { color: #1e293b !important; font-weight: 700 !important; font-size: 20px !important; margin-top: 0px !important; margin-bottom: 5px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 백엔드 구글 시트 연동 함수 ---
def init_google_sheet_client():
    try: return gspread.authorize(Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except: return None

gc = init_google_sheet_client()
SPREADSHEET_NAME = "수행평가_데이터베이스"

def get_google_sheet(sheet_name):
    if gc is None: return None
    try:
        sh = gc.open(SPREADSHEET_NAME)
        for ws in sh.worksheets():
            if ws.title.strip() == sheet_name.strip(): return ws
        return sh.worksheet(sheet_name)
    except:
        try:
            sh = gc.open(SPREADSHEET_NAME)
            return sh.add_worksheet(title=sheet_name, rows="100", cols="20")
        except: return None

def load_sheet_to_df(sheet_name):
    wks = get_google_sheet(sheet_name)
    if wks is None: return pd.DataFrame()
    try:
        all_values = wks.get_all_values()
        if not all_values or len(all_values) < 1: return pd.DataFrame()
        headers = [str(h).strip() for h in all_values[0] if str(h).strip()]
        rows = all_values[1:]
        cleaned_rows = []
        for r in rows:
            if len(r) < len(headers): r = r + [""] * (len(headers) - len(r))
            cleaned_rows.append([str(cell).strip() for cell in r[:len(headers)]])
        return pd.DataFrame(cleaned_rows, columns=headers)
    except: return pd.DataFrame()

def save_df_to_sheet(sheet_name, df):
    wks = get_google_sheet(sheet_name)
    if wks is None: return False
    try:
        wks.clear()
        wks.update(range_name="A1", values=[df.fillna("").columns.tolist()] + df.fillna("").values.tolist())
        return True
    except: return False

def load_master_subjects():
    df = load_sheet_to_df("master_subjects")
    default_structure = {"인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"], "수리·과학군": ["수학", "과학", "기술·가정", "정보"], "예체능군": ["음악", "미술", "체육"]}
    if not df.empty and "교과군" in df.columns and "과목명" in df.columns:
        for _, row in df.iterrows():
            group = str(row['교과군']).strip()
            sub = str(row['과목명']).strip()
            if group in default_structure and sub not in default_structure[group]: default_structure[group].append(sub)
    return default_structure

def get_sheet_names_id(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    return f"cfg_{safe_subject}_{grade}Grade", f"st_{safe_subject}_{grade}_{semester_str.replace(' ', '_').replace('/', '_')}"

@st.dialog("👤 내 정보 수정")
def show_profile_popup_dialog():
    st.markdown(f"<div>👤 <b>{st.session_state['teacher_name']}</b> 선생님의 계정 정보를 관리합니다.</div><br>", unsafe_allow_html=True)
    edit_mode = st.radio("관리할 항목 선택", ["🔐 비밀번호 변경", "📚 담당과목 변경"], horizontal=True)
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    if edit_mode == "🔐 비밀번호 변경":
        if "pw_step_unlocked" not in st.session_state: st.session_state["pw_step_unlocked"] = False
        is_unlocked = st.session_state["pw_step_unlocked"]

        curr_pw = st.text_input("현재 비밀번호", type="password", placeholder="현재 사용 중인 비밀번호 입력", key="curr_pw_input_field", disabled=is_unlocked)
        
        if not is_unlocked and curr_pw:
            actual_pw = st.session_state.get("logged_teacher_pw", "")
            if not actual_pw and st.session_state.get("logged_teacher_id"):
                df_tc = load_sheet_to_df("teacher_accounts")
                if not df_tc.empty and "교사_ID" in df_tc.columns:
                    match = df_tc[df_tc["교사_ID"] == st.session_state["logged_teacher_id"]]
                    if not match.empty: actual_pw = str(match.iloc[0].get("비밀번호", "")).strip()

            if st.session_state["logged_teacher_id"] == "admin":
                st.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold; margin-top: -10px;'>❌ 최고관리자(admin) 계정은 변경할 수 없습니다.</p>", unsafe_allow_html=True)
            elif curr_pw != actual_pw:
                st.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold; margin-top: -10px;'>❌ 현재 비밀번호가 일치하지 않습니다.</p>", unsafe_allow_html=True)
            else:
                st.session_state["pw_step_unlocked"] = True
                is_unlocked = True

        if is_unlocked:
            st.markdown("<p style='color: #10b981; font-size: 13px; font-weight: bold;'>✅ 현재 비밀번호가 확인되었습니다. 변경할 새 비밀번호를 입력하세요.</p>", unsafe_allow_html=True)
            new_pw = st.text_input("새 비밀번호 입력", type="password", placeholder="새로운 비밀번호")
            new_pw_confirm = st.text_input("새 비밀번호 확인", type="password", placeholder="새로운 비밀번호 다시 입력")
            
            components.html("""<script>setTimeout(function() { const inputs = window.parent.document.querySelectorAll('input[type="password"]:not([disabled])'); if (inputs.length > 0) { inputs[0].focus(); } }, 150);</script>""", height=0, width=0)

            msg_box = st.empty()
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1: save_btn = st.button("💾 비밀번호 저장", type="primary", use_container_width=True)
            with col2:
                if st.button("닫기", type="secondary", use_container_width=True):
                    st.session_state["pw_step_unlocked"] = False
                    st.rerun()
                    
            if save_btn:
                if not new_pw or new_pw != new_pw_confirm: msg_box.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold;'>❌ 새 비밀번호가 비어있거나 서로 일치하지 않습니다.</p>", unsafe_allow_html=True)
                elif new_pw == st.session_state.get("logged_teacher_pw", ""): msg_box.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold;'>❌ 현재 사용 중인 비밀번호와 동일합니다.</p>", unsafe_allow_html=True)
                else:
                    df_tc = load_sheet_to_df("teacher_accounts")
                    if not df_tc.empty and "교사_ID" in df_tc.columns:
                        idx = df_tc[df_tc["교사_ID"] == st.session_state["logged_teacher_id"]].index
                        if len(idx) > 0:
                            df_tc.loc[idx[0], "비밀번호"] = new_pw
                            if save_df_to_sheet("teacher_accounts", df_tc):
                                msg_box.markdown("<p style='color: #10b981; font-size: 13px; font-weight: bold;'>🎉 비밀번호가 변경되었습니다! 다음 접속 시 새 비밀번호를 사용하세요.</p>", unsafe_allow_html=True)
                                st.session_state["logged_teacher_pw"] = new_pw
                            else: msg_box.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold;'>❌ 구글 시트 저장에 실패했습니다.</p>", unsafe_allow_html=True)
                        else: msg_box.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold;'>❌ 명단에서 계정을 찾을 수 없습니다.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("닫기", type="secondary", use_container_width=True):
                st.session_state["pw_step_unlocked"] = False
                st.rerun()

    elif edit_mode == "📚 담당과목 변경":
        if st.session_state["logged_teacher_id"] == "admin":
            st.warning("⚠️ 최고관리자(admin) 계정은 마스터 모든 과목 열람 권한이 고정되어 있습니다.")
            if st.button("닫기", type="secondary", use_container_width=True): st.rerun()
        else:
            curr_subs_str = ", ".join(st.session_state.get("allowed_subjects", []))
            new_subs_str = st.text_input("담당 과목 변경 (여러 과목은 콤마[,]로 분리)", value=curr_subs_str, placeholder="예: 정보, 수학")
            msg_box_sub = st.empty()
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1: save_sub_btn = st.button("💾 과목 저장하기", type="primary", use_container_width=True)
            with col2:
                if st.button("닫기", type="secondary", use_container_width=True): st.rerun()
                    
            if save_sub_btn:
                if not new_subs_str.strip(): msg_box_sub.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold;'>❌ 담당 과목을 최소 1개 이상 입력하세요.</p>", unsafe_allow_html=True)
                else:
                    df_tc = load_sheet_to_df("teacher_accounts")
                    if not df_tc.empty and "교사_ID" in df_tc.columns:
                        idx = df_tc[df_tc["교사_ID"] == st.session_state["logged_teacher_id"]].index
                        if len(idx) > 0:
                            df_tc.loc[idx[0], "담당_과목"] = new_subs_str.strip()
                            if save_df_to_sheet("teacher_accounts", df_tc):
                                st.session_state["allowed_subjects"] = [s.strip() for s in new_subs_str.split(",") if s.strip()]
                                msg_box_sub.markdown("<p style='color: #10b981; font-size: 13px; font-weight: bold;'>🎉 담당 과목이 성공적으로 수정되었습니다! (즉시 반영됨)</p>", unsafe_allow_html=True)
                            else: msg_box_sub.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold;'>❌ 구글 시트 저장 실패</p>", unsafe_allow_html=True)
                        else: msg_box_sub.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold;'>❌ 명단에서 계정을 찾을 수 없습니다.</p>", unsafe_allow_html=True)

@st.dialog("➕ 전학생 / 개별 학생 추가")
def show_add_student_dialog(sf_id, current_df):
    st.markdown("새로 명단에 추가할 학생의 기본 정보를 입력해 주세요.")
    with st.form("add_student_form", border=False):
        c1, c2, c3 = st.columns(3)
        with c1: new_ban = st.text_input("반 (숫자만)", placeholder="예: 1")
        with c2: new_num = st.text_input("번호 (숫자만)", placeholder="예: 15")
        with c3: new_name = st.text_input("이름", placeholder="예: 홍길동")
        
        c4, c5 = st.columns(2)
        with c4: new_email = st.text_input("학교 이메일", placeholder="예: student@school.kr")
        with c5: new_pw = st.text_input("초기 비밀번호", placeholder="예: 1234")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("💾 이 학생 명단에 추가하기", use_container_width=True)
        
        if submit_btn:
            if not new_ban or not new_num or not new_name: st.error("❌ 반, 번호, 이름은 필수 입력 항목입니다.")
            else:
                new_row = {"반": new_ban.strip(), "번호": new_num.strip(), "이름": new_name.strip()}
                if "school_email" in current_df.columns: new_row["school_email"] = new_email.strip()
                elif "학교 이메일" in current_df.columns: new_row["학교 이메일"] = new_email.strip()
                elif "이메일" in current_df.columns: new_row["이메일"] = new_email.strip()
                
                if "비밀번호" in current_df.columns: new_row["비밀번호"] = new_pw.strip()
                if "성적조회 횟수" in current_df.columns: new_row["성적조회 횟수"] = "0"
                if "최종 확인일시" in current_df.columns: new_row["최종 확인일시"] = "-"
                
                for col in current_df.columns:
                    if col not in new_row: new_row[col] = ""
                        
                updated_df = pd.concat([current_df, pd.DataFrame([new_row])], ignore_index=True)
                if save_df_to_sheet(sf_id, updated_df):
                    st.success("🎉 성공적으로 추가되었습니다! 창을 닫고 표를 확인하세요.")
                    st.rerun()
                else: st.error("❌ 구글 시트 저장에 실패했습니다.")

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict, sf_id, student_row_idx, current_df):
    st.markdown(f"<div><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True)
    st.table(pd.DataFrame(scores_dict))
    if "has_counted" not in st.session_state:
        try: current_count = int(current_df.loc[student_row_idx, "성적조회 횟수"]) if "성적조회 횟수" in current_df.columns and not pd.isna(current_df.loc[student_row_idx, "성적조회 횟수"]) else 0
        except: current_count = 0
        current_df.loc[student_row_idx, "성적조회 횟수"] = str(current_count + 1)
        current_df.loc[student_row_idx, "최종 확인일시"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_df_to_sheet(sf_id, current_df)
        st.session_state["has_counted"] = True
    if st.button("닫기", type="secondary", use_container_width=True, key="dialog_close_button_unique"):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.session_state.clear()
        st.rerun()

def get_active_databases():
    active_list = []
    if gc is None: return active_list
    try:
        sh = gc.open(SPREADSHEET_NAME)
        for wks in sh.worksheets():
            if wks.title.startswith("cfg_"):
                match = re.search(r"cfg_([A-Za-z0-9_가-힣]+)_([1-3])Grade", wks.title)
                if match: active_list.append({"subject": match.group(1).replace("_", " "), "grade": f"{match.group(2)}학년", "semester": "2026학년도 1학기"})
    except: pass
    return active_list

# 세션 변수 초기화
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "student_logged_in" not in st.session_state: st.session_state["student_logged_in"] = False
if "logged_student_id" not in st.session_state: st.session_state["logged_student_id"] = ""
if "logged_student_pw" not in st.session_state: st.session_state["logged_student_pw"] = ""
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = ""
if "logged_teacher_pw" not in st.session_state: st.session_state["logged_teacher_pw"] = ""
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = ""
if "allowed_subjects" not in st.session_state: st.session_state["allowed_subjects"] = []

SUBJECT_MAP = load_master_subjects()

# =========================================================================
# 🔓 [1단계] 클린 통합 로그인 시스템
# =========================================================================
if not st.session_state["admin_logged_in"] and not st.session_state["student_logged_in"]:
    with st.container():
        with st.form("master_unified_form"):
            st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
            
            login_mode = st.radio("접속 모드", ["학생", "교사"], horizontal=True, label_visibility="collapsed", key="pure_system_role_radio")
            user_id_input = st.text_input("ID", placeholder="ID를 입력하세요", label_visibility="collapsed", key="pure_user_id_field")
            user_pw_input = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed", key="pure_user_pw_field")
            
            b_col1, b_col2, b_col3 = st.columns([1.0, 1.8, 1.0])
            with b_col2: submit_active = st.form_submit_button("로그인", use_container_width=True)
            
            if submit_active:
                clean_id = str(user_id_input).strip()
                clean_pw = str(user_pw_input).strip()
                
                if login_mode == "학생":
                    if not clean_id or not clean_pw: st.error("❌ 학생 ID와 비밀번호를 모두 입력하세요.")
                    else:
                        active_dbs = get_active_databases()
                        if not active_dbs: st.error("❌ 현재 개설된 과목 성적 대장이 시트에 존재하지 않습니다.")
                        else:
                            first_db = active_dbs[0]
                            _, sf_id = get_sheet_names_id(first_db['subject'], first_db['grade'].replace("학년",""), first_db['semester'])
                            df_st = load_sheet_to_df(sf_id)
                            
                            if df_st.empty: st.error("❌ 성적 데이터베이스 시트가 비어있습니다.")
                            else:
                                id_col = "school_email" if "school_email" in df_st.columns else ("이름" if "이름" in df_st.columns else None)
                                if not id_col or "비밀번호" not in df_st.columns: st.error("❌ 성적 대장 시트의 열 이름 구성이 올바르지 않습니다.")
                                else:
                                    id_match = df_st[df_st[id_col] == clean_id]
                                    if id_match.empty: st.error("❌ 존재하지 않는 학생 ID입니다.")
                                    else:
                                        pw_match = id_match[id_match["비밀번호"] == clean_pw]
                                        if pw_match.empty: st.error("❌ 비밀번호가 일치하지 않습니다.")
                                        else:
                                            st.session_state["student_logged_in"] = True
                                            st.session_state["logged_student_id"] = clean_id
                                            st.session_state["logged_student_pw"] = clean_pw
                                            st.rerun()
                                            
                elif login_mode == "교사":
                    if clean_id == "admin" and clean_pw == "1234":
                        st.session_state["admin_logged_in"] = True
                        st.session_state["logged_teacher_id"] = "admin"
                        st.session_state["logged_teacher_pw"] = "1234"
                        st.session_state["teacher_name"] = "최고관리자"
                        st.session_state["allowed_subjects"] = ["마스터"]
                        st.rerun()
                    else:
                        df_tc = load_sheet_to_df("teacher_accounts")
                        if df_tc.empty: st.error("❌ 교사 계정 명단을 불러오지 못했습니다. 구글 시트 연결 상태를 확인하세요.")
                        else:
                            if "교사_ID" not in df_tc.columns or "비밀번호" not in df_tc.columns: st.error("❌ 구글 시트 첫 번째 줄 열 이름이 '교사_ID'와 '비밀번호'인지 확인해 주세요.")
                            else:
                                id_match = df_tc[df_tc['교사_ID'] == clean_id]
                                if id_match.empty: st.error("❌ 존재하지 않는 교사 ID입니다.")
                                else:
                                    pw_match = id_match[id_match['비밀번호'] == clean_pw]
                                    if pw_match.empty: st.error("❌ 비밀번호가 일치하지 않습니다.")
                                    else:
                                        row = pw_match.iloc[0]
                                        st.session_state["admin_logged_in"] = True
                                        st.session_state["logged_teacher_id"] = clean_id
                                        st.session_state["logged_teacher_pw"] = clean_pw
                                        st.session_state["teacher_name"] = str(row.get('교사_성명', '교사')).strip()
                                        t_sub = str(row.get('담당_과목', '')).strip()
                                        st.session_state["allowed_subjects"] = [s.strip() for s in t_sub.split(",") if s.strip()]
                                        st.rerun()

    st.markdown("<div class='footer-container'><div class='footer-text'>Designed & Developed by User & AI Creator</div></div>", unsafe_allow_html=True)

# =========================================================================
# 🎓 [2단계-A] 학생 대시보드
# =========================================================================
elif st.session_state["student_logged_in"]:
    st.markdown(f"<h2>수행평가 점수 확인 시스템 <span style='font-size:16px; color:#3b82f6;'>(학생 모드)</span></h2>", unsafe_allow_html=True)
    if st.button("🚪 로그아웃", key="student_logout_btn"):
        st.session_state.clear()
        st.rerun()
    st.write(f"👤 접속 이메일: **{st.session_state['logged_student_id']}**")
    st.markdown("---")
    
    active_dbs = get_active_databases()
    if not active_dbs: st.warning("현재 평가 데이터베이스에 활성화된 과목 파티션이 존재하지 않습니다.")
    else:
        opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']})" for d in active_dbs]
        sel_s = st.selectbox("조회할 교과과정 선택", opts_s, key="student_subject_select")
        
        if sel_s != "과목 및 학기를 선택하세요.":
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 나의 수행평가 성적 실시간 검증", type="primary", use_container_width=True, key="student_verify_score_btn"):
                db = active_dbs[opts_s.index(sel_s)-1]
                cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                config_df = load_sheet_to_df(cf_id)
                config = config_df.iloc[0].to_dict() if not config_df.empty else None
                
                if config:
                    df_st = load_sheet_to_df(sf_id)
                    if not df_st.empty:
                        st_id = st.session_state["logged_student_id"]
                        st_pw = st.session_state["logged_student_pw"]
                        id_col = "school_email" if "school_email" in df_st.columns else "이름"
                        res = df_st[(df_st[id_col] == st_id) & (df_st['비밀번호'] == st_pw)]
                        if not res.empty:
                            idx = res.index[0]
                            st_name = res.iloc[0].get('이름', '학생')
                            scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                            show_result_dialog(st_name, scores, sf_id, idx, df_st)
                        else: st.error("❌ 일치하는 성적 데이터가 없습니다.")

# =========================================================================
# 🔒 [2단계-B] 교사 대시보드
# =========================================================================
elif st.session_state["admin_logged_in"]:
    with st.sidebar:
        st.markdown('<span class="sidebar-title">📋 교사 메뉴</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="user-info">👤 {st.session_state["teacher_name"]} 선생님 접속 중</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        # 🚨 [순서 변경] 개인별 성적 입력 ➡️ 학생 정보 관리 순으로 메뉴 재배치!
        menu_selection = st.radio("메뉴 선택", [
            "▶ 학생 조회 현황 모니터링", 
            "▶ 개인별 성적 입력", 
            "▶ 학생 정보 관리", 
            "▶ 평가 대상 과목 구성", 
            "▶ 성적 전체 일괄 업로드(CSV)"
        ], label_visibility="collapsed", key="teacher_sidebar_unique_menu_selector_2026")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.button("👤 내 정보 수정", type="secondary", use_container_width=True, key="open_profile_popup_btn"):
            st.session_state["pw_step_unlocked"] = False
            show_profile_popup_dialog()
            
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        
        if st.button("🚪 로그아웃", type="secondary", use_container_width=True, key="teacher_logout_btn_unique"):
            st.session_state.clear()
            st.rerun()

    st.markdown(f"<h2>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
    st.write(f"현재 위치: 교사 모드 > **{menu_selection}**")
    st.markdown("<div style='text-align:center; height: 5px;'></div>", unsafe_allow_html=True)

    # 1. 학생 조회 현황 모니터링
    if menu_selection == "▶ 학생 조회 현황 모니터링":
        with st.container(border=True):
            st.markdown("<h3>📊 학생별 조회 이력 및 성적 현황 모니터링</h3>", unsafe_allow_html=True)
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]: registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
            if not registered_dbs: st.warning("⚠️ 현재 개설된 과목이 없습니다.")
            else:
                col_sub, col_class = st.columns(2)
                with col_sub:
                    selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                    selected_db_str = st.selectbox("📂 대상 교과 선택", options=selector_options, key="t_sub_select_1_unique")
                    chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                cf_id, sf_id = get_sheet_names_id(chosen_db['subject'], chosen_db['grade'].replace("학년",""), chosen_db['semester'])
                db_df = load_sheet_to_df(sf_id)
                cfg_df = load_sheet_to_df(cf_id)
                with col_class:
                    class_options = ["전체 학급 보기"]
                    if not db_df.empty and "반" in db_df.columns: class_options = ["전체 학급 보기"] + [f"{x}반" for x in sorted(db_df['반'].unique())]
                    selected_class = st.selectbox("🎯 필터링할 학급 선택", options=class_options, key="t_class_select_1_unique")
                if not db_df.empty:
                    render_df = db_df.copy()
                    if selected_class != "전체 학급 보기" and "반" in render_df.columns: render_df = render_df[render_df['반'].astype(int) == int(selected_class.replace("반",""))]
                    if not cfg_df.empty:
                        cfg_dict = cfg_df.iloc[0].to_dict()
                        cnt = int(cfg_dict.get('항목개수', 3))
                        score_headers = [cfg_dict.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(cnt)]
                    else: score_headers = []
                    
                    display_cols = ["반", "번호", "이름"]
                    # 이메일 유연한 탐색
                    for col in ["학교 이메일", "school_email", "이메일"]:
                        if col in render_df.columns: display_cols.append(col); break
                        
                    display_cols.extend(score_headers)
                    display_cols.extend(["성적조회 횟수", "최종 확인일시"])
                    st.dataframe(render_df[[c for c in display_cols if c in render_df.columns]].fillna("-"), use_container_width=True, hide_index=True)

    # 🚨 2. 개인별 성적 입력 (학생 기본정보 잠금, 오직 성적만 수정)
    elif menu_selection == "▶ 개인별 성적 입력":
        with st.container(border=True):
            st.markdown("<h3>📝 개인별 성적 데이터 입력</h3>", unsafe_allow_html=True)
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]: registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
            if not registered_dbs: st.warning("⚠️ 권한이 있는 과목이 없습니다.")
            else:
                col_sub_ed, col_class_ed = st.columns(2)
                with col_sub_ed:
                    selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                    selected_db_str = st.selectbox("📂 관리할 교과 선택", options=selector_options, key="t_sub_select_2_unique")
                    chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                cf_id, sf_id = get_sheet_names_id(chosen_db['subject'], chosen_db['grade'].replace("학년",""), chosen_db['semester'])
                db_df = load_sheet_to_df(sf_id)
                cfg_df = load_sheet_to_df(cf_id)
                with col_class_ed:
                    class_options_ed = ["전체"]
                    if not db_df.empty and "반" in db_df.columns: class_options_ed = ["전체"] + [f"{x}반" for x in sorted(db_df['반'].unique())]
                    selected_class_ed = st.selectbox("👥 학반 필터링", options=class_options_ed, key="t_class_select_2_unique")
                if not db_df.empty:
                    if not cfg_df.empty:
                        cfg_dict = cfg_df.iloc[0].to_dict()
                        cnt = int(cfg_dict.get('항목개수', 3))
                        score_headers = [cfg_dict.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(cnt)]
                    else: score_headers = []
                    
                    display_cols = ["반", "번호", "이름"]
                    display_cols.extend(score_headers) 
                    
                    valid_cols = [c for c in display_cols if c in db_df.columns]
                    if selected_class_ed != "전체" and "반" in db_df.columns:
                        filtered_idx = db_df[db_df["반"].astype(int) == int(selected_class_ed.replace("반", ""))].index
                        edit_target_df = db_df.loc[filtered_idx, valid_cols]
                    else:
                        filtered_idx = db_df.index
                        edit_target_df = db_df[valid_cols]
                        
                    # 🚨 성적 입력 모드: 반, 번호, 이름은 잠금 처리하여 보호
                    edited_df = st.data_editor(
                        edit_target_df, 
                        use_container_width=True, 
                        num_rows="fixed", 
                        disabled=["반", "번호", "이름"], 
                        hide_index=True, 
                        key="teacher_data_editor_grid_system"
                    )
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    bc1, bc2 = st.columns([4.2, 1.2])
                    with bc2:
                        if st.button("💾 성적 저장하기", use_container_width=True, type="primary", key="save_edit_btn_unique"):
                            for idx_pos, row_idx in enumerate(filtered_idx):
                                for col in edited_df.columns: db_df.loc[row_idx, col] = edited_df.iloc[idx_pos][col]
                            if save_df_to_sheet(sf_id, db_df): st.success("🎉 성적이 완벽하게 저장되었습니다!"); st.rerun()

    # 🚨 3. 학생 정보 관리 (성적 제외, 학생 추가 및 기본 정보만 수정)
    elif menu_selection == "▶ 학생 정보 관리":
        with st.container(border=True):
            st.markdown("<h3>📇 학생 기본 정보 관리</h3>", unsafe_allow_html=True)
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]: registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
            if not registered_dbs: st.warning("⚠️ 권한이 있는 과목이 없습니다.")
            else:
                col_sub_ed, col_class_ed = st.columns(2)
                with col_sub_ed:
                    selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                    selected_db_str = st.selectbox("📂 관리할 교과 선택", options=selector_options, key="t_sub_select_info_unique")
                    chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                cf_id, sf_id = get_sheet_names_id(chosen_db['subject'], chosen_db['grade'].replace("학년",""), chosen_db['semester'])
                db_df = load_sheet_to_df(sf_id)
                with col_class_ed:
                    class_options_ed = ["전체"]
                    if not db_df.empty and "반" in db_df.columns: class_options_ed = ["전체"] + [f"{x}반" for x in sorted(db_df['반'].unique())]
                    selected_class_ed = st.selectbox("👥 학반 필터링", options=class_options_ed, key="t_class_select_info_unique")
                
                if not db_df.empty:
                    display_cols = ["반", "번호", "이름"]
                    # 이메일, 비밀번호 이름 유연하게 찾기
                    for col in ["학교 이메일", "school_email", "이메일"]:
                        if col in db_df.columns: display_cols.append(col); break
                    for col in ["비밀번호", "비번"]:
                        if col in db_df.columns: display_cols.append(col); break
                    
                    valid_cols = [c for c in display_cols if c in db_df.columns]
                    if selected_class_ed != "전체" and "반" in db_df.columns:
                        filtered_idx = db_df[db_df["반"].astype(int) == int(selected_class_ed.replace("반", ""))].index
                        edit_target_df = db_df.loc[filtered_idx, valid_cols]
                    else:
                        filtered_idx = db_df.index
                        edit_target_df = db_df[valid_cols]
                        
                    # 학생 정보 관리는 잠금장치(disabled) 없이 자유롭게 수정 가능!
                    edited_df = st.data_editor(
                        edit_target_df, 
                        use_container_width=True, 
                        num_rows="fixed", 
                        hide_index=True, 
                        key="teacher_info_editor_grid_system"
                    )
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    bc1, bc2, bc3 = st.columns([3.6, 1.2, 1.2])
                    with bc2:
                        if st.button("➕ 학생 개별 추가", use_container_width=True, type="secondary", key="add_student_dialog_btn"):
                            show_add_student_dialog(sf_id, db_df)
                    with bc3:
                        if st.button("💾 학생 정보 저장", use_container_width=True, type="primary", key="save_info_btn_unique"):
                            for idx_pos, row_idx in enumerate(filtered_idx):
                                for col in edited_df.columns: db_df.loc[row_idx, col] = edited_df.iloc[idx_pos][col]
                            if save_df_to_sheet(sf_id, db_df): st.success("🎉 학생 기본 정보가 수정되었습니다!"); st.rerun()

    # 4. 평가 대상 과목 구성
    elif menu_selection == "▶ 평가 대상 과목 구성":
        with st.container(border=True):
            st.markdown("<h3>⚙️ 1. 평가 과목 설정</h3>", unsafe_allow_html=True)
            st.caption("평가 대상 과목과 학기를 연동하세요.")
            
            r1, r2 = st.columns(2)
            with r1: sel_g = st.selectbox("교과군 선택", options=["인문·사회군", "수리·과학군", "예체능군"], key="cfg_group_select_unique")
            with r2: sel_gr = st.selectbox("학년 지정", options=["1학년", "2학년", "3학년"], key="cfg_grade_select_unique")
            
            r3, r4 = st.columns(2)
            with r3: final_sub = st.selectbox("세부 과목", options=SUBJECT_MAP.get(sel_g, ["국어"]), key="cfg_sub_select_unique")
            with r4: sel_se = st.selectbox("학기 선택", options=["2026학년도 1학기", "2026학년도 2학기"], key="cfg_sem_select_unique")
            
            st.markdown("<hr style='border: 1px dashed #cbd5e1; margin: 25px 0;'>", unsafe_allow_html=True)
            
            st.markdown("<h3>🎯 2. 수행평가 항목 구성</h3>", unsafe_allow_html=True)
            item_count = st.selectbox("평가 반영 항목 개수 선택", [1, 2, 3, 4, 5], index=2, key="cfg_item_cnt_select_unique")
            
            item_titles = []
            cols_items = st.columns(item_count)
            for i in range(item_count):
                with cols_items[i]:
                    t_in = st.text_input(f"수행평가 항목 {i+1} 제목", value=f"수행평가_{i+1}", key=f"pure_item_title_{i}_unique")
                    item_titles.append(t_in.strip())
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            bc1, bc2 = st.columns([4.2, 1.2]) 
            with bc2:
                if st.button("💾 기본 설정 저장", type="primary", use_container_width=True, key="make_partition_btn_unique"):
                    if "마스터" not in st.session_state["allowed_subjects"] and final_sub not in st.session_state["allowed_subjects"]:
                        st.error(f"❌ 권한 오류: 선생님은 [{final_sub}] 과목에 대한 개설 권한이 없습니다.")
                    else:
                        cf_id, sf_id = get_sheet_names_id(final_sub, sel_gr.replace("학년",""), sel_se)
                        config_df = pd.DataFrame([{"선택된반 목록": "1,2,3", "항목개수": item_count, **{f"항목{k+1}_이름": item_titles[k] for k in range(item_count)}}])
                        if save_df_to_sheet(cf_id, config_df): st.success("✅ 기본 설정 저장 완료!")

    # 5. 성적 전체 일괄 업로드(CSV)
    elif menu_selection == "▶ 성적 전체 일괄 업로드(CSV)":
        with st.container(border=True):
            st.markdown("<h3>📥 전체 일괄 성적 대장 CSV 업로드</h3>", unsafe_allow_html=True)
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]: registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
            if not registered_dbs: st.warning("개설된 과목이 없습니다.")
            else:
                selected_db_str = st.selectbox("📂 성적 연동 과목 선택", options=[f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs], key="csv_db_select_unique")
                chosen_db = registered_dbs[[f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs].index(selected_db_str)]
                cf_id, sf_id = get_sheet_names_id(chosen_db['subject'], chosen_db['grade'].replace("학년",""), chosen_db['semester'])
                
                template_df = pd.DataFrame({
                    "반": ["1", "1", "2"],
                    "번호": ["1", "2", "1"],
                    "이름": ["홍길동", "이영희", "강백호"],
                    "학교 이메일": ["hgd@school.kr", "lyh@school.kr", "kbh@school.kr"],
                    "비밀번호": ["1234", "1234", "1234"],
                    "수행평가1": ["20", "19", "15"],
                    "수행평가2": ["18", "20", "15"],
                    "수행평가3": ["25", "22", "20"],
                    "성적조회 횟수": ["0", "0", "0"],
                    "최종 확인일시": ["-", "-", "-"]
                })
                csv_buffer = template_df.to_csv(index=False).encode('utf-8-sig') 
                
                st.markdown("💡 **양식을 다운로드하여 성적을 업로드하세요.**")
                st.download_button(
                    label="📥 일괄 업로드용 성적 양식(.CSV) 다운로드",
                    data=csv_buffer,
                    file_name="성적일괄업로드_양식.csv",
                    mime="text/csv",
                    type="secondary"
                )
                st.markdown("<br>", unsafe_allow_html=True)
                
                up_f = st.file_uploader("성적 대장 마스터 CSV 파일 업로드", type="csv", key="csv_file_uploader_unique")
                if up_f:
                    df_up = pd.read_csv(up_f, encoding='cp949')
                    df_up.columns = [c.strip() for c in df_up.columns]
                    if "학교 이메일" not in df_up.columns and "school_email" not in df_up.columns: df_up["학교 이메일"] = ""
                    if "성적조회 횟수" not in df_up.columns: df_up["성적조회 횟수"] = "0"
                    if "최종 확인일시" not in df_up.columns: df_up["최종 확인일시"] = "-"
                    if save_df_to_sheet(sf_id, df_up): st.success("🎉 클라우드 데이터베이스 미러링 마감 성공!")