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

# --- 앱 기본 세팅 ---
st.set_page_config(page_title="수행평가 결과 시스템 v7", layout="wide")

# =========================================================================
# 🎯 [스타일 결정판] 2번 그림처럼 완벽하게 아담한 상자 안에 모든 색상 가두기
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
        div[data-testid="stHeader"] { display: none !important; }
        
        /* 🚨 상단 유령 사각형 공백 버그 무조건 완전 파괴 */
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
        
        /* 🎯 [2번 그림 100% 일치] 모든 내용과 알림 색상을 가로 550px 하얀색 상자 안으로 완벽 구속 */
        .universal-compact-card {
            max-width: 550px !important;
            margin: 50px auto 40px auto !important;
            background-color: #ffffff !important;
            padding: 35px !important;
            border-radius: 14px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.04) !important;
        }
        
        /* 상자 내부 알림 메시지(성공/에러)가 상자 밖으로 퍼지지 않게 카드 안쪽으로 100% 구속 */
        .universal-compact-card div[data-testid="stNotification"],
        .universal-compact-card .stAlert {
            max-width: 100% !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            border-radius: 8px !important;
        }
        
        /* 내부 Form 기본 테두리 무효화 */
        .universal-compact-card div[data-testid="stForm"] {
            border: none !important;
            padding: 0px !important;
            box-shadow: none !important;
        }
        
        /* 교사용 제어판 단추 슬림화 및 정렬선 맞춤 */
        div.stButton > button[key="outer_teacher_btn"] {
            width: fit-content !important;
            min-width: auto !important;
            padding: 4px 14px !important;
            font-size: 14px !important;
            border-radius: 6px !important;
            border: 1px solid #cbd5e1 !important;
            color: #475569 !important;
            background-color: #ffffff !important;
        }
        
        /* 조회 버튼 빨간색 최적화 */
        div.stButton > button[kind="primary"] {
            background-color: #ef4444 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            padding: 10px 0px !important;
            border-radius: 6px !important;
        }
        
        h2 { font-size: 22px !important; color: #0f172a !important; font-weight: 800 !important; margin: 0 0 15px 0 !important; }
        h3 { font-size: 17px !important; font-weight: 700 !important; color: #1e293b !important; margin-bottom: 8px !important; }
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

# --- 내부 화면 페이지 제어 상태 관리 ---
if "page_status" not in st.session_state:
    st.session_state["page_status"] = "student_main"

if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

is_teacher_layout = (st.session_state["page_status"] == "teacher_main")
is_logged_in = st.session_state["admin_logged_in"]

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년을 선택하세요.", "1학년", "2학년", "3학년"]
CURRENT_ADMIN_PW = load_admin_password()


# ==========================================
# 🚀 진짜 최종 화면 출력 파트
# ==========================================

if st.session_state["page_status"] == "student_main":
    
    # 🎯 [선생님 요청 핵심] 가로 550px 아담하고 예쁜 흰색 전용 카드 상자 열기 (모든 것은 이 안에 가둠)
    st.markdown("<div class='universal-compact-card'>", unsafe_allow_html=True)
    
    st.markdown("<h2>🎒 수행평가 성적 확인 시스템</h2>", unsafe_allow_html=True)
    
    # 1번 그림 양식: 타이틀 바로 밑에 이쁘게 안착하는 버튼
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
                # 🎯 안내 메시지 초록색 박스도 이 상자 너비(550px) 안에 이쁘게 가둬짐
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
                                
    st.markdown("</div>", unsafe_allow_html=True) # 🎯 550px 카드 상자 닫기

elif st.session_state["page_status"] == "teacher_auth":
    st.title("🛡️ 교과 관리자 인증")
    if st.button("🎒 학생 화면"):
        st.session_state["page_status"] = "student_main"
        st.rerun()

elif st.session_state["page_status"] == "teacher_main":
    st.title("⚙️ 교과 제어 센터")
    if st.button("🎒 학생 화면 (로그아웃)"):
        st.session_state["page_status"] = "student_main"
        st.session_state["admin_logged_in"] = False
        st.rerun()