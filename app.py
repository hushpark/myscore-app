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

# 🎯 독립형 모달 팝업창 디자인 개선
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

# --- 앱 설정 ---
st.set_page_config(page_title="교과 성적 제어 센터 v7", layout="wide")

query_params = st.query_params
is_admin_mode = query_params.get("mode") == "admin"

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년을 선택하세요.", "1학년", "2학년", "3학년"]
CURRENT_ADMIN_PW = load_admin_password()


# =========================================================================
# 🎯 전역 스타일 마스터 제어 (모드에 따라 클래스를 엄격하게 분리 타겟팅)
# =========================================================================
st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        div[data-testid="stHeader"] { height: 0px !important; display:none; }
        
        /* 팝업창 잔상 버그 영역 투명화 삭제 */
        div[data-testid="stDialog"] { display: none !important; }
        iframe { display: none !important; }
        
        /* 🎯 [선생님 요청 반영] 관리자 로그인 전용 박스 스타일 - 가로 420px 완벽 구속 */
        .real-admin-login-box {
            max-width: 420px !important;
            margin: 100px auto 0 auto !important;
            background-color: #ffffff !important; 
            border: 1px solid #e2e8f0 !important; 
            border-radius: 16px !important;       
            padding: 40px !important; 
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.07) !important; 
        }
        
        /* 🎯 학생 화면 메인 레이아웃 박스 스타일 - 가로 500px 구속 */
        .student-main-container {
            max-width: 500px !important;
            margin: 60px auto 0 auto !important;
            background-color: #ffffff !important;
            padding: 30px !important;
            border-radius: 14px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        }
        
        /* 박스 내부 Form 기본 외곽선 제거 */
        .real-admin-login-box div[data-testid="stForm"],
        .student-main-container div[data-testid="stForm"] {
            border: none !important;
            padding: 0px !important;
            box-shadow: none !important;
            max-width: 100% !important;
        }
        
        /* 💡 교사용 제어판 버튼 디자인 최적화 (글자 크기에 맞춰 축소 및 우측 가이드라인 정렬) */
        div.stButton > button[key="go_to_admin_btn"] {
            width: fit-content !important;
            min-width: auto !important;
            padding: 3px 12px !important;
            font-size: 15px !important;
            float: right !important;
            border-radius: 6px !important;
            border: 1px solid #cbd5e1 !important;
            color: #475569 !important;
            background-color: #ffffff !important;
        }
        
        .box-title { font-size: 26px; font-weight: 700; color: #1e293b; text-align: center; margin-bottom: 8px; }
        .box-desc { font-size: 14px; color: #64748b; text-align: center; margin-bottom: 25px; line-height: 1.5; }
        div.stButton > button { border-radius: 8px !important; transition: all 0.2s; }
        div.stButton > button[kind="primary"] { background-color: #ef4444 !important; border:none !important; }
        
        h1 { color: #0f172a !important; font-weight: 800 !important; }
        h2 { color: #0f172a !important; font-weight: 800 !important; font-size: 22px !important; margin: 0; }
        h3 { font-size: 17px !important; font-weight: 700 !important; color: #1e293b !important; }
        h4 { color: #334155 !important; }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# A. 선생님 관리자 화면 (?mode=admin)
# ==========================================
if is_admin_mode:
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    # A-1. 교과 관리자 인증 (🎯 정확하게 가로 420px 독립 박스 구속)
    if not st.session_state["admin_logged_in"]:
        st.markdown("<div class='real-admin-login-box'>", unsafe_allow_html=True)
        with st.form("admin_premium_login_form"):
            st.markdown("<div class='box-title'>🛡️ 교과 관리자 인증</div>", unsafe_allow_html=True)
            st.markdown("<div class='box-desc'>본인 교과의 성적 데이터를 관리하기 위해<br>인증 비밀번호를 입력해 주세요.</div>", unsafe_allow_html=True)
            admin_pw = st.text_input("비밀번호", type="password", placeholder="Password")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.form_submit_button("인증 및 로그인", use_container_width=True, type="primary"):
                if admin_pw == CURRENT_ADMIN_PW:
                    st.session_state["admin_logged_in"] = True
                    st.rerun()
                else: st.error("❌ 비밀번호가 틀렸습니다.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    # A-2. 로그인 성공 시 진짜 제어 센터 (여기는 정상적으로 넓고 편안한 와이드 형태 유지)
    else:
        t_col1, t_col2, t_col3 = st.columns([5, 1.5, 1.2])
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

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown("<h4 style='margin-bottom:20px;'>🛠️ [단계 1] 교과군 및 과목 지정</h4>", unsafe_allow_html=True)
            
            if "sel_group_idx" not in st.session_state: st.session_state.sel_group_idx = 0
            if "sel_sub_idx" not in st.session_state: st.session_state.sel_sub_idx = 0
            if "sel_grade_idx" not in st.session_state: st.session_state.sel_grade_idx = 0

            c1, c2, c3, c4 = st.columns([1, 1, 0.8, 0.7])
            with c1:
                g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"]
                sel_g = st.selectbox("1. 교과군", options=g_opts, index=st.session_state.sel_group_idx)
            with c2:
                final_sub = ""
                if sel_g == "➕ 신규 과목 개설":
                    t_g = st.selectbox("추가 위치", ["인문·사회군", "수리·과학군", "예체능군"])
                    final_sub = st.text_input("새 과목명").strip()
                elif sel_g != "교과군 선택":
                    s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                    sel_s = st.selectbox("2. 세부 과목", options=s_opts)
                    if sel_s != "과목 선택": final_sub = sel_s
                else: st.selectbox("2. 세부 과목", ["선택 대기"], disabled=True)
            with c3:
                sel_gr = st.selectbox("3. 관리 학년", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx)
                final_gr = sel_gr.replace("학년", "") if sel_gr != "학년을 선택하세요." else ""
            with c4:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("✅ 영역 활성화", use_container_width=True, type="primary"):
                    if final_sub and final_gr:
                        if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub)
                        st.session_state.active_subject, st.session_state.active_grade = final_sub, final_gr
                        st.rerun()
                    else: st.warning("항목 선택 필수")

        if "active_subject" in st.session_state and st.session_state.active_subject:
            sub, grd = st.session_state.active_subject, st.session_state.active_grade
            cf, sf = get_file_names(sub, grd)
            conf = load_config(cf)
            
            st.markdown(f"### 📍 현재 편집 중: <span style='color:#ef4444;'>[{sub}] {grd}학년</span>", unsafe_allow_html=True)
            
            col_left, col_right = st.columns(2)
            with col_left:
                with st.container(border=True):
                    st.markdown("#### 📌 [파트 1] 평가 기본 세팅")
                    y_opts = ["학기 선택"] + [f"{y}년 {t}학기" for y in range(2024, 2028) for t in [1, 2]]
                    sel_t = st.selectbox("대상 학기", y_opts)
                    
                    st.write("**담당 학급**")
                    cols_cl = st.columns(6)
                    sel_cl = []
                    for i in range(1, 13):
                        with cols_cl[(i-1)%6]:
                            if st.checkbox(f"{i}반"): sel_cl.append(i)
                            
                    n_item = st.number_input("평가 항목 개수", 0, 10, 0)
                    item_names = [st.text_input(f"{i+1}번 항목명") for i in range(n_item)]

            with col_right:
                with st.container(border=True):
                    st.markdown("#### 📂 [파트 2] 데이터 연동")
                    up_f = st.file_uploader("성적 CSV 업로드", type="csv")
                    if up_f:
                        pd.read_csv(up_f, encoding='cp949').to_csv(sf, index=False)
                        st.success("데이터 업로드 완료!")
                        
                    st.markdown("---")
                    if st.button("💾 이 과목 설정 최종 저장", use_container_width=True, type="primary"):
                        if sel_t != "학기 선택" and sel_cl and n_item > 0:
                            d = {"교과명":sub, "학년":grd, "학기통합명":sel_t, "선택된반 목록":",".join(map(str, sel_cl)), "항목개수":n_item}
                            for i, name in enumerate(item_names): d[f"항목{i+1}_이름"] = name
                            pd.DataFrame([d]).to_csv(cf, index=False)
                            st.success("설정 저장 성공!")
                    
                    st.button("🗑️ 전체 데이터 초기화", on_click=reset_all_data, use_container_width=True)

# ==========================================
# B. 학생 화면 (기본)
# ==========================================
else:
    # 🎯 학생 화면 전체 컴포넌트를 정확히 가로 500px 상자 안에 격리
    st.markdown('<div class="student-main-container">', unsafe_allow_html=True)
    
    h_col1, h_col2 = st.columns([3.3, 1.7])
    with h_col1: 
        st.markdown("<h2 style='text-align:left;'>🎒 수행평가 성적 확인 시스템</h2>", unsafe_allow_html=True)
    with h_col2:
        if st.button("🔓 교사용 제어판", key="go_to_admin_btn"):
            st.query_params.update(mode="admin")
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
            
            st.success(f"🧬 **{db['subject']}** | **{config['학기통합명'] if config else '설정 미완료'}**")
            
            with st.form("login_form"):
                classes = [f"{x.strip()}반" for x in str(config['선택된반 목록']).split(",")] if config else ["1반"]
                
                c1, c2, c3 = st.columns(3)
                with c1: b_in = st.selectbox("반", classes)
                with c2: n_in = st.number_input("번호", 1, 50, 1)
                with c3: name_in = st.text_input("이름", placeholder="홍길동")
                
                pw_in = st.text_input("비밀번호", type="password", placeholder="비밀번호")
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                
                if st.form_submit_button("🔍 내 점수 확인하기", use_container_width=True):
                    df_st = load_students(sf)
                    if df_st.empty: 
                        st.error("성적 데이터가 아직 연동되지 않은 교과입니다. 교과 선생님께 문의하세요.")
                    else:
                        res = df_st[(df_st['반']==int(b_in.replace("반",""))) & (df_st['번호']==n_in) & (df_st['이름']==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                        if not res.empty:
                            idx = res.index[0]
                            scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                            st.success(f"🎉 {name_in} 학생의 조회 결과입니다.")
                            st.table(pd.DataFrame(scores))
                            
                            if df_st.loc[idx, '확인여부'] != "확인 완료":
                                df_st.loc[idx, '확인여부'], df_st.loc[idx, '확인시간'] = "확인 완료", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                df_st.to_csv(sf, index=False)
                        else: 
                            st.error("입력한 학생 정보 또는 비밀번호가 일치하지 않습니다. 다시 확인해 주세요.")
                            
    st.markdown('</div>', unsafe_allow_html=True)