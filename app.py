import streamlit st
import pandas as pd
import os
from datetime import datetime
import io
import glob
import re
import gspread
from google.oauth2.service_account import Credentials
import csv
import profile_pop

# 🚨 [최상단 규칙 엄수] 와이드 레이아웃 설정
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="wide")

# =========================================================================
# 🔄 [수동 여백 조정 마스터 CSS] 숫자로 직접 밀어버리는 레이아웃
# =========================================================================
st.markdown("""
    <style>
        /* 기본 배경 격리 */
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        [data-testid="stSidebar"], section[data-testid="stSidebar"] { min-width: 260px !important; max-width: 260px !important; background-color: #1e293b !important; box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; }
        [data-testid="stAppViewContainer"] { margin-left: 0px !important; }

        /* 사이드바 고유 버튼 무전역 고정 */
        [data-testid="stSidebar"] button[kind="primary"] { background-color: #3b82f6 !important; border: 2px solid #2563eb !important; color: #ffffff !important; border-radius: 6px !important; font-weight: 700 !important; padding: 10px 16px !important; width: 100% !important; display: block !important; }
        [data-testid="stSidebar"] button[kind="secondary"] { background-color: #475569 !important; border: 2px solid #334155 !important; color: #ffffff !important; border-radius: 6px !important; font-weight: 700 !important; padding: 10px 16px !important; width: 100% !important; display: block !important; }
        [data-testid="stDialog"] button[kind="primary"] { background-color: #ef4444 !important; color: #ffffff !important; font-weight: 800 !important; border: none !important; border-radius: 6px !important; padding: 12px 0 !important; font-size: 15px !important; width: 100% !important; }

        /* -------------------------------------------------------------------------------- */
        /* 🚨 2. 하얀색 로그인 박스 외형 정의 */
        /* -------------------------------------------------------------------------------- */
        div[data-testid="stForm"] {
            background-color: #ffffff !important; 
            border: 1px solid #cbd5e1 !important;
            padding: 45px 40px 45px 40px !important; 
            border-radius: 24px !important;
            box-shadow: 0 15px 40px rgba(0,0,0,0.06) !important; 
            max-width: 440px !important; 
            margin: 70px auto 0 auto !important; 
        }
        
        /* 제목 정중앙 정렬 */
        div[data-testid="stForm"] h2 {
            font-size: 26px !important; 
            white-space: nowrap !important; 
            text-align: center !important; 
            margin: 0 auto 20px auto !important;
            font-weight: 800 !important;
            color: #0f172a !important;
        }

        /* 🚨 [핵심] 라디오 버튼을 숫자를 써서 수동으로 우측 이동 (원하는 만큼 숫자 조절 가능) */
        div[data-testid="stForm"] div[data-testid="stRadio"] {
            padding-left: 55px !important; /* 👈 이 숫자를 늘리면 우측으로 더 이동하고, 줄이면 좌측으로 갑니다 */
            margin-bottom: 20px !important;
        }
        div[data-testid="stForm"] div[role="radiogroup"] {
            display: flex !important;
            gap: 60px !important; /* 학생과 교사 버튼 사이의 간격 */
            align-items: center !important;
        }
        div[data-testid="stForm"] div[role="radiogroup"] label p {
            margin: 0 0 0 8px !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            color: #334155 !important;
        }

        /* 🚨 3. 입력 필드 및 비밀번호 보기 버튼 뒷배경 흰색 잔상 완전 소멸 */
        div[data-testid="stTextInput"] div[data-baseweb="input"] { 
            background-color: #f8fafc !important; 
            border: 2px solid #e2e8f0 !important; 
            border-radius: 8px !important; 
            overflow: hidden !important;
        }
        div[data-testid="stTextInput"] div[data-baseweb="base-input"], 
        div[data-testid="stTextInput"] input { background-color: transparent !important; }
        div[data-testid="stTextInput"] div[data-styled-inner-component="true"] { background-color: transparent !important; }
        div[data-testid="stTextInput"] button { background-color: transparent !important; border: none !important; box-shadow: none !important; color: #64748b !important; }

        /* 🚨 4. 제출 버튼 스타일 고정 */
        div[data-testid="stFormSubmitButton"] button {
            background-color: #4a69bd !important;
            color: #ffffff !important;
            font-weight: bold !important;
            border: none !important;
            padding: 0.75rem 0 !important;
            border-radius: 8px !important;
            font-size: 16px !important;
            box-shadow: 0 4px 12px rgba(74, 105, 189, 0.2) !important;
        }
        
        .footer-container { width: 100%; display: flex; justify-content: center; margin-top: 25px; }
        .footer-text { text-align: center; font-size: 12px; color: #94a3b8; font-weight: 500; }
        h3 { color: #1e293b !important; font-weight: 700 !important; font-size: 20px !important; margin-top: 0px !important; margin-bottom: 5px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 백엔드 데이터 연동 함수 정의 ---
def load_master_subjects():
    default_structure = {"인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"], "수리·과학군": ["수학", "과학", "기술·가정", "정보"], "예체능군": ["음악", "미술", "체육"]}
    df = load_sheet_to_df("master_subjects", ["교과군", "과목명"])
    if not df.empty:
        for _, row in df.iterrows():
            group = str(row['교과군']).strip()
            sub = str(row['과목명']).strip()
            if group in default_structure and sub not in default_structure[group]: default_structure[group].append(sub)
    return default_structure

def save_new_subject_to_master(group, subject):
    df = load_sheet_to_df("master_subjects", ["교과군", "과목명"])
    if not ((df['교과군'] == group) & (df['과목명'] == subject)).any():
        new_row = pd.DataFrame([{"교과군": group, "과목명": subject}])
        df = pd.concat([df, new_row], ignore_index=True)
        save_df_to_sheet("master_subjects", df)

def verify_teacher_credentials(input_id, input_pw):
    df = load_sheet_to_df("teacher_accounts", ["교사_ID", "비밀번호", "교사_성명", "담당_과목"])
    if not df.empty:
        df['교사_ID'] = df['교사_ID'].astype(str).str.strip()
        df['비밀번호'] = df['비밀번호'].astype(str).str.strip()
        match = df[(df['교사_ID'] == str(input_id).strip()) & (df['비밀번호'] == str(input_pw).strip())]
        if not match.empty:
            row = match.iloc[0]
            return {"success": True, "teacher_id": str(row['교사_ID']).strip(), "teacher_name": str(row['교사_성명']).strip(), "authorized_subjects": [s.strip() for s in str(row['담당_과목']).split(",") if s.strip()]}
    if input_id.strip() == "admin" and input_pw.strip() == "1234": return {"success": True, "teacher_id": "admin", "teacher_name": "최고관리자", "authorized_subjects": ["마스터"]}
    return {"success": False, "teacher_name": "", "authorized_subjects": []}

def get_sheet_names_id(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    return f"cfg_{safe_subject}_{grade}Grade", f"st_{safe_subject}_{grade}_{semester_str.replace(' ', '_').replace('/', '_')}"

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict, sf_id, student_row_idx, current_df):
    st.markdown(f"<div><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True)
    st.table(pd.DataFrame(scores_dict))
    if "has_counted" not in st.session_state:
        try: current_count = int(current_df.loc[student_row_idx, "성적조회 횟수"]) if "성적조회 횟수" in current_df.columns and not pd.isna(current_df.loc[student_row_idx, "성적조회 횟수"]) else 0
        except: current_count = 0
        current_df.loc[student_row_idx, "성적조회 횟수"] = current_count + 1
        current_df.loc[student_row_idx, "최종 확인일시"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_df_to_sheet(sf_id, current_df)
        st.session_state["has_counted"] = True
    if st.button("닫기", type="secondary", use_container_width=True):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.session_state.clear()
        st.rerun()

def init_google_sheet_client():
    try: return gspread.authorize(Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except: return None

gc = init_google_sheet_client()
SPREADSHEET_NAME = "수행평가_데이터베이스"

def get_google_sheet(sheet_name):
    if gc is None: return None
    try:
        sh = gc.open(SPREADSHEET_NAME)
        try: return sh.worksheet(sheet_name)
        except: return sh.add_worksheet(title=sheet_name, rows="100", cols="20")
    except: return None

def save_df_to_sheet(sheet_name, df):
    wks = get_google_sheet(sheet_name)
    if wks is None: return False
    try:
        wks.clear()
        wks.update(range_name="A1", values=[df.fillna("").columns.tolist()] + df.fillna("").values.tolist())
        return True
    except: return False

def load_sheet_to_df(sheet_name, default_cols=None):
    wks = get_google_sheet(sheet_name)
    if wks is None: return pd.DataFrame(columns=default_cols if default_cols else [])
    try:
        records = wks.get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=default_cols if default_cols else [])
    except: return pd.DataFrame(columns=default_cols if default_cols else [])

def get_active_databases():
    active_list = []
    if gc is None: return active_list
    try:
        sh = gc.open(SPREADSHEET_NAME)
        for wks in sh.worksheets():
            if wks.title.startswith("cfg_"):
                match = re.search(r"cfg_([A-Za-z0-9_]+)_([1-3])Grade", wks.title)
                if match: active_list.append({"subject": match.group(1).replace("_", " "), "grade": f"{match.group(2)}학년", "semester": "2026학년도 1학기"})
    except: pass
    return active_list

# 세션 상태 초기화
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "student_logged_in" not in st.session_state: st.session_state["student_logged_in"] = False
if "logged_student_id" not in st.session_state: st.session_state["logged_student_id"] = ""
if "logged_student_pw" not in st.session_state: st.session_state["logged_student_pw"] = ""
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = ""
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = ""
if "allowed_subjects" not in st.session_state: st.session_state["allowed_subjects"] = []

SUBJECT_MAP = load_master_subjects()

def sidebar_logout_callback():
    st.session_state["admin_logged_in"] = False
    st.session_state["logged_teacher_id"] = ""
    st.session_state["teacher_name"] = ""
    st.session_state["allowed_subjects"] = []

if "open_profile_popup" not in st.session_state: st.session_state["open_profile_popup"] = False
if st.session_state["open_profile_popup"]:
    st.session_state["open_profile_popup"] = False
    launch_isolated_profile_dialog()

# =========================================================================
# 🔓 [1단계] 클린 통합 로그인 시스템 (동적 텍스트 및 수평 영점 박제)
# =========================================================================
if not st.session_state["admin_logged_in"] and not st.session_state["student_logged_in"]:
    with st.form("master_unified_form"):
        st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        
        # 🚨 [순서 교정 완료] 무조건 학생이 1번, 교사가 2번으로 나오도록 스왑 완료!
        login_mode = st.radio("접속 모드", ["학생", "교사"], horizontal=True, label_visibility="collapsed")
            
        placeholder_text = "학생 ID(이메일)를 입력하세요" if login_mode == "학생" else "교사 ID를 입력하세요"
        
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            
        user_id_input = st.text_input("ID", placeholder=placeholder_text, label_visibility="collapsed")
        user_pw_input = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed")
        
        # 🚨 순정 컬럼 분할로 로그인 버튼을 가로 180px 크기로 정중앙 배치
        b_col1, b_col2, b_col3 = st.columns([1.0, 1.8, 1.0])
        with b_col2:
            submit_active = st.form_submit_button("시스템 로그인", use_container_width=True)
        
        if submit_active:
            if login_mode == "교사":
                auth_result = verify_teacher_credentials(user_id_input, user_pw_input)
                if auth_result["success"]:
                    st.session_state["admin_logged_in"] = True
                    st.session_state["logged_teacher_id"] = auth_result["teacher_id"]
                    st.session_state["teacher_name"] = auth_result["teacher_name"]
                    st.session_state["allowed_subjects"] = auth_result["authorized_subjects"]
                    st.rerun()
                else: st.error("❌ 교사 ID 또는 비밀번호 오류")
            elif login_mode == "학생":
                if user_id_input and user_pw_input:
                    st.session_state["student_logged_in"] = True
                    st.session_state["logged_student_id"] = user_id_input.strip()
                    st.session_state["logged_student_pw"] = user_pw_input.strip()
                    st.rerun()
                else: st.error("❌ 학생 ID와 비밀번호를 모두 입력하세요.")

    st.markdown("<div class='footer-container'><div class='footer-text'>Designed & Developed by User & AI Creator</div></div>", unsafe_allow_html=True)

# =========================================================================
# 🎓 [2단계-A] 분리 개설된 학생 전용 과목 선택 대시보드
# =========================================================================
elif st.session_state["student_logged_in"]:
    st.markdown(f"<h2>수행평가 점수 확인 시스템 <span style='font-size:16px; color:#3b82f6;'>(학생 모드)</span></h2>", unsafe_allow_html=True)
    if st.button("🚪 안전 로그아웃"):
        st.session_state["student_logged_in"] = False
        st.rerun()
    st.write(f"👤 접속 이메일: **{st.session_state['logged_student_id']}**")
    st.markdown("---")
    
    active_dbs = get_active_databases()
    if not active_dbs:
        st.warning("현재 평가 데이터베이스에 활성화된 과목 파티션이 존재하지 않습니다.")
    else:
        opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']})" for d in active_dbs]
        sel_s = st.selectbox("조회할 교과과정 선택", opts_s)
        
        if sel_s != "과목 및 학기를 선택하세요.":
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 나의 수행평가 성적 실시간 검증", type="primary", use_container_width=True):
                db = active_dbs[opts_s.index(sel_s)-1]
                cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                config = load_sheet_to_df(cf_id).iloc[0].to_dict() if not load_sheet_to_df(cf_id).empty else None
                
                if config:
                    df_st = load_sheet_to_df(sf_id)
                    if not df_st.empty:
                        st_id = st.session_state["logged_student_id"]
                        st_pw = st.session_state["logged_student_pw"]
                        
                        if "school_email" in df_st.columns:
                            res = df_st[(df_st['school_email'].astype(str).str.strip() == str(st_id)) & (df_st['비밀번호'].astype(str) == str(st_pw))]
                        else:
                            res = df_st[(df_st['이름'].astype(str).str.strip() == str(st_id)) & (df_st['비밀번호'].astype(str) == str(st_pw))]
                            
                        if not res.empty:
                            idx = res.index[0]
                            st_name = res.iloc[0].get('이름', '학생')
                            scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                            show_result_dialog(st_name, scores, sf_id, idx, df_st)
                        else: 
                            st.error("❌ 입력하신 로그인 계정 정보와 일치하는 성적 대장 데이터 행을 찾을 수 없습니다.")

# =========================================================================
# 🔒 [2단계-B] 교사 마스터 제어 대시보드
# =========================================================================
elif st.session_state["admin_logged_in"]:
    with st.sidebar:
        st.markdown("<h4>📋 교사 메뉴</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:12px; color:#94a3b8; margin-bottom:15px;'>👤 {st.session_state['teacher_name']} 선생님 접속 중</div>", unsafe_allow_html=True)
        st.markdown("---")
        menu_selection = st.radio("메뉴 선택", ["▶ 학생 조회 현황 모니터링", "▶ 개인별 성적 입력", "▶ 평가 대상 과목 구성", "▶ 성적 전체 일괄 업로드(CSV)"], label_visibility="collapsed")
        st.markdown("---")
        
        if st.button("🔐 내 정보 수정", type="primary", use_container_width=True):
            st.session_state["open_profile_popup"] = True
            st.rerun()
            
        st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)
        st.button("🚪 시스템 로그아웃", type="secondary", use_container_width=True, on_click=sidebar_logout_callback)

    st.markdown(f"<h2>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
    st.write(f"현재 위치: 교사 모드 > {menu_selection}")
    st.markdown("<div style='text-align:center; height: 5px;'></div>", unsafe_allow_html=True)

    # 📊 모듈 1: 학생 조회 현황 모니터링
    if menu_selection == "▶ 학생 조회 현황 모니터링":
        with st.container(border=True):
            st.markdown(f"<h3>📊 학생별 조회 이력 및 성적 현황 모니터링</h3>", unsafe_allow_html=True)
            
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]:
                registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
                
            if not registered_dbs:
                st.warning("⚠️ 현재 개설 파티션이 없습니다.")
            else:
                col_sub, col_class = st.columns(2)
                with col_sub:
                    selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                    selected_db_str = st.selectbox("📂 대상 교과 선택", options=selector_options)
                    chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                
                cf_id, sf_id = get_sheet_names_id(chosen_db['subject'], chosen_db['grade'].replace("학년",""), chosen_db['semester'])
                db_df = load_sheet_to_df(sf_id)
                cfg_df = load_sheet_to_df(cf_id)
                
                with col_class:
                    class_options = ["전체 학급 보기"]
                    if not db_df.empty and "반" in db_df.columns:
                        class_options = ["전체 학급 보기"] + [f"{x}반" for x in sorted(db_df['반'].unique())]
                    selected_class = st.selectbox("🎯 필터링할 학급 선택", options=class_options)
                
                if not db_df.empty:
                    render_df = db_df.copy()
                    if selected_class != "전체 학급 보기":
                        render_df = render_df[render_df['반'].astype(int) == int(selected_class.replace("반",""))]
                        
                    if not cfg_df.empty:
                        cfg_dict = cfg_df.iloc[0].to_dict()
                        cnt = int(cfg_dict.get('항목개수', 3))
                        score_headers = [cfg_dict.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(cnt)]
                    else: score_headers = []
                    
                    display_cols = ["반", "번호", "이름"]
                    if "school_email" in render_df.columns: display_cols.append("school_email")
                    display_cols.extend(score_headers)
                    display_cols.extend(["성적조회 횟수", "최종 확인일시"])
                    
                    st.dataframe(render_df[[c for c in display_cols if c in render_df.columns]].fillna("-"), use_container_width=True, hide_index=True)

    # 📝 모듈 2: 개인별 성적 입력
    elif menu_selection == "▶ 개인별 성적 입력":
        with st.container(border=True):
            st.markdown("<h3>📝 개인별 성적 데이터 편집</h3>", unsafe_allow_html=True)
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]:
                registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
                
            if not registered_dbs: st.warning("⚠️ 권한 파티션이 없습니다.")
            else:
                col_sub_ed, col_class_ed = st.columns(2)
                with col_sub_ed:
                    selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                    selected_db_str = st.selectbox("📂 관리할 교과 선택", options=selector_options)
                    chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                
                cf_id, sf_id = get_sheet_names_id(chosen_db['subject'], chosen_db['grade'].replace("학년",""), chosen_db['semester'])
                db_df = load_sheet_to_df(sf_id)
                cfg_df = load_sheet_to_df(cf_id)
                
                with col_class_ed:
                    class_options_ed = ["전체"]
                    if not db_df.empty and "반" in db_df.columns: class_options_ed = ["전체"] + [f"{x}반" for x in sorted(db_df['반'].unique())]
                    selected_class_ed = st.selectbox("👥 학반 필터링", options=class_options_ed)
                
                if not db_df.empty:
                    if not cfg_df.empty:
                        cfg_dict = cfg_df.iloc[0].to_dict()
                        cnt = int(cfg_dict.get('항목개수', 3))
                        score_headers = [cfg_dict.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(cnt)]
                    else: score_headers = []
                    
                    display_cols = ["반", "번호", "이름"]
                    if "school_email" in db_df.columns: display_cols.append("school_email")
                    if "비밀번호" in db_df.columns: display_cols.append("비밀번호")
                    display_cols.extend(score_headers)
                    
                    valid_cols = [c for c in display_cols if c in db_df.columns]
                    if selected_class_ed != "전체":
                        filtered_idx = db_df[db_df["반"].astype(int) == int(selected_class_ed.replace("반", ""))].index
                        edit_target_df = db_df.loc[filtered_idx, valid_cols]
                    else:
                        filtered_idx = db_df.index
                        edit_target_df = db_df[valid_cols]
                    
                    edited_df = st.data_editor(edit_target_df, use_container_width=True, num_rows="dynamic", disabled=["반", "번호", "이름"], hide_index=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    bc1, bc2 = st.columns([5, 1])
                    with bc2:
                        if st.button("💾 수정 저장", use_container_width=True, type="primary"):
                            for idx_pos, row_idx in enumerate(filtered_idx):
                                for col in edited_df.columns: db_df.loc[row_idx, col] = edited_df.iloc[idx_pos][col]
                            if save_df_to_sheet(sf_id, db_df):
                                st.success("🎉 저장 동기화 완료!")
                                st.rerun()

    # 📁 모듈 3: 평가 대상 과목 구성
    elif menu_selection == "▶ 평가 대상 과목 구성":
        with st.container(border=True):
            st.markdown("<h3>⚙️ 수행평가 항목 구성 및 파티션 개설</h3>", unsafe_allow_html=True)
            r1, r2 = st.columns(2)
            with r1: sel_g = st.selectbox("교과군 분류", options=["인문·사회군", "수리·과학군", "예체능군"])
            with r2: sel_gr = st.selectbox("학년 선택", options=["1학년", "2학년", "3학년"])
            
            r3, r4 = st.columns(2)
            with r3: final_sub = st.selectbox("세부 과목", options=SUBJECT_MAP.get(sel_g, ["국어"]))
            with r4: sel_se = st.selectbox("학기 선택", options=["2026학년도 1학기", "2026학년도 2학기"])
            
            item_count = st.selectbox("🎯 평가 반영 항목 개수", [1, 2, 3, 4, 5], index=2)
            item_titles = []
            cols_items = st.columns(item_count)
            for i in range(item_count):
                with cols_items[i]:
                    t_in = st.text_input(f"항목 {i+1} 제목", value=f"수행평가_{i+1}")
                    item_titles.append(t_in.strip())
            
            if st.button("🚀 기본 설정 파티션 저장 개설", type="primary", use_container_width=True):
                if "마스터" not in st.session_state["allowed_subjects"] and final_sub not in st.session_state["allowed_subjects"]:
                    st.error(f"❌ 권한 오류: 선생님은 [{final_sub}] 과목에 대한 개설 권한이 없습니다.")
                else:
                    cf_id, sf_id = get_sheet_names_id(final_sub, sel_gr.replace("학년",""), sel_se)
                    config_df = pd.DataFrame([{"선택된반 목록": "1,2,3", "항목개수": item_count, **{f"항목{k+1}_이름": item_titles[k] for k in range(item_count)}}])
                    if save_df_to_sheet(cf_id, config_df): st.success("✅ 파티션 연동 기본 설정 저장 완료!")

    # 📤 모듈 4: 성적 전체 일괄 업로드(CSV)
    elif menu_selection == "▶ 성적 전체 일괄 업로드(CSV)":
        with st.container(border=True):
            st.markdown("<h3>📥 전체 일괄 성적 대장 CSV 업로드</h3>", unsafe_allow_html=True)
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]: registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
            
            if not registered_dbs: st.warning("개설 파티션이 없습니다.")
            else:
                selected_db_str = st.selectbox("📂 성적 연동 과목 파티션 선택", options=[f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs])
                chosen_db = registered_dbs[[f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs].index(selected_db_str)]
                cf_id, sf_id = get_sheet_names_id(chosen_db['subject'], chosen_db['grade'].replace("학년",""), chosen_db['semester'])
                
                up_f = st.file_uploader("성적 대장 마스터 CSV 파일 업로드", type="csv")
                if up_f:
                    df_up = pd.read_csv(up_f, encoding='cp949')
                    if "school_email" not in df_up.columns: df_up["school_email"] = ""
                    if "성적조회 횟수" not in df_up.columns: df_up["성적조회 횟수"] = 0
                    if "최종 확인일시" not in df_up.columns: df_up["최종 확인일시"] = "-"
                    if save_df_to_sheet(sf_id, df_up): st.success("🎉 클라우드 데이터베이스 미러링 마감 성공!")