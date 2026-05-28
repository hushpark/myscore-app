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

# --- 앱 기본 세팅 (가장 먼저 실행) ---
st.set_page_config(page_title="수행평가 결과 시스템", layout="wide")

# =========================================================================
# 🎯 [순정 마스터 CSS] 모든 화면을 아담한 550px 상자로 전역 구속 (유령 박스 완전 없음)
# =========================================================================
st.markdown("""
    <style>
        /* 기본 배경 및 헤더 숨기기 */
        .main, [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
        div[data-testid="stHeader"] { display: none !important; }
        
        /* 🚨 문제의 유령 사각형을 만들던 st.dialog 관련 잔상 요소를 원천 차단 */
        div[data-testid="stDialog"], div[role="dialog"], .stDialog { display: none !important; }
        
        /* 🎯 [선생님 핵심 요청] 모든 화면의 메인 본체 상자를 가로 550px 아담한 카드로 고정 */
        .master-compact-card {
            max-width: 550px !important;
            margin: 60px auto 40px auto !important;
            background-color: #ffffff !important;
            padding: 35px !important;
            border-radius: 14px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.04) !important;
        }
        
        /* 내장 Form 기본 테두리 무효화 */
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0px !important;
            box-shadow: none !important;
        }
        
        /* 교사용 제어판 슬림 버튼 스타일 */
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
        
        /* 빨간색 확인 및 저장 단추 스타일 */
        div.stButton > button[kind="primary"] {
            background-color: #ef4444 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            padding: 10px 0px !important;
            border-radius: 6px !important;
        }
        
        h2 { font-size: 22px !important; color: #0f172a !important; font-weight: 800 !important; margin: 0 0 10px 0 !important; }
        h3 { font-size: 17px !important; font-weight: 700 !important; color: #1e293b !important; margin-bottom: 8px !important; }
        h4 { font-size: 16px !important; color: #334155 !important; font-weight: 600 !important; }
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

# --- 내부 화면 세션 상태 관리 ---
if "page_status" not in st.session_state:
    st.session_state["page_status"] = "student_main"

if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

if "show_pw_edit_section" not in st.session_state:
    st.session_state["show_pw_edit_section"] = False

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년을 선택하세요.", "1학년", "2학년", "3학년"]
CURRENT_ADMIN_PW = load_admin_password()


# =========================================================================
# 🔄 독점적 550px 상자 기반 화면 스위칭 시스템
# =========================================================================

# ------------------------------------------
# 🎒 1. 학생용 개인 성적 조회 첫 화면
# ------------------------------------------
if st.session_state["page_status"] == "student_main":
    
    st.markdown("<div class='master-compact-card'>", unsafe_allow_html=True)
    st.markdown("<h2>🎒 수행평가 성적 확인 시스템</h2>", unsafe_allow_html=True)
    
    # [1번 그림 양식] 제목 바로 아래에 예쁘게 들어가는 버튼
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
    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------
# 🛡️ 2. 교과 관리자 인증 화면 (로그인 전 - 3번 그림)
# ------------------------------------------
elif st.session_state["page_status"] == "teacher_auth":
    
    st.markdown("<div class='master-compact-card'>", unsafe_allow_html=True)
    st.markdown("<h2>🛡️ 교과 관리자 인증</h2>", unsafe_allow_html=True)
    
    with st.form("admin_login_form"):
        st.markdown("<p style='text-align:center; font-size:14px; color:#64748b; margin-bottom:20px;'>본인 교과의 성적 데이터를 관리하기 위해<br>인증 비밀번호를 입력해 주세요.</p>", unsafe_allow_html=True)
        admin_pw = st.text_input("비밀번호", type="password", placeholder="Password")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.form_submit_button("인증 및 로그인", use_container_width=True, type="primary"):
            if admin_pw == CURRENT_ADMIN_PW:
                st.session_state["admin_logged_in"] = True
                st.session_state["page_status"] = "teacher_main"
                st.rerun()
            else: 
                st.error("❌ 비밀번호가 틀렸습니다.")
                
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("🎒 학생 화면으로 돌아가기", key="outer_student_btn", use_container_width=True):
        st.session_state["page_status"] = "student_main"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------
# ⚙️ 3. 진짜 교사용 제어 센터 화면 (로그인 후)
# ------------------------------------------
elif st.session_state["page_status"] == "teacher_main":
    if not st.session_state["admin_logged_in"]:
        st.session_state["page_status"] = "teacher_auth"
        st.rerun()
        
    st.markdown("<div class='master-compact-card'>", unsafe_allow_html=True)
    st.markdown("<h2>⚙️ 교과 제어 센터</h2>", unsafe_allow_html=True)
    
    if st.button("🎒 학생 화면으로 나가기 (로그아웃)", key="outer_logout_btn", use_container_width=True):
        st.session_state["page_status"] = "student_main"
        st.session_state["admin_logged_in"] = False
        st.session_state["show_pw_edit_section"] = False
        st.rerun()
        
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    # [내부 암호 변경 서브 패널]
    if not st.session_state["show_pw_edit_section"]:
        if st.button("🔐 관리자 암호 변경하기", use_container_width=True):
            st.session_state["show_pw_edit_section"] = True
            st.rerun()
    else:
        with st.container(border=True):
            st.markdown("#### 🔐 관리자 암호 수정", unsafe_allow_html=True)
            new_pw = st.text_input("새 암호 입력", type="password")
            confirm_pw = st.text_input("새 암호 확인", type="password")
            
            is_valid, msg = is_strong_password(new_pw)
            if new_pw:
                if new_pw == confirm_pw and is_valid:
                    st.markdown("<div style='color:green; font-size:13px;'>✅ 암호 조건이 일치합니다.</div>", unsafe_allow_html=True)
                elif confirm_pw and new_pw != confirm_pw:
                    st.markdown("<div style='color:red; font-size:13px;'>❌ 암호 확인 칸이 일치하지 않습니다.</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='color:orange; font-size:13px;'>{msg}</div>", unsafe_allow_html=True)
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("새 암호 저장", use_container_width=True, type="primary", disabled=not (is_valid and new_pw == confirm_pw)):
                    save_admin_password(new_pw)
                    st.success("암호가 변경되었습니다!")
                    st.session_state["show_pw_edit_section"] = False
                    st.rerun()
            with c_btn2:
                if st.button("변경 취소", use_container_width=True):
                    st.session_state["show_pw_edit_section"] = False
                    st.rerun()
                    
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    # [단계 1] 구역
    with st.container(border=True):
        st.markdown("<h4>🛠️ [단계 1] 교과군 및 과목 지정</h4>", unsafe_allow_html=True)
        
        if "sel_group_idx" not in st.session_state: st.session_state.sel_group_idx = 0
        if "sel_sub_idx" not in st.session_state: st.session_state.sel_sub_idx = 0
        if "sel_grade_idx" not in st.session_state: st.session_state.sel_grade_idx = 0

        c1, c2 = st.columns(2)
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
            
        c3, c4 = st.columns([1.3, 0.7])
        with c3:
            sel_gr = st.selectbox("3. 관리 학년", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx)
            final_gr = sel_gr.replace("학년", "") if sel_gr != "학년을 선택하세요." else ""
        with c4:
            st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 활성화", use_container_width=True, type="primary"):
                if final_sub and final_gr:
                    if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub)
                    st.session_state.active_subject, st.session_state.active_grade = final_sub, final_gr
                    st.rerun()

    # 하부 편집판 구역
    if "active_subject" in st.session_state and st.session_state.active_subject:
        st.markdown("---")
        sub, grd = st.session_state.active_subject, st.session_state.active_grade
        cf, sf = get_file_names(sub, grd)
        conf = load_config(cf)
        
        st.markdown(f"##### 📍 현재 편집 중: [{sub}] {grd}학년", unsafe_allow_html=True)
        
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
            
    st.markdown("</div>", unsafe_allow_html=True)