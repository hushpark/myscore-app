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
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="centered")

# =========================================================================
# 🎯 [CSS 최종 완결판] 대시보드 탭(Tab) 메뉴 스타일 입히기 및 간격 초밀착 튜닝
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
        div[data-testid="stHeader"] { display: none !important; background: transparent !important; }
        
        /* 하단 잉여 공간(푸터) 완전 제거 */
        footer { display: none !important; }
        
        /* 상단 잘림 버그 완치 */
        .block-container {
            padding-top: 2.5rem !important; 
            padding-bottom: 0.5rem !important; 
        }
        
        /* 전체 가로폭 카드 크기를 1450px로 설정 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #e2e8f0 !important;
            padding: 20px 25px 30px 25px !important; 
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            background-color: #ffffff !important;
            max-width: 1450px !important; 
            margin: 0px auto !important; 
        }
        
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0px !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }
        
        /* 타이틀 및 서브 타이틀 글씨 크기 원래대로 단정하게 고정 */
        h2 { font-size: 22px !important; color: #0f172a !important; font-weight: 800 !important; margin: 5px 0 10px 0 !important; white-space: nowrap !important; text-align: center; }
        h4 { font-size: 14px !important; font-weight: 700 !important; color: #475569 !important; margin-top: 0px !important; margin-bottom: 2px !important; white-space: nowrap !important; }
        
        /* 상단 우측 학생인증 관련 버튼 스타일 */
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
        
        /* 좌측 세로형 제어판 버튼들 자동 크기 복원 및 한 줄 고정 */
        div[data-testid="stHorizontalBlock"] div.stButton button,
        div[data-testid="stHorizontalBlock"] div.stButton button:disabled,
        div[data-testid="stHorizontalBlock"] div.stButton button[disabled] {
            white-space: nowrap !important;
            word-break: keep-all !important;
        }
        
        /* 모든 버튼과 컴포넌트 간의 세로 유격을 최소화하여 촘촘하게 배치 */
        div[data-testid="stVerticalBlock"] > div:has(div.stButton),
        div[data-testid="stVerticalBlock"] > div:has(div.stSelectbox) {
            padding-bottom: 0px !important;
            margin-bottom: -4px !important;
        }
        div.stButton button {
            margin: 0px auto !important;
            padding-top: 5px !important;
            padding-bottom: 5px !important;
            transition: all 0.15s ease-in-out !important;
        }
        
        /* 다운로드 버튼 폰트 및 스타일 미니멀화 */
        div.stDownloadButton, div.stDownloadButton button, div.stDownloadButton button * {
            font-size: 11px !important; 
            white-space: nowrap !important;
            word-break: keep-all !important;
        }
        div.stDownloadButton button {
            padding: 4px 6px !important;
        }
        
        /* 다운로드 버튼 밑바닥 마진을 대폭 위로 밀어올려 업로더 박스와 밀착 */
        div.stDownloadButton {
            margin-bottom: -15px !important; 
        }
        
        /* 성적 일괄 업로드 테두리 박스 내부 공백을 콤팩트하게 다듬기 */
        div.compact-upload-box {
            padding: 6px 10px !important;
            margin-top: 2px !important;
            margin-bottom: 2px !important;
        }
        
        /* 파일 업로드 영역의 내부 상단 여백을 극단적으로 줄여 딱 붙임 */
        div[data-testid="stFileUploader"] {
            padding-top: 0px !important;
            margin-top: -10px !important; 
        }
        
        /* Upload 밑의 200MB 안내 문구 가독성 튜닝 */
        div[data-testid="stFileUploader"] section small {
            white-space: normal !important;
            word-break: break-all !important;
            display: block !important;
            line-height: 1.3 !important;
            color: #64748b !important;
        }
        
        /* 최하단 가이드 바 바닥선 정렬 여백 */
        div.custom-guide-bar {
            background-color: #eff6ff !important; 
            border: 2px dashed #93c5fd !important; 
            padding: 10px !important; 
            border-radius: 8px !important; 
            margin-top: 15px !important; 
            margin-bottom: 10px !important; 
            color: #1e3a8a !important; 
            font-size: 14px !important; 
            text-align: center !important; 
            font-weight: 500 !important; 
            white-space: nowrap !important;
        }
        
        /* 테이블 내부 완전 중앙 정렬 */
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

def get_file_names(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    safe_semester = semester_str.replace(" ", "_").replace("/", "_")
    return f"config_{safe_subject}_{grade}grade_{safe_semester}.csv", f"students_{safe_subject}_{grade}grade_{safe_semester}.csv"

def load_config(file):
    if os.path.exists(file):
        try: return pd.read_csv(file).iloc[0].to_dict()
        except: return None
    return None

def load_students(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

def get_active_databases():
    active_list = []
    for f in glob.glob("config_*.csv"):
        try:
            filename = os.path.basename(f)
            if filename == CONFIG_FILE_MAIN:
                continue
            core_name = filename.replace("config_", "").replace(".csv", "")
            
            match = re.search(r"(.+?)_(1|2|3)grade_(.+)", core_name)
            if match:
                sub_name = match.group(1).replace("_", " ")
                grd_name = f"{match.group(2)}학년"
                sem_name = match.group(3).replace("_", " ")
                active_list.append({"subject": sub_name, "grade": grd_name, "semester": sem_name})
        except: pass
    return active_list

def remove_subject_completely_from_disk(sub_name):
    if os.path.exists(CONFIG_FILE_MAIN):
        try:
            df = pd.read_csv(CONFIG_FILE_MAIN)
            df = df[df["과목명"] != sub_name]
            df.to_csv(CONFIG_FILE_MAIN, index=False)
        except: pass
    
    safe_sub = sub_name.replace(" ", "_")
    all_targets = glob.glob(f"config_{safe_sub}_*.csv") + glob.glob(f"students_{safe_sub}_*.csv")
    for f in all_targets:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

def reset_all_data():
    targets = glob.glob("config_*.csv") + glob.glob("students_*.csv") + [CONFIG_FILE_MAIN, META_FILE]
    for f in targets:
        if os.path.exists(f):
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

if "show_monitor_view" not in st.session_state:
    st.session_state["show_monitor_view"] = False

if "show_delete_panel" not in st.session_state:
    st.session_state["show_delete_panel"] = False

if "sel_group_idx" not in st.session_state: st.session_state.sel_group_idx = 0
if "sel_sub_idx" not in st.session_state: st.session_state.sel_sub_idx = 0
if "sel_grade_idx" not in st.session_state: st.session_state.sel_grade_idx = 0
if "sel_semester_idx" not in st.session_state: st.session_state.sel_semester_idx = 0

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 선택", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]
CURRENT_ADMIN_PW = load_admin_password()


# ==========================================
# 🔄 독점 화면 분기 구동 영역
# ==========================================

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
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 5px 0px;'>🎒 수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; margin: 0px 0px 10px 0px; color: #475569;'>📝 개인별 성적 조회</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:14px; color:#64748b; margin-bottom:20px;'>과목과 해당 학기를 선택하고 정보를 입력해 주세요.</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        
        if not active_dbs:
            st.warning("현재 등록된 성적 데이터가 없습니다.")
        else:
            st.markdown("<div style='font-size:14px; font-weight:700; color:#0f172a; margin-bottom:8px;'>🎯 대상 과목 및 학기 선택</div>", unsafe_allow_html=True)
            opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs]
            sel_s = st.selectbox("조회할 과목 선택", opts_s, label_visibility="collapsed", key="student_select_sub")
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            
            if sel_s != "과목 및 학기를 선택하세요.":
                db = active_dbs[opts_s.index(sel_s)-1]
                cf, sf = get_file_names(db['subject'], db['grade'].replace("학년",""), db['semester'])
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
                                                if pd.notna(val): total_sum += float(val)
                                            except: pass
                                    
                                    if float(total_sum).is_integer(): scores['합계'] = [int(total_sum)]
                                    else: scores['합계'] = [round(total_sum, 2)]
                                    
                                    if df_st.loc[idx, '확인여부'] != "확인 완료":
                                        df_st.loc[idx, '확인여부'], df_st.loc[idx, '확인시간'] = "확인 완료", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        df_st.to_csv(sf, index=False)
                                        
                                    show_result_dialog(name_in, scores)
                                else: 
                                    st.error("입력한 학생 정보 또는 비밀번호가 일치하지 않습니다.")

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
            else: st.error("❌ 비밀번호가 틀렸습니다.")
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

    col_empty, col_pw, col_logout = st.columns([5, 1.4, 1.4])
    with col_pw:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if st.button("🔐 암호 변경", key="outer_pw_btn", use_container_width=True): password_update_dialog()
    with col_logout:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if st.button("🎒 학생 화면", key="outer_logout_btn", use_container_width=True):
            st.session_state["page_status"] = "student_main"
            st.session_state["admin_logged_in"] = False
            st.session_state["show_monitor_view"] = False
            st.session_state["show_delete_panel"] = False
            st.rerun()

    with st.container(border=True):
        st.markdown("<h2>⚙️ 교과·학년 통합 제어 센터</h2>", unsafe_allow_html=True)
        
        # 좌우 분할 비율 1.4 : 4.2 매칭
        frame_left, frame_right = st.columns([1.4, 4.2])
        
        has_active = "active_subject" in st.session_state and st.session_state.active_subject
        
        # ==========================================
        # 👈 [1구역 - 왼쪽 제어 메뉴]
        # ==========================================
        with frame_left:
            st.markdown("<h4>📁 대상 과목 및 학기 선택</h4>", unsafe_allow_html=True)
            
            g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"]
            sel_g = st.selectbox("1단계: 교과군 분류", options=g_opts, index=st.session_state.sel_group_idx, label_visibility="collapsed")
            
            final_sub = ""
            t_g = ""
            if sel_g == "➕ 신규 과목 개설":
                t_g = st.selectbox("추가 위치 지정", ["인문·사회군", "수리·과학군", "예체능군"])
                final_sub = st.text_input("✏️ 새 과목명 입력", placeholder="과목명 입력").strip()
            elif sel_g != "교과군 선택":
                s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                idx_s = st.session_state.sel_sub_idx if st.session_state.sel_sub_idx < len(s_opts) else 0
                sel_s = st.selectbox("2단계: 세부 과목 선택", options=s_opts, index=idx_s, label_visibility="collapsed")
                if sel_s != "과목 선택": final_sub = sel_s
            else: 
                st.selectbox("2단계: 세부 과목 선택", ["과목 선택 대기"], disabled=True, label_visibility="collapsed")
                
            sel_gr = st.selectbox("3단계: 관리 학년 지정", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx, label_visibility="collapsed")
            final_gr = sel_gr.replace("학년", "") if sel_gr != "학년 선택" else ""
            
            sel_se = st.selectbox("4단계: 대상 학기 선택", options=SEMESTER_OPTIONS, index=st.session_state.sel_semester_idx, label_visibility="collapsed")
            final_se = sel_se if sel_se != "학기 선택" else ""
            
            # 💡 [디자인 보정]: 과목 활성화 버튼 (기본 탭)
            if st.button("🚀 과목 활성화", use_container_width=True, key="side_activate_btn"):
                if final_sub and final_gr and final_se:
                    if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub)
                    st.session_state.active_subject = final_sub
                    st.session_state.active_grade = final_gr
                    st.session_state.active_semester = final_se
                    
                    st.session_state.sel_group_idx = g_opts.index(sel_g)
                    if sel_g != "➕ 신규 과목 개설": st.session_state.sel_sub_idx = s_opts.index(final_sub)
                    st.session_state.sel_grade_idx = GRADE_OPTIONS.index(sel_gr)
                    st.session_state.sel_semester_idx = SEMESTER_OPTIONS.index(sel_se)
                    st.session_state["show_delete_panel"] = False
                    st.rerun()
                else: st.warning("과목, 학년, 학기 데이터를 누락 없이 모두 선택해 주세요.")
            
            # 💡 [1단계 핵심]: 데이터 삭제 탭 (선택 상태에 따라 배경색 토글 및 빨간색 밑줄 강제 연동)
            if st.session_state["show_delete_panel"]:
                # 탭 활성화 상태: 세련된 경고용 배경 연빨강 + 글자 진빨강 + 밑줄 진빨강
                st.markdown("""<style>
                    div:has(> button[key='side_toggle_delete_btn']) button {
                        background-color: #fef2f2 !important;
                        border: 1px solid #fca5a5 !important;
                        box-shadow: inset 0 2px 4px rgba(239, 68, 68, 0.05) !important;
                    }
                    div:has(> button[key='side_toggle_delete_btn']) p, 
                    div:has(> button[key='side_toggle_delete_btn']) span {
                        color: #ef4444 !important;
                        text-decoration: underline !important;
                        text-decoration-color: #ef4444 !important;
                        text-underline-offset: 4px !important;
                        font-weight: 800 !important;
                    }
                </style>""", unsafe_allow_html=True)
                del_panel_label = "🚨 데이터 삭제 닫기"
            else:
                # 탭 비활성화 기본 상태: 글자 빨간색 + 밑줄 빨간색 고정으로 시각적 주의 집중
                st.markdown("""<style>
                    div:has(> button[key='side_toggle_delete_btn']) p, 
                    div:has(> button[key='side_toggle_delete_btn']) span {
                        color: #ef4444 !important;
                        text-decoration: underline !important;
                        text-decoration-color: #ef4444 !important;
                        text-underline-offset: 4px !important;
                        font-weight: 700 !important;
                    }
                </style>""", unsafe_allow_html=True)
                del_panel_label = "🚨 데이터 삭제"

            if st.button(del_panel_label, key="side_toggle_delete_btn", use_container_width=True):
                st.session_state["show_delete_panel"] = not st.session_state["show_delete_panel"]
                if st.session_state["show_delete_panel"]:
                    st.session_state["show_monitor_view"] = False
                st.rerun()
            
            # 💡 [2구역 긴밀 정렬] 데이터 삭제 버튼 바로 하단 여백 공간 압축
            st.markdown("<div style='margin-bottom: -15px;'></div>", unsafe_allow_html=True)
            
            # 💡 [2단계 핵심]: 설정 저장 탭 (활성화 되었을 때 세련된 블루 테마 탭으로 유도)
            if has_active:
                st.markdown("""<style>
                    div:has(> button[key='side_save_btn']) button {
                        border: 1px solid #93c5fd !important;
                        background-color: #eff6ff !important;
                    }
                    div:has(> button[key='side_save_btn']) p,
                    div:has(> button[key='side_save_btn']) span {
                        color: #1d4ed8 !important;
                        font-weight: 700 !important;
                    }
                </style>""", unsafe_allow_html=True)
            
            save_btn_label = f"💾 [{st.session_state.get('active_subject', '미정')}] 설정 저장" if has_active else "💾 설정 저장"
            if st.button(save_btn_label, key="side_save_btn", disabled=not has_active):
                st.session_state["trigger_save_action"] = True
            
            # 💡 [3단계 핵심]: 학생 입력 확인 탭 (활성화 시 상큼한 그린 테마 탭으로 스위칭)
            if st.session_state["show_monitor_view"]:
                st.markdown("""<style>
                    div:has(> button[key='side_monitor_btn']) button {
                        background-color: #f0fdf4 !important;
                        border: 1px solid #86efac !important;
                        box-shadow: inset 0 2px 4px rgba(34, 197, 94, 0.05) !important;
                    }
                    div:has(> button[key='side_monitor_btn']) p,
                    div:has(> button[key='side_monitor_btn']) span {
                        color: #16a34a !important;
                        font-weight: 700 !important;
                    }
                </style>""", unsafe_allow_html=True)
                monitor_label = "👀 학생 입력 확인 닫기"
            else:
                monitor_label = "👥 학생 입력 확인"

            if st.button(monitor_label, key="side_monitor_btn", disabled=not has_active):
                st.session_state["show_monitor_view"] = not st.session_state["show_monitor_view"]
                st.rerun()
                
            # 과목 추가 버튼
            if st.button("➕ 과목 추가", key="side_add_btn"):
                st.session_state.active_subject = None
                st.session_state.active_grade = None
                st.session_state.active_semester = None
                st.session_state.sel_group_idx = 0
                st.session_state.sel_sub_idx = 0
                st.session_state.sel_grade_idx = 0
                st.session_state.sel_semester_idx = 0
                st.session_state["show_monitor_view"] = False
                st.session_state["show_delete_panel"] = False
                st.rerun()

            # 성적 CSV 관리 및 업로드 구역
            if has_active:
                sub = st.session_state.active_subject
                grd = st.session_state.active_grade
                sem = st.session_state.active_semester
                cf, sf = get_file_names(sub, grd, sem)
                conf = load_config(cf)
                item_names = [conf.get(f'항목{i+1}_이름', f'수행{i+1}') for i in range(int(conf.get('항목개수', 0)))] if conf else ["수행1", "수행2"]

                with st.container(border=True):
                    st.markdown('<div class="compact-upload-box">', unsafe_allow_html=True)
                    st.markdown("<div style='font-size:12px; font-weight:600; color:#475569; margin-bottom:6px;'>📁 성적 일괄 업로드</div>", unsafe_allow_html=True)
                    
                    sample_columns = ["반", "번호", "이름", "비밀번호", "확인여부", "확인시간"] + item_names
                    sample_df = pd.DataFrame([[1, 1, "홍길동", "1234", "미확인", ""] + [0]*len(item_names)], columns=sample_columns)
                    csv_buffer = io.StringIO()
                    sample_df.to_csv(csv_buffer, index=False, encoding='cp949')
                    csv_bytes = csv_buffer.getvalue().encode('cp949')
                    
                    st.download_button(
                        label="📥 예시 파일 다운로드",
                        data=csv_bytes,
                        file_name=f"sample_students_{sub}_{sem}.csv",
                        mime="text/csv",
                        key="btn_download_sample"
                    )
                    
                    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
                    
                    up_f = st.file_uploader("성적 CSV 업로드", type="csv", label_visibility="collapsed", key="uploader_csv_file")
                    if up_f:
                        try:
                            df_up = pd.read_csv(up_f, encoding='cp949')
                            df_up.to_csv(sf, index=False)
                            st.success("🎉 성적 연동 완료!")
                            st.rerun()
                        except: 
                            st.error("❌ 파일 형식을 확인하세요 (CP949/UTF-8)")
                    st.markdown('</div>', unsafe_allow_html=True)
                        
            # 시스템 초기화 버튼
            if st.button("🗑️ 시스템 초기화", key="side_reset_btn"): reset_all_data()

        # ==========================================
        # 👉 [2구역 - 오른쪽 메인 기능 판넬 및 모니터 창]
        # ==========================================
        with frame_right:
            if st.session_state["show_delete_panel"]:
                st.markdown("<h4 style='color: #ef4444; margin-top: 0px;'>⚙️ 데이터 삭제 및 청소 관리 센터</h4>", unsafe_allow_html=True)
                st.markdown("<p style='font-size:13px; color:#64748b;'>선택 과목의 CSV 데이터 파괴 및 마스터 연동 삭제를 선별 관리합니다.</p>", unsafe_allow_html=True)
                
                tab_del_sem, tab_del_sub = st.tabs(["학기 및 학년별 삭제", "과목 일괄 삭제"])
                
                # 1) 학기 및 학년별 삭제 모드
                with tab_del_sem:
                    existing_dbs = get_active_databases()
                    if not existing_dbs:
                        st.info("현재 디스크에 누적 보관 중인 학기별 데이터베이스가 없습니다.")
                    else:
                        st.markdown("<div style='font-size:12px; font-weight:600; color:#475569; margin-bottom:4px;'>1. 폐기 타격할 분기 학기 데이터베이스 지정</div>", unsafe_allow_html=True)
                        sem_opts = [f"📚 {d['subject']} | {d['grade']} | {d['semester']}" for d in existing_dbs]
                        selected_sem_str = st.selectbox("삭제 대상 선택", options=sem_opts, label_visibility="collapsed", key="sb_delete_target_sem")
                        
                        target_idx = sem_opts.index(selected_sem_str)
                        t_db = existing_dbs[target_idx]
                        
                        verify_code_sem = f"{t_db['subject']}_{t_db['grade'].replace('학년','')}_{t_db['semester'].replace('학년도','').replace(' ', '')}"
                        
                        st.markdown(f"""<div style="background-color:#fff3cd; padding:10px; border-radius:6px; font-size:12px; color:#664d03; margin-bottom:10px;">
                        ⚠️ <b>경고:</b> 과목의 대분류 틀은 안전히 보존하되, <b>[{t_db['subject']} - {t_db['grade']} {t_db['semester']}]</b>에 구성된 데이터 원본을 완전 파괴합니다.
                        </div>""", unsafe_allow_html=True)
                        
                        st.markdown(f"<div style='font-size:12px; margin-bottom:4px;'>데이터 오작동 전면 방지를 위해 아래 코드를 똑같이 입력해 주세요.<br>👉 인증코드: <code style='background:#f1f5f9; padding:2px 4px; border-radius:4px; font-weight:bold; color:#ef4444;'>{verify_code_sem}</code></div>", unsafe_allow_html=True)
                        user_confirm_sem = st.text_input("인증코드 입력창", placeholder="인증코드를 대소문자/공백 없이 정확히 치세요", label_visibility="collapsed", key="ti_verify_sem_code")
                        
                        btn_disabled_sem = (user_confirm_sem != verify_code_sem)
                        if st.button("🔒 선택 학기 데이터 영구 폐기 실행", disabled=btn_disabled_sem, type="primary", use_container_width=True, key="btn_execute_delete_sem"):
                            cf, sf = get_file_names(t_db['subject'], t_db['grade'].replace("학년",""), t_db['semester'])
                            if os.path.exists(cf): os.remove(cf)
                            if os.path.exists(sf): os.remove(sf)
                            st.toast("🎉 선택하신 분기 학기 데이터 클렌징 완료!")
                            st.rerun()

                # 2) 과목 일괄 삭제 모드
                with tab_del_sub:
                    raw_subjects = load_master_subjects()
                    flat_subs = sorted(list(set([sub for list_sub in raw_subjects.values() for sub in list_sub])))
                    
                    if not flat_subs:
                        st.info("등록 개설된 교과목 마스터 목록이 비어 있습니다.")
                    else:
                        st.markdown("<div style='font-size:12px; font-weight:600; color:#475569; margin-bottom:4px;'>1. 마스터 데이터베이스에서 완전히 영구 말소할 과목 선택</div>", unsafe_allow_html=True)
                        selected_sub_to_del = st.selectbox("과목명 선택", options=flat_subs, label_visibility="collapsed", key="sb_delete_target_sub")
                        
                        st.markdown(f"""<div style="background-color:#f8d7da; padding:10px; border-radius:6px; font-size:12px; color:#721c24; margin-bottom:10px;">
                        🚫 <b>치명적 경고 (연쇄 삭제):</b> 과목 마스터 데이터를 소멸시키면 과목 목록 자체에서 완전 증발함과 동시에, 현재 서버 디스크에 백업 보관 중인 <b>해당 과목의 모든 학년, 모든 분기 학기 성적 CSV 원본 파일이 연쇄 추적되어 흔적 없이 일괄 파괴</b>됩니다!
                        </div>""", unsafe_allow_html=True)
                        
                        st.markdown(f"<div style='font-size:12px; margin-bottom:4px;'>대형 사고 전면 방지를 위해 삭제할 교과목 명칭을 정확히 타이핑하세요.<br>👉 과목명 확인: <code style='background:#f1f5f9; padding:2px 4px; border-radius:4px; font-weight:bold; color:#ef4444;'>{selected_sub_to_del}</code></div>", unsafe_allow_html=True)
                        user_confirm_sub = st.text_input("과목명 재입력창", placeholder="위 교과 명칭을 토씨 하나 틀리지 않게 치세요", label_visibility="collapsed", key="ti_verify_sub_code")
                        
                        btn_disabled_sub = (user_confirm_sub != selected_sub_to_del)
                        if st.button("🚨 마스터 교과 및 하위 데이터 연쇄 일괄 파괴 실행", disabled=btn_disabled_sub, type="primary", use_container_width=True, key="btn_execute_delete_sub"):
                            remove_subject_completely_from_disk(selected_sub_to_del)
                            st.session_state.active_subject = None
                            st.toast(f"🎉 [{selected_sub_to_del}] 교과 및 하위 종속 파일 일괄 영구 소멸 완료!")
                            st.rerun()

            elif has_active:
                sub = st.session_state.active_subject
                grd = st.session_state.active_grade
                sem = st.session_state.active_semester
                
                cf, sf = get_file_names(sub, grd, sem)
                conf = load_config(cf)
                
                st.markdown(f"<div style='background-color:#eff6ff; border:1px solid #bfdbfe; padding:8px 12px; border-radius:6px; margin-bottom:12px; text-align:center; font-size:13px; font-weight:600; color:#1e40af;'>📍 작업 구역: [{sub}] {grd}학년 ({sem})</div>", unsafe_allow_html=True)
                st.markdown("<h4 style='color: #1e293b; margin-top: 0px;'>📌 학기 및 평가 세팅</h4>", unsafe_allow_html=True)
                
                with st.container(border=True):
                    if conf:
                        st.markdown(f"<div style='font-size:13px; font-weight:600; color:#16a34a; margin-bottom:8px;'>✅ 기존 설정 불러오기 완료 ({sem})</div>", unsafe_allow_html=True)
                        saved_cl = [int(x) for x in str(conf.get('선택된반 목록', '')).split(",") if x.strip()]
                        default_items_count = int(conf.get('항목개수', 0))
                    else:
                        st.markdown(f"<div style='font-size:13px; font-weight:600; color:#3b82f6; margin-bottom:8px;'>🎯 지정 학기 연동 완료: {sem}</div>", unsafe_allow_html=True)
                        saved_cl = []
                        default_items_count = 0

                    st.markdown("<div style='margin-top:8px; margin-bottom:2px; font-size:12px; font-weight:600; color:#475569;'>🏫 담당 학급(반) 지정</div>", unsafe_allow_html=True)
                    sel_cl = []
                    cols_cl = st.columns(6)
                    for i in range(1, 13):
                        with cols_cl[(i-1)%6]:
                            if st.checkbox(f"{i}반", value=i in saved_cl, key=f"chk_class_{i}"): 
                                sel_cl.append(i)

                    st.markdown("<div style='margin-top:8px; margin-bottom:2px; font-size:12px; font-weight:600; color:#475569;'>✍️ 평가 항목 설정</div>", unsafe_allow_html=True)
                    n_item = st.number_input("평가 항목 개수", 0, 10, default_items_count, key="num_items_input")
                    item_names = []
                    
                    placeholders = ["지필평가", "포트폴리오", "실기평가", "보고서", "발표평가", "실험실습", "형성평가", "논술형평가", "독서기록", "과제물"]
                    
                    if n_item > 0:
                        cols_i = st.columns(2)
                        for i in range(1, n_item + 1):
                            with cols_i[(i-1)%2]:
                                default_val = conf.get(f'항목{i}_이름', "") if conf else ""
                                ex_name = placeholders[(i-1) % len(placeholders)]
                                item_names.append(st.text_input(
                                    f"{i}번 항목명", 
                                    value=default_val, 
                                    placeholder=f"예: {ex_name}", 
                                    key=f"item_name_input_{i}", 
                                    label_visibility="collapsed"
                                ))

                # 저장 동작 프로세스
                ready = sel_cl and n_item > 0 and all(item_names)
                if st.session_state.get("trigger_save_action", False):
                    st.session_state["trigger_save_action"] = False
                    if ready:
                        d = {"교과명":sub, "학년":grd, "학기통합명":sem, "선택된반 목록":",".join(map(str, sorted(sel_cl))), "항목개수":n_item}
                        for i, name in enumerate(item_names): d[f"항목{i+1}_이름"] = name
                        pd.DataFrame([d]).to_csv(cf, index=False)
                        st.success("🎉 학기별 설정 저장 완료!")
                        st.rerun()
                    else: st.error("❌ 학급(반) 선택 및 평가 항목 명칭을 채운 후 저장을 눌러주세요.")

                # 📊 실시간 데이터 연동 모니터 구역
                if st.session_state["show_monitor_view"]:
                    st.markdown("<hr style='margin: 15px 0 10px 0; border: none; border-top: 1px solid #cbd5e1;'>", unsafe_allow_html=True)
                    st.markdown("<h4 style='color: #0f172a; margin-top: 0px;'>📊 실시간 데이터 연동 모니터</h4>", unsafe_allow_html=True)
                    
                    with st.container(border=True):
                        if conf:
                            st.markdown(f"""
                            <div style='background:#f8fafc; border:1px solid #e2e8f0; padding:8px 10px; border-radius:6px; font-size:12px; margin-bottom:10px; color:#475569;'>
                                ✅ <b>세팅:</b> {conf.get('학기통합명', '미정')} | <b>학급:</b> {conf.get('선택된반 목록', '미정')} 반 | <b>항목:</b> {conf.get('항목개수', 0)}개 완료
                            </div>
                            """, unsafe_allow_html=True)
                        
                        df_monitor = load_students(sf)
                        if not df_monitor.empty:
                            st.markdown('<div class="monitor-table">', unsafe_allow_html=True)
                            st.dataframe(df_monitor, use_container_width=True, hide_index=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        else: st.warning("⚠️ 해당 학기의 성적 CSV 파일이 아직 업로드되지 않았습니다.")
            else:
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
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="centered")

# =========================================================================
# 🎯 [CSS 최종 완결판] 버튼 초밀착 + 삭제 탭 빨간색 테마 + 텍스트 강조 밑줄
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
        div[data-testid="stHeader"] { display: none !important; background: transparent !important; }
        footer { display: none !important; }
        
        /* 상단 패딩 최적화 */
        .block-container { padding-top: 2.5rem !important; padding-bottom: 0.5rem !important; }
        
        /* 전체 가로폭 카드 스타일 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #e2e8f0 !important;
            padding: 20px 25px 30px 25px !important; 
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            background-color: #ffffff !important;
            max-width: 1450px !important; 
            margin: 0px auto !important; 
        }

        /* 💡 [교정 1]: 메뉴 버튼 간의 간격을 강제로 박멸하여 초밀착 */
        div[data-testid="stVerticalBlock"] > div:has(div.stButton) {
            margin-bottom: -12px !important; 
            padding-bottom: 0px !important;
        }
        
        /* 💡 [교정 2]: 데이터 삭제 메인 버튼 - 빨간색 글자 + 빨간색 밑줄 세팅 */
        div:has(> button[key='side_toggle_delete_btn']) p, 
        div:has(> button[key='side_toggle_delete_btn']) span {
            color: #ef4444 !important;
            text-decoration: underline !important;
            text-decoration-color: #ef4444 !important;
            text-underline-offset: 5px !important;
            font-weight: 700 !important;
        }

        /* 💡 [교정 3]: 삭제 센터 내부 '탭(Tab)' 디자인 - 선택 시 빨간색 및 빨간 밑줄 강제 주입 */
        div[data-testid="stTabs"] button[aria-selected="true"] p {
            color: #ef4444 !important;
            font-weight: bold !important;
        }
        div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {
            background-color: #ef4444 !important;
        }

        /* 타이틀 및 서브 타이틀 글씨 크기 고정 */
        h2 { font-size: 22px !important; color: #0f172a !important; font-weight: 800 !important; margin: 5px 0 10px 0 !important; text-align: center; }
        h4 { font-size: 14px !important; font-weight: 700 !important; color: #475569 !important; margin-bottom: 2px !important; }
        
        /* 테이블 내부 완전 중앙 정렬 */
        div.monitor-table table th, div.monitor-table table td { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# --- [보안] 암호 복잡도 검사 함수 ---
def is_strong_password(pw):
    if len(pw) < 12: return False, "❌ 최소 12자리 이상이어야 합니다."
    if not re.search("[a-zA-Z]", pw): return False, "❌ 영문자가 포함되어야 합니다."
    if not re.search("[0-9]", pw): return False, "❌ 숫자가 포함되어야 합니다."
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", pw): return False, "❌ 특수문자가 포함되어야 합니다."
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
                group, sub = row['교과군'], row['과목명']
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
        try: return str(pd.read_csv(META_FILE).iloc[0]['password']).strip()
        except: pass
    return "1234"

def save_admin_password(new_pw):
    pd.DataFrame([{"password": str(new_pw).strip()}]).to_csv(META_FILE, index=False)

def get_file_names(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    safe_semester = semester_str.replace(" ", "_").replace("/", "_")
    return f"config_{safe_subject}_{grade}grade_{safe_semester}.csv", f"students_{safe_subject}_{grade}grade_{safe_semester}.csv"

def load_config(file):
    if os.path.exists(file):
        try: return pd.read_csv(file).iloc[0].to_dict()
        except: return None
    return None

def load_students(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

def get_active_databases():
    active_list = []
    for f in glob.glob("config_*.csv"):
        try:
            filename = os.path.basename(f)
            if filename == CONFIG_FILE_MAIN: continue
            match = re.search(r"config_(.+?)_(1|2|3)grade_(.+)\.csv", filename)
            if match:
                active_list.append({"subject": match.group(1).replace("_", " "), "grade": f"{match.group(2)}학년", "semester": match.group(3).replace("_", " ")})
        except: pass
    return active_list

def remove_subject_completely_from_disk(sub_name):
    if os.path.exists(CONFIG_FILE_MAIN):
        try:
            df = pd.read_csv(CONFIG_FILE_MAIN)
            df = df[df["과목명"] != sub_name]
            df.to_csv(CONFIG_FILE_MAIN, index=False)
        except: pass
    safe_sub = sub_name.replace(" ", "_")
    for f in (glob.glob(f"config_{safe_sub}_*.csv") + glob.glob(f"students_{safe_sub}_*.csv")):
        try: os.remove(f)
        except: pass

def reset_all_data():
    for f in (glob.glob("config_*.csv") + glob.glob("students_*.csv") + [CONFIG_FILE_MAIN, META_FILE]):
        try: os.remove(f)
        except: pass
    st.session_state.clear()
    st.rerun()

# --- 팝업 모달 함수 ---
@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict):
    st.table(pd.DataFrame(scores_dict))
    if st.button("확인 후 닫기", use_container_width=True, type="primary"): st.rerun()

@st.dialog("🔐 관리자 암호 수정")
def password_update_dialog():
    new_pw = st.text_input("1. 새 암호 입력", type="password")
    confirm_pw = st.text_input("2. 새 암호 확인", type="password")
    is_valid, msg = is_strong_password(new_pw)
    if new_pw and new_pw == confirm_pw and is_valid: st.success("✅ 암호 조건 일치")
    if st.button("저장", disabled=not (is_valid and new_pw == confirm_pw), type="primary", use_container_width=True):
        save_admin_password(new_pw); st.rerun()

# --- 세션 상태 초기화 ---
for key, val in [("page_status", "student_main"), ("admin_logged_in", False), ("show_monitor_view", False), ("show_delete_panel", False)]:
    if key not in st.session_state: st.session_state[key] = val

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 선택", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]
CURRENT_ADMIN_PW = load_admin_password()

# ==========================================
# 🔄 화면 분기 구동 영역
# ==========================================
if st.session_state["page_status"] == "student_main":
    col_empty, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("🔓 교사용 제어판", key="outer_teacher_btn"): st.session_state["page_status"] = "teacher_auth"; st.rerun()
    active_dbs = get_active_databases()
    with st.container(border=True):
        st.markdown("<h2 style='text-align: center;'>🎒 수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        if not active_dbs: st.warning("현재 등록된 성적 데이터가 없습니다.")
        else:
            opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs]
            sel_s = st.selectbox("조회 과목", opts_s, label_visibility="collapsed")
            if sel_s != "과목 및 학기를 선택하세요.":
                db = active_dbs[opts_s.index(sel_s)-1]
                cf, sf = get_file_names(db['subject'], db['grade'].replace("학년",""), db['semester'])
                config = load_config(cf)
                if config:
                    with st.form("login_form"):
                        classes = [f"{x.strip()}반" for x in str(config['선택된반 목록']).split(",")]
                        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
                        with c1: b_in = st.selectbox("반", classes)
                        with c2: n_in = st.number_input("번호", 1, 50, 1)
                        with c3: name_in = st.text_input("이름")
                        with c4: pw_in = st.text_input("비번", type="password")
                        if st.form_submit_button("🔍 내 점수 확인", use_container_width=True, type="primary"):
                            df_st = load_students(sf)
                            res = df_st[(df_st['반']==int(b_in.replace("반",""))) & (df_st['번호']==n_in) & (df_st['이름']==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                            if not res.empty:
                                scores, total_sum, idx = {}, 0, res.index[0]
                                for i in range(int(config['항목개수'])):
                                    h_name = config.get(f'항목{i+1}_이름', f'수행{i+1}')
                                    val = df_st.loc[idx, h_name]; scores[h_name] = [val]; total_sum += float(val or 0)
                                scores['합계'] = [int(total_sum) if total_sum.is_integer() else round(total_sum, 2)]
                                df_st.loc[idx, '확인여부'], df_st.loc[idx, '확인시간'] = "확인 완료", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                df_st.to_csv(sf, index=False); show_result_dialog(name_in, scores)
                            else: st.error("❌ 정보 불일치")

elif st.session_state["page_status"] == "teacher_auth":
    with st.form("admin_login_form"):
        st.markdown("<h2 style='text-align: center;'>⚙️ 교과 통합 관리자</h2>", unsafe_allow_html=True)
        admin_pw = st.text_input("비밀번호", type="password")
        if st.form_submit_button("로그인", use_container_width=True, type="primary"):
            if admin_pw == CURRENT_ADMIN_PW: st.session_state["admin_logged_in"] = True; st.session_state["page_status"] = "teacher_main"; st.rerun()
            else: st.error("❌ 비밀번호 오류")
    if st.button("🎒 학생 화면으로 돌아가기", use_container_width=True): st.session_state["page_status"] = "student_main"; st.rerun()

elif st.session_state["page_status"] == "teacher_main":
    if not st.session_state["admin_logged_in"]: st.session_state["page_status"] = "teacher_auth"; st.rerun()
    col_empty, col_pw, col_logout = st.columns([5, 1.4, 1.4])
    with col_pw: 
        if st.button("🔐 암호 변경", use_container_width=True): password_update_dialog()
    with col_logout:
        if st.button("🎒 학생 화면", use_container_width=True): 
            st.session_state["admin_logged_in"] = False; st.session_state["page_status"] = "student_main"; st.rerun()

    with st.container(border=True):
        st.markdown("<h2>⚙️ 교과·학년 통합 제어 센터</h2>", unsafe_allow_html=True)
        frame_left, frame_right = st.columns([1.4, 4.2])
        has_active = "active_subject" in st.session_state and st.session_state.active_subject

        with frame_left:
            st.markdown("<h4>📁 대상 과목 선택</h4>", unsafe_allow_html=True)
            sel_g = st.selectbox("교과군", ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목"], label_visibility="collapsed")
            final_sub = ""
            if sel_g == "➕ 신규 과목": final_sub = st.text_input("새 과목명")
            elif sel_g != "교과군 선택":
                sel_s = st.selectbox("과목", ["과목 선택"] + SUBJECT_MAP[sel_g], label_visibility="collapsed")
                if sel_s != "과목 선택": final_sub = sel_s
            sel_gr = st.selectbox("학년", GRADE_OPTIONS, label_visibility="collapsed")
            sel_se = st.selectbox("학기", SEMESTER_OPTIONS, label_visibility="collapsed")

            if st.button("🚀 과목 활성화", use_container_width=True, type="primary", key="side_activate_btn"):
                if final_sub and sel_gr != "학년 선택" and sel_se != "학기 선택":
                    if sel_g == "➕ 신규 과목": save_new_subject_to_master(sel_g, final_sub)
                    st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester = final_sub, sel_gr.replace("학년",""), sel_se
                    st.rerun()
                else: st.warning("모든 항목을 선택하세요.")

            # 💡 [문구/디자인]: 빨간색 밑줄 강조가 들어간 삭제 버튼
            del_label = "🚨 데이터 삭제 닫기" if st.session_state["show_delete_panel"] else "🚨 데이터 삭제"
            if st.button(del_label, key="side_toggle_delete_btn", use_container_width=True):
                st.session_state["show_delete_panel"] = not st.session_state["show_delete_panel"]
                st.session_state["show_monitor_view"] = False; st.rerun()

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            if st.button(f"💾 설정 저장", disabled=not has_active, use_container_width=True, key="side_save_btn"):
                st.session_state["trigger_save"] = True
            if st.button("👥 학생 입력 확인", disabled=not has_active, use_container_width=True, key="side_monitor_btn"):
                st.session_state["show_monitor_view"] = not st.session_state["show_monitor_view"]; st.rerun()
            if st.button("➕ 과목 추가"): 
                st.session_state.active_subject = None; st.rerun()
            if st.button("🗑️ 시스템 초기화"): reset_all_data()

        with frame_right:
            # 💡 [교정 4]: 삭제 센터 내부 - 그림과 똑같은 탭 디자인 적용
            if st.session_state["show_delete_panel"]:
                st.markdown("<h4 style='color: #ef4444;'>⚙️ 데이터 삭제 관리</h4>", unsafe_allow_html=True)
                tab_sem, tab_sub = st.tabs(["학기 및 학년별 삭제", "과목 일괄 삭제"])
                with tab_sem:
                    existing = get_active_databases()
                    if not existing: st.info("데이터가 없습니다.")
                    else:
                        target = st.selectbox("폐기 대상", [f"📚 {d['subject']} | {d['grade']} | {d['semester']}" for d in existing])
                        verify = target.split("|")[0].replace("📚 ","").strip()
                        user_code = st.text_input(f"인증코드: {verify}")
                        if st.button("🔥 폐기 실행", disabled=user_code != verify, type="primary"):
                            cf, sf = get_file_names(verify, target.split("|")[1].replace("학년","").strip(), target.split("|")[2].strip())
                            if os.path.exists(cf): os.remove(cf)
                            if os.path.exists(sf): os.remove(sf)
                            st.success("삭제 완료"); st.rerun()
                with tab_sub:
                    raw = load_master_subjects()
                    flat = sorted(list(set([s for l in raw.values() for s in l])))
                    target_sub = st.selectbox("말소 과목", flat)
                    user_sub = st.text_input(f"과목명 재입력: {target_sub}")
                    if st.button("🚨 일괄 삭제", disabled=user_sub != target_sub, type="primary"):
                        remove_subject_completely_from_disk(target_sub); st.rerun()

            elif has_active:
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                cf, sf = get_file_names(sub, grd, sem)
                conf = load_config(cf)
                st.markdown(f"<div style='background-color:#eff6ff; padding:10px; border-radius:6px; font-weight:600; color:#1e40af; text-align:center;'>📍 작업 중: [{sub}] {grd}학년 ({sem})</div>", unsafe_allow_html=True)
                
                with st.container(border=True):
                    sel_cl = []
                    saved_cl = [int(x) for x in str(conf.get('선택된반 목록','')).split(",") if x.strip()] if conf else []
                    cols = st.columns(6)
                    for i in range(1, 13):
                        with cols[(i-1)%6]:
                            if st.checkbox(f"{i}반", value=i in saved_cl, key=f"cl_{i}"): sel_cl.append(i)
                    n_item = st.number_input("평가 항목 개수", 1, 10, int(conf.get('항목개수', 1)) if conf else 1)
                    item_names = []
                    cols_i = st.columns(2)
                    for i in range(n_item):
                        with cols_i[i%2]:
                            item_names.append(st.text_input(f"{i+1}번 항목명", value=conf.get(f'항목{i+1}_이름','') if conf else ""))

                if st.session_state.get("trigger_save"):
                    st.session_state["trigger_save"] = False
                    if sel_cl and all(item_names):
                        d = {"교과명":sub, "학년":grd, "학기통합명":sem, "선택된반 목록":",".join(map(str, sorted(sel_cl))), "항목개수":n_item}
                        for i, name in enumerate(item_names): d[f"항목{i+1}_이름"] = name
                        pd.DataFrame([d]).to_csv(cf, index=False); st.success("저장 완료"); st.rerun()

                if st.session_state["show_monitor_view"]:
                    st.markdown("<h4>📊 실시간 모니터</h4>", unsafe_allow_html=True)
                    df_m = load_students(sf)
                    if not df_m.empty: st.dataframe(df_m, use_container_width=True, hide_index=True)
                    else: st.info("성적 CSV를 업로드해 주세요.")
            else: st.info("👈 과목을 활성화해 주세요.")st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                st.info("👈 왼쪽 제어판에서 과목 사양을 선택한 뒤 [🚀 과목 활성화] 또는 [🛠️ 데이터 삭제]를 클릭해 주세요.")

        # 최하단 가이드 바
        st.markdown("<div class='custom-guide-bar'>💡 <b>[🚀 과목 활성화]</b>를 누르시면 해당 과목의 <b style='color:#ef4444; font-size:15px; background-color:#ffe4e6; padding:3px 6px; border-radius:4px;'>[만들기 및 불러오기]</b>가 됩니다.</div>", unsafe_allow_html=True)