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
# 🎯 [순정 마스터 CSS] 유령 사각형 태그 요소를 원천 봉쇄하는 스타일 양식
# =========================================================================
st.markdown("""
    <style>
        /* 웹 페이지 백그라운드 정리 및 헤더 바 완전 숨김 */
        .main, [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
        div[data-testid="stHeader"] { display: none !important; background: transparent !important; }
        
        /* 🚨 서버 잔상으로 인해 발생하는 모든 유령 대화상자/프레임 요소를 브라우저단에서 영구 차단 */
        div[data-testid="stDialog"], div[role="dialog"], .stDialog, div.element-container:has(iframe) { 
            display: none !important; 
            opacity: 0 !important; 
            visibility: hidden !important; 
            height: 0px !important; 
            width: 0px !important; 
            margin: 0 !important; 
            padding: 0 !important; 
        }
        iframe { display: none !important; height: 0px !important; }
        
        /* 내장 Form 기본 테두리 무효화 */
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0px !important;
            box-shadow: none !important;
        }
        
        /* 교사용 제어판 슬림 이동 단추 스타일 지정 */
        div.stButton > button[key="outer_teacher_btn"],
        div.stButton > button[key="outer_student_btn"],
        div.stButton > button[key="outer_logout_btn"] {
            width: fit-content !important;
            min-width: auto !important;
            padding: 4px 14px !important;
            font-size: 14px !important;
            border-radius: 6px !important;
            border: 1px solid #cbd5e1 !important;
            color: #475569 !important;
            background-color: #ffffff !important;
        }
        
        /* 💡 교사용 제어판 버튼을 컨테이너 우측 끝(과목선택창 라인)으로 밀착 정렬 */
        div.stButton:has(button[key="outer_teacher_btn"]) {
            display: flex;
            justify-content: flex-end;
        }
        
        /* 확인 및 저장용 주요 단추 양식 정의 */
        div.stButton > button[kind="primary"] {
            background-color: #ef4444 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            padding: 10px 0px !important;
            border-radius: 6px !important;
        }
        
        h2 { font-size: 24px !important; color: #0f172a !important; font-weight: 800 !important; margin: 20px 0 10px 0 !important; }
        h3 { font-size: 18px !important; font-weight: 700 !important; color: #1e293b !important; margin-bottom: 8px !important; }
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
    
    # 💡 컬럼을 사용하여 제목은 왼쪽, 버튼은 오른쪽에 동일 선상으로 배치
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.markdown("<h2>🎒 수행평가 성적 확인 시스템</h2>", unsafe_allow_html=True)
    with col_btn:
        # H2 태그의 기본 마진(20px)과 높이를 맞추기 위해 상단 여백 추가
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        if st.button("🔓 교사용 제어판", key="outer_teacher_btn"):
            st.session_state["page_status"] = "teacher_auth"
            st.rerun()
            
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("### 📝 개인별 성적 조회")
    
    active_dbs = get_active_databases()
    if not active_dbs:
        st.warning("현재 등록된 성적 데이터가 없습니다.")
    else:
        opts_s = ["과목을 선택하세요."] + [f"📚 {d['subject']} ({d['grade']})" for d in active_dbs]
        sel_s = st.selectbox("조회할 과목 선택", opts_s, label_visibility="collapsed", key="student_select_sub")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        if sel_s != "과목을 선택하세요.":
            db = active_dbs[opts_s.index(sel_s)-1]
            cf, sf = get_file_names(db['subject'], db['grade'].replace("학년",""))
            config = load_config(cf)
            
            if config:
                st.success(f"🧬 **{config['교과명']}** | **{config['학기통합명']}**")
                
                with st.form("login_form"):
                    classes = [f"{x.strip()}반" for x in str(config['선택된반 목록']).split(",")] if '선택된반 목록' in config else ["1반"]
                    
                    c1, c2, c3 = st.columns(3)
                    with c1: b_in = st.selectbox("반", classes)
                    with c2: n_in = st.number_input("번호", 1, 50, 1)
                    with c3: name_in = st.text_input("이름", placeholder="홍길동")
                    
                    pw_in = st.text_input("비밀번호", type="password", placeholder="비밀번호")
                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    
                    if st.form_submit_button("🔍 내 점수 확인하기", use_container_width=True):
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
                                        
                                st.success(f"🎉 {name_in} 학생의 조회 결과입니다.")
                                st.table(pd.DataFrame(scores))
                                
                                if df_st.loc[idx, '확인여부'] != "확인 완료":
                                    df_st.loc[idx, '확인여부'], df_st.loc[idx, '확인시간'] = "확인 완료", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    df_st.to_csv(sf, index=False)
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