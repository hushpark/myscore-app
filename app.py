import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import glob
import re

# 파일 경로 정의
CONFIG_FILE_MAIN = "master_subjects.csv"
META_FILE = "admin_meta.csv"

# --- [보안] 암호 복잡도 검사 함수 ---
def is_strong_password(pw):
    if len(pw) < 12:
        return False, "❌ 최소 12자리 이상이어야 합니다."
    if not re.search("[a-zA-Z]", pw):
        return False, "❌ 영문자가 포함되어야 합니다."
    if not re.search("[0-9]", pw):
        return False, "❌ 숫자가 포함되어야 합니다."
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", pw):
        return False, "❌ 특수문자가 포함되어야 합니다."
    return True, "✅ 사용 가능한 안전한 암호 조건입니다."

# --- 데이터 로드/저장 함수 ---
def load_master_subjects():
    default_structure = {
        "인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"],
        "수리·과학군": ["수학", "과학", "기술·가정", "정보"],
        "예체능군": ["음악", "미술", "체육"]
    }
    if os.path.exists(CONFIG_FILE_MAIN):
        try:
            df = pd.read_csv(CONFIG_FILE_MAIN)
            for _, row in df.iterrows():
                group = row['교과군']
                sub = row['과목명']
                if group in default_structure and sub not in default_structure[group]:
                    default_structure[group].append(sub)
        except: pass
    return default_structure

def save_new_subject_to_master(group, subject):
    new_data = pd.DataFrame([{"교과군": group, "과목명": subject}])
    if os.path.exists(CONFIG_FILE_MAIN):
        try:
            df = pd.read_csv(CONFIG_FILE_MAIN)
            if not ((df['교과군'] == group) & (df['과목명'] == subject)).any():
                pd.concat([df, new_data], ignore_index=True).to_csv(CONFIG_FILE_MAIN, index=False)
        except: new_data.to_csv(CONFIG_FILE_MAIN, index=False)
    else: new_data.to_csv(CONFIG_FILE_MAIN, index=False)

def load_admin_password():
    if os.path.exists(META_FILE):
        try:
            df = pd.read_csv(META_FILE)
            return str(df.iloc[0]['password']).strip()
        except: pass
    return "1234"

def save_admin_password(new_pw):
    pd.DataFrame([{"password": str(new_pw).strip()}]).to_csv(META_FILE, index=False)

def get_file_names(subject, grade):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    return f"config_{safe_subject}_{grade}grade.csv", f"students_{safe_subject}_{grade}grade.csv"

def load_config(file):
    if os.path.exists(file):
        try: return pd.read_csv(file).iloc[0].to_dict()
        except: return None
    return None

def load_students(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

def get_active_databases():
    active_list = []
    for f in glob.glob("config_*_*grade.csv"):
        try:
            parts = f.replace("config_", "").replace("grade.csv", "").split("_")
            if len(parts) >= 2:
                active_list.append({"subject": parts[0].replace("_", " "), "grade": f"{parts[-1]}학년"})
        except: pass
    return active_list

def reset_all_data():
    for f in glob.glob("config_*") + glob.glob("students_*") + [CONFIG_FILE_MAIN, META_FILE]:
        try: os.remove(f)
        except: pass
    st.session_state.clear()
    st.rerun()

# 🎯 독립형 모달 팝업창 (교사용 모드에서만 호출되므로 자유로운 넓은 규격)
@st.dialog("🔐 관리자 암호 수정")
def password_update_dialog():
    st.markdown("<div style='padding: 5px;'></div>", unsafe_allow_html=True)
    new_pw = st.text_input("1. 새 암호 입력", type="password", key="dialog_new_pw")
    confirm_pw = st.text_input("2. 새 암호 확인", type="password", key="dialog_confirm_pw")
    
    is_valid, msg = is_strong_password(new_pw)
    
    if new_pw:
        if new_pw == confirm_pw and is_valid:
            st.markdown("<div style='background-color:#E8F5E9; border-radius:4px; padding:10px; color:#2E7D32; font-weight:500; margin-bottom:10px;'>✅ 두 암호가 완벽하게 일치합니다.</div>", unsafe_allow_html=True)
        elif confirm_pw and new_pw != confirm_pw:
            st.error("❌ 암호 확인 칸이 일치하지 않습니다.")
        else:
            st.warning(msg)
            
    st.markdown("""<div style="font-size: 13px; color: #57606a; line-height: 1.6; background: #f8f9fa; padding: 15px; border-radius: 8px;">
    <b>[안전 암호 규칙]</b><br>
    - 최소 12자 이상 필수<br>
    - 영문 + 숫자 + 특수기호 조합<br>
    - 예시: <code style='background:#eee; padding:2px 4px;'>teacher!@2026info</code>
    </div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    can_submit = is_valid and (new_pw == confirm_pw)
    
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("저장 후 적용", disabled=not can_submit, use_container_width=True, type="primary"):
            save_admin_password(new_pw)
            st.toast("🎉 암호가 변경되었습니다!")
            st.rerun()
    with b_col2:
        if st.button("수정 취소", use_container_width=True):
            st.rerun()

# --- 앱 기본 설정 ---
st.set_page_config(page_title="수행평가 결과 시스템 v7", layout="wide")

query_params = st.query_params
is_admin_mode = query_params.get("mode") == "admin"

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년을 선택하세요.", "1학년", "2학년", "3학년"]
CURRENT_ADMIN_PW = load_admin_password()


# =========================================================================
# [구조 분리] 디자인 스타일 컴포넌트 이원화 주입 구역
# =========================================================================
if not is_admin_mode:
    # 🎒 B. 학생 화면용 독립 CSS 스타일 세트 (정확히 가로 500px 구속 및 팝업 잔상 제거)
    st.markdown("""
        <style>
            .main { background-color: #f8fafc; }
            div[data-testid="stHeader"] { height: 0px !important; display:none; }
            
            /* 대화상자 잔상으로 인해 상단에 발생하던 빈 사각형 영역 강제 삭제 */
            div[data-testid="stDialog"] { display: none !important; }
            
            /* 🎯 학생 화면 전체를 500px 정중앙 전용 카드로 구속 */
            .student-card-layout {
                max-width: 500px !important;
                margin: 50px auto 0 auto !important;
                background-color: #ffffff !important;
                padding: 30px !important;
                border-radius: 14px !important;
                border: 1px solid #e2e8f0 !important;
                box-shadow: 0 12px 25px rgba(0,0,0,0.05) !important;
            }
            
            /* 💡 교사용 제어판 버튼을 글자 길이에 맞춰 축소 및 우측 라인 밀착 정렬 */
            div.stButton > button[key="go_to_admin_btn"] {
                width: fit-content !important;
                min-width: auto !important;
                padding: 3px 12px !important;
                font-size: 15px !important; /* 조회할 과목 선택 폰트 스케일과 매칭 */
                float: right !important;
                border-radius: 6px !important;
                border: 1px solid #cbd5e1 !important;
                color: #475569 !important;
                background-color: #ffffff !important;
            }
            div.stButton > button[key="go_to_admin_btn"]:hover {
                background-color: #f1f5f9 !important;
                border-color: #94a3b8 !important;
            }
            
            /* 학생 화면 내부 기본 Form 외곽선 무효화 */
            .student-card-layout div[data-testid="stForm"] {
                border: none !important;
                padding: 0px !important;
                box-shadow: none !important;
                max-width: 100% !important;
            }
            
            h2 { color: #0f172a !important; font-weight: 800 !important; font-size: 21px !important; margin: 0; }
            h3 { font-size: 16px !important; font-weight: 700 !important; color: #1e293b !important; }
        </style>
    """, unsafe_allow_html=True)
else:
    # ⚙️ A. 교사용 화면용 독립 CSS 스타일 세트 (원래의 넓고 시원한 와이드 정렬 100% 유지)
    st.markdown("""
        <style>
            div[data-testid="stHeader"] { height: 0px !important; display:none; }
            
            /* 관리자 로그인 박스 전용 스타일 (420px 고전 규격 유지) */
            .admin-center-login {
                max-width: 420px !important;
                margin: 90px auto 0 auto !important;
            }
            .admin-center-login div[data-testid="stForm"] {
                background-color: #ffffff !important; 
                border: 1px solid #e2e8f0 !important;
                padding: 35px !important;
                border-radius: 16px !important;
                box-shadow: 0 15px 35px rgba(0,0,0,0.06) !important;
                max-width: 100% !important;
            }
            
            /* 버튼 라운딩 처리 */
            div.stButton > button { border-radius: 6px !important; }
            div.stButton > button[kind="primary"] { background-color: #ef4444 !important; border:none !important; }
            
            h1 { color: #0f172a !important; font-weight: 800 !important; }
            h4 { color: #334155 !important; font-weight: 600 !important; }
        </style>
    """, unsafe_allow_html=True)


# =========================================================================
# A. 선생님 관리자 화면 분리 영역
# =========================================================================
if is_admin_mode:
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    # A-1. 교과 관리자 로그인 인증 인터페이스
    if not st.session_state["admin_logged_in"]:
        st.markdown("<div class='admin-center-login'>", unsafe_allow_html=True)
        with st.form("admin_premium_login_form"):
            st.markdown("<h3 style='text-align:center; margin-bottom:15px;'>🛡️ 교과 관리자 인증</h3>", unsafe_allow_html=True)
            admin_pw = st.text_input("비밀번호를 입력하세요", type="password", placeholder="Password")
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            if st.form_submit_button("인증 및 로그인", use_container_width=True, type="primary"):
                if admin_pw == CURRENT_ADMIN_PW:
                    st.session_state["admin_logged_in"] = True
                    st.rerun()
                else: 
                    st.error("❌ 관리자 인증 비밀번호가 올바르지 않습니다.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    # A-2. 로그인 성공 시 진입하는 진짜 교사용 제어 센터 (기존 와이드 형태 완벽 유지)
    else:
        # 상단 내비게이션 바
        t_col1, t_col2, t_col3 = st.columns([5, 1.4, 1.2])
        with t_col1: 
            st.title("⚙️ 교과·학년 통합 제어 센터")
        with t_col2:
            st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
            if st.button("🔐 관리자 암호 변경", use_container_width=True): 
                password_update_dialog()
        with t_col3:
            st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
            if st.button("🎒 학생 화면", use_container_width=True):
                st.query_params.clear()
                st.session_state["admin_logged_in"] = False
                st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # [단계 1] 제어 모듈
        with st.container(border=True):
            st.markdown("#### 🛠️ [단계 1] 획기적인 교과군별 과목 지정")
            c1, c2, c3, c4 = st.columns([1, 1, 0.8, 0.7])
            with c1:
                g_opts = ["교과군을 선택하세요.", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"]
                sel_g = st.selectbox("1단계: 교과군", options=g_opts, index=st.session_state.sel_group_idx)
            with c2:
                final_sub = ""
                if sel_g == "➕ 신규 과목 개설":
                    final_sub = st.text_input("새 과목명 입력", placeholder="정보과학").strip()
                elif sel_g != "교과군을 선택하세요.":
                    s_opts = ["과목을 선택하세요."] + SUBJECT_MAP.get(sel_g, [])
                    sel_s = st.selectbox("2단계: 세부 과목", options=s_opts)
                    if sel_s != "과목을 선택하세요.": final_sub = sel_s
                else: 
                    st.selectbox("2단계: 세부 과목", ["교과군을 먼저 선택하세요."], disabled=True)
            with c3:
                sel_gr = st.selectbox("3단계: 관리 학년", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx)
                final_gr = sel_gr.replace("학년", "") if sel_gr != "학년을 선택하세요." else ""
            with c4:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("🔄 영역 활성화", use_container_width=True):
                    if final_sub and final_gr:
                        if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(