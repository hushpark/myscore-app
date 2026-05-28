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
        div.stButton > button[key="outer_logout_btn"],
        div.stButton > button[key="outer_pw_btn"] {
            width: fit-content !important;
            min-width: auto !important;
            padding: 3px 12px !important;
            font-size: 12px !important;
            border-radius: 6px !important;
            border: 1px solid #cbd5e1 !important;
            color: #475569 !important;
            background-color: #ffffff !important;
            white-space: nowrap !important;
        }
        
        /* 우측 정렬 유지 */
        div.stButton:has(button[key="outer_teacher_btn"]),
        div.stButton:has(button[key="outer_logout_btn"]),
        div.stButton:has(button[key="outer_pw_btn"]) {
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
        
        /* 팝업창(모달) 및 모니터링 내부 성적 테이블의 제목(th)과 점수(td) 모두 가운데 정렬 */
        div[role="dialog"] table th, div[role="dialog"] table td,
        div.monitor-table table th, div.monitor-table table td {
            text-align: center !important;
        }
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
        st.session_state.clear()
        st.rerun()

# 🎯 비밀번호 변경을 위한 팝업 모달 함수
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


# --- 내부 화면 페이지 제어 상태 초기화 ---
if "page_status" not in st.session_state:
    st.session_state["page_status"] = "student_main"

if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

if "show_pw_edit_section" not in st.session_state:
    st.session_state["show_pw_edit_section"] = False

if "sel_group_idx" not in st.session_state: st.session_state.sel_group_idx = 0
if "sel_sub_idx" not in st.session_state: st.session_state.sel_sub_idx = 0
if "sel_grade_idx" not in st.session_state: st.session_state.sel_grade_idx = 0

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 선택", "1학년", "2학년", "3학년"]
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
    
    col_empty, col_btn = st.columns([3, 1])
    with col_btn:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if st.button("🔓 교사용 제어판", key="outer_teacher_btn"):
            st.session_state["page_status"] = "teacher_auth"
            st.rerun()
            
    active_dbs = get_active_databases()
    
    with st.container(border=True):
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 5px 0px;'>🎒 수행평가 성적 확인 시스템</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; margin: 0px 0px 10px 0px; color: #475569;'>📝 개인별 성적 조회</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:14px; color:#64748b; margin-bottom:20px;'>과목을 선택하고 본인의 정보를 정확하게 입력해 주세요.</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        
        if not active_dbs:
            st.warning("현재 등록된 성적 데이터가 없습니다.")
        else:
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
                        st.markdown("<div style='font-size:14px; font-weight:700; color:#0f172a; margin-bottom:8px;'>🔐 본인 인증 정보 입력</div>", unsafe_allow_html=True)
                        classes = [f"{x.strip()}반" for x in str(config['선택된반 목록']).split(",")] if '선택된반 목록' in config else ["1반"]
                        
                        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
                        with c1: b_in = st.selectbox("반", classes)
                        with c2: n_in = st.number_input("번호", 1, 50, 1)
                        with c3: name_in = st.text_input("이름", placeholder="홍길동")
                        with c4: pw_in = st.text_input("비밀번호", type="password", placeholder="****")
                            
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
                                    total_sum = 0
                                    
                                    for i in range(int(config['항목개수'])):
                                        h_name = config.get(f'항목{i+1}_이름', f'항목{i+1}')
                                        if h_name in df_st.columns:
                                            val = df_st.loc[idx, h_name]
                                            scores[h_name] = [val]
                                            
                                            try:
                                                if pd.notna(val):
                                                    total_sum += float(val)
                                            except:
                                                pass
                                    
                                    if float(total_sum).is_integer():
                                        scores['합계'] = [int(total_sum)]
                                    else:
                                        scores['합계'] = [round(total_sum, 2)]
                                    
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
        
    st.markdown("""
        <style>
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #e2e8f0 !important;
            padding: 35px 40px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            background-color: #ffffff !important;
            max-width: 900px !important; 
            margin: 0px auto 20px auto !important; 
        }
        </style>
    """, unsafe_allow_html=True)

    col_empty, col_pw, col_logout = st.columns([5, 1.4, 1.4])
    with col_pw:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if st.button("🔐 암호 변경", key="outer_pw_btn", use_container_width=True):
            password_update_dialog()
    with col_logout:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if st.button("🎒 학생 화면", key="outer_logout_btn", use_container_width=True):
            st.session_state["page_status"] = "student_main"
            st.session_state["admin_logged_in"] = False
            st.rerun()

    with st.container(border=True):
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 5px 0px;'>⚙️ 교과·학년 통합 제어 센터</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; margin: 0px 0px 10px 0px; color: #475569;'>🛠️ [단계 1] 획기적인 교과군별 과목 지정</h4>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 15px 0 25px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns([1.3, 1.3, 1.0, 1.3])
        
        with c1:
            st.markdown("<div style='font-size:13px; font-weight:600; color:#475569; margin-bottom:5px;'>📁 1단계: 교과군 분류</div>", unsafe_allow_html=True)
            g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"]
            sel_g = st.selectbox("교과군", options=g_opts, index=st.session_state.sel_group_idx, label_visibility="collapsed")
            
        with c2:
            st.markdown("<div style='font-size:13px; font-weight:600; color:#475569; margin-bottom:5px;'>🗂️ 2단계: 세부 과목 선택</div>", unsafe_allow_html=True)
            final_sub = ""
            t_g = ""
            if sel_g == "➕ 신규 과목 개설":
                t_g = st.selectbox("추가 위치", ["인문·사회군", "수리·과학군", "예체능군"], label_visibility="collapsed")
                final_sub = st.text_input("새 과목명", placeholder="새 과목명을 입력하세요", label_visibility="collapsed").strip()
            elif sel_g != "교과군 선택":
                s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                idx_s = st.session_state.sel_sub_idx if st.session_state.sel_sub_idx < len(s_opts) else 0
                sel_s = st.selectbox("세부과목", options=s_opts, index=idx_s, label_visibility="collapsed")
                if sel_s != "과목 선택": final_sub = sel_s
            else: 
                st.selectbox("세부과목", ["선택 대기"], disabled=True, label_visibility="collapsed")
                
        with c3:
            st.markdown("<div style='font-size:13px; font-weight:600; color:#475569; margin-bottom:5px;'>🎓 3단계: 관리 학년</div>", unsafe_allow_html=True)
            sel_gr = st.selectbox("관리학년", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx, label_visibility="collapsed")
            final_gr = sel_gr.replace("학년", "") if sel_gr != "학년 선택" else ""
            
        with c4:
            st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 과목 활성화", use_container_width=True):
                if final_sub and final_gr:
                    if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub)
                    st.session_state.active_subject, st.session_state.active_grade = final_sub, final_gr
                    st.session_state.sel_group_idx = g_opts.index(sel_g)
                    if sel_g != "➕ 신규 과목 개설": st.session_state.sel_sub_idx = s_opts.index(final_sub)
                    st.session_state.sel_grade_idx = GRADE_OPTIONS.index(sel_gr)
                    st.rerun()
                else: 
                    st.warning("모든 항목을 선택해 주세요.")
                    
        st.markdown("<div style='background-color:#eff6ff; border: 2px dashed #93c5fd; padding:15px; border-radius:8px; margin-top:20px; color:#1e3a8a; font-size:15px; text-align: center; font-weight: 500;'><span style='display: inline-block !important; white-space: nowrap !important; word-break: keep-all !important;'>💡 <b>[🚀 과목 활성화]</b>를 누르시면 해당 과목의 <b style='color:#ef4444; font-size:16px; background-color:#ffe4e6; padding:4px 8px; border-radius:4px;'>[만들기 및 불러오기]</b>가 됩니다.</span></div>", unsafe_allow_html=True)
        
        # 🚀 과목 활성화 이후 작업 구역
        if "active_subject" in st.session_state and st.session_state.active_subject:
            sub, grd = st.session_state.active_subject, st.session_state.active_grade
            cf, sf = get_file_names(sub, grd)
            conf = load_config(cf)
            
            st.markdown("<hr style='margin: 30px 0 20px 0; border: none; border-top: 2px dashed #e2e8f0;'>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; color: #1e3a8a; margin-bottom: 25px;'>📍 현재 작업 중: <span style='color:#ef4444;'>[{sub}]</span> {grd}학년</h3>", unsafe_allow_html=True)
            
            # 파트 1 (학기/평가 세팅)
            with st.container(border=True):
                st.markdown("<h4 style='color: #1e293b; margin-top: 5px; margin-bottom: 20px;'>📌 [파트 1] 학기 및 평가 세팅</h4>", unsafe_allow_html=True)
                
                col_t, _ = st.columns([1.5, 1.5])
                with col_t:
                    y_opts = ["학년도/학기를 선택하세요."] + [f"{y}학년도 {t}학기" for y in range(2024, 2030) for t in [1, 2]] + ["➕ 직접 입력"]
                    saved_s = conf['학기통합명'] if conf else "학년도/학기를 선택하세요."
                    idx_t = y_opts.index(saved_s) if saved_s in y_opts else y_opts.index("➕ 직접 입력") if saved_s != "학년도/학기를 선택하세요." else 0
                    sel_t = st.selectbox("대상 학기", y_opts, index=idx_t)
                    final_t = st.text_input("✏️ 직접 입력", value=saved_s if idx_t == len(y_opts)-1 else "") if sel_t == "➕ 직접 입력" else sel_t

                st.markdown("<div style='margin-top:15px; margin-bottom:5px; font-weight:600;'>🏫 담당 학급(반)</div>", unsafe_allow_html=True)
                saved_cl = [int(x) for x in str(conf['선택된반 목록']).split(",")] if conf else []
                sel_cl = []
                cols_cl = st.columns(6)
                for i in range(1, 13):
                    with cols_cl[(i-1)%6]:
                        if st.checkbox(f"{i}반", value=i in saved_cl): sel_cl.append(i)

                st.markdown("<div style='margin-top:15px; margin-bottom:5px; font-weight:600;'>✍️ 평가 항목</div>", unsafe_allow_html=True)
                n_item = st.number_input("평가 항목 개수", 0, 10, int(conf['항목개수']) if conf else 0)
                item_names = []
                if n_item > 0:
                    cols_i = st.columns(3)
                    for i in range(1, n_item + 1):
                        with cols_i[(i-1)%3]:
                            item_names.append(st.text_input(f"{i}번 이름", value=conf.get(f'항목{i}_이름', "") if conf else ""))

            # 파트 2 (데이터 제어)
            with st.container(border=True):
                st.markdown("<h4 style='color: #1e293b; margin-top: 5px; margin-bottom: 20px;'>📂 [파트 2] 데이터 제어</h4>", unsafe_allow_html=True)
                ready = final_t != "학년도/학기를 선택하세요." and sel_cl and n_item > 0 and all(item_names)
                
                c1, c2 = st.columns([1.5, 1.5])
                with c1:
                    if ready:
                        if st.button(f"💾 [{sub}] 설정 저장", type="primary", use_container_width=True):
                            d = {"교과명":sub, "학년":grd, "학기통합명":final_t, "선택된반 목록":",".join(map(str, sorted(sel_cl))), "항목개수":n_item}
                            for i, name in enumerate(item_names): d[f"항목{i+1}_이름"] = name
                            pd.DataFrame([d]).to_csv(cf, index=False)
                            st.success("저장 완료!")
                            st.rerun()
                    else: st.button("⚠️ 설정 미완료", disabled=True, use_container_width=True)
                with c2:
                    if st.button("➕ 다른 과목 추가하기", use_container_width=True):
                        st.session_state.active_subject = None
                        st.session_state.sel_group_idx = 0
                        st.session_state.sel_sub_idx = 0
                        st.session_state.sel_grade_idx = 0
                        st.rerun()

                st.markdown("<hr style='margin: 25px 0 15px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                
                st.markdown("<div style='font-size:14px; font-weight:600; color:#475569; margin-bottom:8px;'>📁 성적 CSV 관리 및 업로드</div>", unsafe_allow_html=True)
                up_col1, up_col2 = st.columns([3.5, 1.5])
                with up_col1:
                    up_f = st.file_uploader("성적 CSV 업로드", type="csv", label_visibility="collapsed")
                    if up_f:
                        try:
                            df_up = pd.read_csv(up_f, encoding='cp949')
                            df_up.to_csv(sf, index=False)
                            st.success("성적 데이터 연동 완료!")
                            st.rerun()
                        except: st.error("파일 형식을 확인하세요 (CP949/UTF-8)")
                        
                with up_col2:
                    sample_columns = ["반", "번호", "이름", "비밀번호", "확인여부", "확인시간"] + (item_names if item_names else ["수행1", "수행2"])
                    sample_df = pd.DataFrame([[1, 1, "홍길동", "1234", "미확인", ""] + [0]*len(item_names if item_names else ["수행1", "수행2"])], columns=sample_columns)
                    
                    csv_buffer = io.StringIO()
                    sample_df.to_csv(csv_buffer, index=False, encoding='cp949')
                    csv_bytes = csv_buffer.getvalue().encode('cp949')
                    
                    st.download_button(
                        label="📥 예시 파일 다운로드",
                        data=csv_bytes,
                        file_name=f"sample_students_{sub}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            # ==========================================
            # 💡 [신규 추가] 📊 실시간 데이터 확인 모니터 구역
            # ==========================================
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<h4 style='color: #0f172a; margin-top: 5px; margin-bottom: 15px;'>📊 실시간 데이터 연동 모니터</h4>", unsafe_allow_html=True)
                
                # 1. 설정값 존재 유무 파악
                if conf:
                    st.markdown(f"""
                    <div style='background:#f8fafc; border:1px solid #e2e8f0; padding:12px 15px; border-radius:6px; font-size:14px; margin-bottom:15px;'>
                        ✅ <b>설정 파일 감지됨:</b> {conf.get('학기통합명', '미정')} | 
                        <b>배정 학급:</b> {conf.get('선택된반 목록', '미정')} | 
                        <b>평가 항목:</b> {conf.get('항목개수', 0)}개 세팅 완료
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("ℹ️ 파트 1 설정을 저장하면 세팅 요약 정보가 여기에 표시됩니다.")
                
                # 2. 명렬표 데이터 존재 유무 파악
                df_monitor = load_students(sf)
                if not df_monitor.empty:
                    st.markdown("<div style='font-size:13px; font-weight:600; color:#475569; margin-bottom:5px;'>📋 현재 연동된 학생 명렬표 (가운데 정렬)</div>", unsafe_allow_html=True)
                    
                    # 가운데 정렬 CSS 클래스 주입을 위한 래퍼 디브 생성
                    st.markdown('<div class="monitor-table">', unsafe_allow_html=True)
                    st.dataframe(df_monitor, use_container_width=True, hide_index=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning("⚠️ 아직 업로드된 학생 성적 CSV 데이터가 없습니다. 파일을 업로드해 주세요.")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("🗑️ 초기화 (모든 데이터 포맷)", use_container_width=True): 
                reset_all_data()