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

# --- 🎯 layout 설정을 centered로 고정하여 기본 프레임 최적화 ---
st.set_page_config(page_title="수행평가 결과 시스템", layout="centered")

# =========================================================================
# 🎯 [CSS 최적화] 유령 사각형 차단 및 디자인 양식
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
        div[data-testid="stHeader"] { display: none !important; background: transparent !important; }
        
        /* 하단 잉여 공간(푸터) 완전 제거 및 전체 화면 위로 끌어올리기 */
        footer { display: none !important; }
        .block-container {
            padding-top: 3rem !important; 
            padding-bottom: 1rem !important; 
        }
        
        div.element-container:has(iframe) { display: none !important; }
        iframe { display: none !important; height: 0px !important; }
        
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0px !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }
        
        /* 교사용 제어판 버튼 글씨 크기(12px) 및 패딩 축소 */
        div.stButton > button[key="outer_teacher_btn"],
        div.stButton > button[key="outer_student_btn"],
        div.stButton > button[key="outer_logout_btn"] {
            width: fit-content !important;
            min-width: auto !important;
            padding: 3px 12px !important;
            font-size: 12px !important;
            border-radius: 6px !important;
            border: 1px solid #cbd5e1 !important;
            color: #475569 !important;
            background-color: #ffffff !important;
        }
        
        div.stButton:has(button[key="outer_teacher_btn"]) {
            display: flex;
            justify-content: flex-end;
        }
        
        div.stButton > button[kind="primary"] {
            background-color: #ef4444 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            padding: 10px 0px !important;
            border-radius: 6px !important;
        }
        
        h2 { font-size: 24px !important; color: #0f172a !important; font-weight: 800 !important; margin: 20px 0 10px 0 !important; }
        h4 { font-size: 18px !important; font-weight: 700 !important; color: #1e293b !important; margin-bottom: 8px !important; }
    </style>
""", unsafe_allow_html=True)

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

# 🎯 성적 조회 결과를 보여주는 팝업 모달 함수
@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict):
    st.markdown(f"<div style='margin-bottom:15px;'><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True)
    st.table(pd.DataFrame(scores_dict))
    
    if st.button("확인 후 닫기", use_container_width=True, type="primary"):
        # 사이트 세션을 완전히 지워 초기 화면으로 되돌림
        st.session_state.clear()
        st.rerun()

# --- 내부 화면 페이지 제어 상태 초기화 ---
if "page_status" not in st.session_state:
    st.session_state["page_status"] = "student_main"

if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

if "show_pw_edit_section" not in st.session_state:
    st.session_state["show_pw_edit_section"] = False

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년을 선택하세요.", "1학년", "2학년", "3학년"]
CURRENT_ADMIN_PW = load_admin_password()


# ==========================================
# 🔄 독점 화면 분기 구동 영역
# ==========================================

# ------------------------------------------
# 🎒 1. 학생용 개인 성적 조회 첫 화면
# ------------------------------------------
if st.session_state["page_status"] == "student_main":
    
    st.markdown("""
        <style>
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #e2e8f0 !important;
            padding: 35px 40px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            background-color: #ffffff !important;
            max-width: 500px !important; 
            margin: 0px auto 20px auto !important; 
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 교사용 제어판 버튼
    col_empty, col_btn = st.columns([3, 1])
    with col_btn:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if st.button("🔓 교사용 제어판", key="outer_teacher_btn"):
            st.session_state["page_status"] = "teacher_auth"
            st.rerun()
            
    active_dbs = get_active_databases()
    
    # 학생용 카드 컨테이너
    with st.container(border=True):
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 5px 0px;'>🎒 수행평가 성적 확인 시스템</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; margin: 0px 0px 10px 0px; color: #475569;'>📝 개인별 성적 조회</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:14px; color:#64748b; margin-bottom:20px;'>과목을 선택하고 본인의 정보를 정확하게 입력해 주세요.</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        
        if not active_dbs:
            st.warning("현재 등록된 성적 데이터가 없습니다.")
        else:
            # 💡 수정 포인트 1: 숫자 대신 아이콘과 세련된 소제목 적용
            st.markdown("<div style='font-size:14px; font-weight:700; color:#0f172a; margin-bottom:8px;'>🎯 대상 과목 선택</div>", unsafe_allow_html=True)
            opts_s = ["과목을 선택하세요."] + [f"📚 {d['subject']} ({d['grade']})" for d in active_dbs]
            sel_s = st.selectbox("조회할 과목 선택", opts_s, label_visibility="collapsed", key="student_select_sub")
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            
            if sel_s != "과목을 선택하세요.":
                db = active_dbs[opts_s.index(sel_s)-1]
                cf, sf = get_file_names(db['subject'], db['grade'].replace("학년",""))
                config = load_config(cf)
                
                if config:
                    st.markdown(f"<div style='background:#f1f5f9; padding:12px 15px; border-radius:8px; margin-bottom:20px; font-size:14px;'><span style='font-weight:600; color:#475569;'>선택된 교과:</span> &nbsp;🧬 <b>{config['교과명']}</b> ({config['학기통합명']})</div>", unsafe_allow_html=True)
                    
                    with st.form("login_form"):
                        # 💡 수정 포인트 2: 숫자 대신 아이콘과 세련된 소제목 적용
                        st.markdown("<div style='font-size:14px; font-weight:700; color:#0f172a; margin-bottom:8px;'>🔐 본인 인증 정보 입력</div>", unsafe_allow_html=True)
                        classes = [f"{x.strip()}반" for x in str(config['선택된반 목록']).split(",")] if '선택된반 목록' in config else ["1반"]
                        
                        c1, c2, c3 = st.columns(3)
                        with c1: b_in = st.selectbox("반", classes)
                        with c2: n_in = st.number_input("번호", 1, 50, 1)
                        with c3: name_in = st.text_input("이름", placeholder="홍길동")
                        
                        # 💡 수정 포인트 3: 비밀번호 칸을 컬럼 안에 넣어 비율 축소 (약 60% 넓이)
                        col_pw, col_empty = st.columns([3, 2])
                        with col_pw:
                            pw_in = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
                            
                        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                        
                        if st.form_submit_button("🔍 내 점수 확인하기", use_container_width=True, type="primary"):
                            df_st = load_students(sf)
                            if df_st.empty: 
                                st.error("성적 데이터가 아직 연동되지 않은 교과입니다.")
                            else:
                                res = df_st[(df_st['반']==int(b_in.replace("반",""))) & (df_st['번호']==n_in) & (df_st['이름']==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                                if not res.empty:
                                    idx = res.index[0]
                                    
                                    scores = {}
                                    for i in range(int(config['항목개수'])):
                                        h_name = config.get(f'항목{i+1}_이름', f'항목{i+1}')
                                        if h_name in df_st.columns:
                                            scores[h_name] = [df_st.loc[idx, h_name]]
                                    
                                    if df_st.loc[idx, '확인여부'] != "확인 완료":
                                        df_st.loc[idx, '확인여부'], df_st.loc[idx, '확인시간'] = "확인 완료", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        df_st.to_csv(sf, index=False)
                                        
                                    show_result_dialog(name_in, scores)
                                else: 
                                    st.error("입력한 학생 정보 또는 비밀번호가 일치하지 않습니다.")

# ------------------------------------------
# 🛡️ 2. 교과 관리자 인증 화면 (로그인 전)
# ------------------------------------------
elif st.session_state["page_status"] == "teacher_auth":
    
    st.markdown("""
        <style>
        div[data-testid="stForm"] {
            border: 1px solid #e2e8f0 !important;
            padding: 35px 40px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            background-color: #ffffff !important;
            max-width: 450px !important;
            margin: 40px auto 20px auto !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.form("admin_login_form"):
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 5px 0px;'>⚙️ 교과 통합 관리자</h2>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 15px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:14px; color:#64748b; margin-bottom:25px; line-height: 1.5;'>여러 교과와 학년별 성적 데이터베이스를<br>스위칭하며 관리하는 공간입니다.</p>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px; font-weight:600; color:#1e293b; margin-bottom:8px;'>관리자 인증 비밀번호를 입력하세요</div>", unsafe_allow_html=True)
        admin_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력", label_visibility="collapsed")
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        if st.form_submit_button("로그인", use_container_width=True, type="primary"):
            if admin_pw == CURRENT_ADMIN_PW:
                st.session_state["admin_logged_in"] = True
                st.session_state["page_status"] = "teacher_main"
                st.rerun()
            else: 
                st.error("❌ 비밀번호가 틀렸습니다.")
                
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎒 학생 화면으로 돌아가기", key="outer_student_btn", use_container_width=True):
            st.session_state["page_status"] = "student_main"
            st.rerun()

# ------------------------------------------
# ⚙️ 3. 진짜 교사용 제어 센터 화면 (로그인 후)
# ------------------------------------------
elif st.session_state["page_status"] == "teacher_main":
    if not st.session_state["admin_logged_in"]:
        st.session_state["page_status"] = "teacher_auth"
        st.rerun()
        
    st.markdown("<h2>⚙️ 교과 제어 센터</h2>", unsafe_allow_html=True)
    if st.button("🎒 학생 화면 (로그아웃)", key="outer_logout_btn", use_container_width=True):
        st.session_state["page_status"] = "student_main"
        st.session_state["admin_logged_in"] = False
        st.rerun()