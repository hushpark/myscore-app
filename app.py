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

# 독립형 모달 팝업창 디자인
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
            
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("저장 후 적용", disabled=not can_submit, use_container_width=True, type="primary"):
            save_admin_password(new_pw)
            st.toast("🎉 암호가 변경되었습니다!")
            st.rerun()
    with b_col2:
        if st.button("수정 취소", use_container_width=True):
            st.rerun()

# --- 앱 설정 ---
st.set_page_config(page_title="교과 성적 제어 센터 v7", layout="wide")

st.markdown("""
    <style>
        /* 기본 배경 및 폰트 설정 */
        .main { background-color: #f8fafc; }
        div[data-testid="stHeader"] {height: 0px !important; display:none;}
        
        /* 🎯 [선생님 요청 반영] 학생 화면 메인 컨테이너 500px 고정 및 중앙 정렬 */
        .student-center-card {
            max-width: 500px !important;
            margin: 0 auto !important;
            background-color: #ffffff !important;
            padding: 30px !important;
            border-radius: 16px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 12px 30px rgba(0,0,0,0.06) !important;
        }

        /* 💡 [선생님 요청 반영] 교사용 제어판 버튼 크기 및 폰트 최적화 */
        div.stButton > button[key="go_to_admin_btn"] {
            width: fit-content !important;
            min-width: auto !important;
            padding: 4px 14px !important;
            font-size: 16px !important; /* 조회할 과목 선택 글씨 크기와 비슷하게 맞춤 */
            float: right !important;
            border-radius: 6px !important;
            border: 1px solid #cbd5e1 !important;
            color: #475569 !important;
        }
        
        /* 헤더 폰트 스타일 */
        h2 { color: #0f172a !important; font-weight: 800 !important; text-align: center; font-size: 24px !important; }
        h3 { font-size: 18px !important; font-weight: 700 !important; color: #1e293b !important; }
        
        /* 로그인 폼 전용 */
        div[data-testid="stForm"] {
            background-color: #ffffff !important; 
            border: none !important;
            padding: 0px !important;
            box-shadow: none !important; 
        }
        
        /* 관리자 로그인창은 기존 420px 유지 */
        .admin-login-box div[data-testid="stForm"] {
            max-width: 420px !important;
            margin: 0 auto !important;
            border: 1px solid #e2e8f0 !important;
            padding: 35px !important;
            border-radius: 16px !important;
            box-shadow: 0 15px 35px rgba(0,0,0,0.07) !important;
        }
    </style>
""", unsafe_allow_html=True)

query_params = st.query_params
is_admin_mode = query_params.get("mode") == "admin"

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년을 선택하세요.", "1학년", "2학년", "3학년"]
CURRENT_ADMIN_PW = load_admin_password()

# ==========================================
# A. 선생님 관리자 화면 (?mode=admin)
# ==========================================
if is_admin_mode:
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if not st.session_state["admin_logged_in"]:
        st.markdown("<div class='admin-login-box'><div style='height: 80px;'></div>", unsafe_allow_html=True)
        with st.form("admin_premium_login_form"):
            st.markdown("<h3 style='text-align:center;'>🛡️ 교과 관리자 인증</h3>", unsafe_allow_html=True)
            admin_pw = st.text_input("비밀번호", type="password", placeholder="Password")
            if st.form_submit_button("인증 및 로그인", use_container_width=True, type="primary"):
                if admin_pw == CURRENT_ADMIN_PW:
                    st.session_state["admin_logged_in"] = True
                    st.rerun()
                else: st.error("❌ 비밀번호가 틀렸습니다.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # 관리자 헤더
        t_col1, t_col2, t_col3 = st.columns([5, 1.4, 1.2])
        with t_col1: st.title("⚙️ 교과 제어 센터")
        with t_col2:
            st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
            if st.button("🔐 암호 수정", use_container_width=True): password_update_dialog()
        with t_col3:
            st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
            if st.button("🎒 학생 화면", use_container_width=True):
                st.query_params.clear()
                st.session_state["admin_logged_in"] = False
                st.rerun()

        # [단계 1] 구역
        with st.container(border=True):
            st.markdown("#### 🛠️ [단계 1] 교과군 및 과목 지정")
            c1, c2, c3, c4 = st.columns([1, 1, 0.8, 0.7])
            with c1:
                g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"]
                sel_g = st.selectbox("1. 교과군", options=g_opts)
            with c2:
                final_sub = ""
                if sel_g == "➕ 신규 과목 개설":
                    final_sub = st.text_input("새 과목명").strip()
                elif sel_g != "교과군 선택":
                    s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                    sel_s = st.selectbox("2. 세부 과목", options=s_opts)
                    if sel_s != "과목 선택": final_sub = sel_s
                else: st.selectbox("2. 세부 과목", ["선택 대기"], disabled=True)
            with c3:
                sel_gr = st.selectbox("3. 관리 학년", options=GRADE_OPTIONS)
                final_gr = sel_gr.replace("학년", "") if sel_gr != "학년을 선택하세요." else ""
            with c4:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("✅ 영역 활성화", use_container_width=True, type="primary"):
                    if final_sub and final_gr:
                        st.session_state.active_subject, st.session_state.active_grade = final_sub, final_gr
                        st.rerun()

        # 작업 상세 영역
        if "active_subject" in st.session_state and st.session_state.active_subject:
            sub, grd = st.session_state.active_subject, st.session_state.active_grade
            cf, sf = get_file_names(sub, grd)
            conf = load_config(cf)
            st.markdown(f"### 📍 현재 편집 중: [{sub}] {grd}학년")
            col_l, col_r = st.columns(2)
            with col_l:
                with st.container(border=True):
                    st.markdown("#### 평가 설정")
                    sel_t = st.selectbox("대상 학기", ["1학기", "2학기"])
                    n_item = st.number_input("항목 개수", 0, 10, 0)
            with col_r:
                with st.container(border=True):
                    st.markdown("#### 데이터 관리")
                    if st.button("💾 최종 저장", use_container_width=True, type="primary"): st.success("저장 완료")
                    if st.button("🗑️ 초기화", use_container_width=True): reset_all_data()

# ==========================================
# B. 학생 화면 (메인)
# ==========================================
else:
    # 🎯 [요청 반영] 500px 너비로 전체 레이아웃 구속
    st.markdown('<div class="student-center-card">', unsafe_allow_html=True)
    
    # 헤더 섹션 (타이틀과 제어판 버튼을 한 줄에 배치)
    h_col1, h_col2 = st.columns([3, 2])
    with h_col1:
        st.markdown("<h2 style='text-align:left; margin:0;'>🎒 성적 확인 시스템</h2>", unsafe_allow_html=True)
    with h_col2:
        # 🎯 [요청 반영] 버튼 크기를 글자 길이에 맞춰 줄이고 폰트 크기 조정
        if st.button("🔓 교사용 제어판", key="go_to_admin_btn"):
            st.query_params.update(mode="admin")
            st.rerun()
            
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    
    active_dbs = get_active_databases()
    if not active_dbs:
        st.info("현재 등록된 조회 데이터가 없습니다.")
    else:
        st.markdown("### 📝 개인별 성적 조회")
        opts_s = ["과목을 선택하세요."] + [f"📚 {d['subject']} ({d['grade']})" for d in active_dbs]
        sel_s = st.selectbox("조회할 과목 선택", opts_s, key="student_select_sub")
        
        if sel_s != "과목을 선택하세요.":
            db = active_dbs[opts_s.index(sel_s)-1]
            cf, sf = get_file_names(db['subject'], db['grade'].replace("학년",""))
            config = load_config(cf)
            
            # 정보 박스
            st.success(f"🧬 **{config['교과명']}** | **{config['학기통합명'] if config else ''}**")
            
            with st.form("login_form"):
                # 🎯 500px 안에서 가로로 너무 좁지 않게 폼 구성
                c1, c2 = st.columns(2)
                with c1: b_in = st.selectbox("반", [f"{x}반" for x in (config['선택된반 목록'].split(",") if config else ["1"])])
                with c2: n_in = st.number_input("번호", 1, 50, 1)
                
                name_in = st.text_input("이름", placeholder="이름을 입력하세요")
                pw_in = st.text_input("비밀번호", type="password", placeholder="Password")
                
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                if st.form_submit_button("🔍 내 성적 확인하기", use_container_width=True, type="secondary"):
                    df_st = load_students(sf)
                    if not df_st.empty:
                        res = df_st[(df_st['반']==int(b_in.replace("반",""))) & (df_st['번호']==n_in) & (df_st['이름']==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                        if not res.empty:
                            st.success(f"🎉 {name_in} 학생의 결과입니다.")
                            st.table(pd.DataFrame({k: [res.iloc[0][k]] for k in res.columns if '항목' in k or '점수' in k}))
                        else: st.error("정보가 일치하지 않습니다.")
    
    st.markdown('</div>', unsafe_allow_html=True) # 카드 닫기