import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import glob
import re
import gspread
from google.oauth2.service_account import Credentials
import csv

# 파일 경로 정의
CONFIG_FILE_MAIN = "master_subjects.csv"
META_FILE = "admin_meta.csv"

# --- 데이터 로드/저장 시스템 (기존 구글 시트 백엔드 무결점 보존) ---
def load_master_subjects():
    default_structure = {
        "인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"],
        "수리·과학군": ["수학", "과학", "기술·가정", "정보"],
        "예체능군": ["음악", "미술", "체육"]
    }
    df = load_sheet_to_df("master_subjects", ["교과군", "과목명"])
    if not df.empty:
        for _, row in df.iterrows():
            group = str(row['교과군']).strip()
            sub = str(row['과목명']).strip()
            if group in default_structure and sub not in default_structure[group]:
                default_structure[group].append(sub)
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
            return {
                "success": True,
                "teacher_id": str(row['교사_ID']).strip(),
                "teacher_name": str(row['교사_성명']).strip(),
                "authorized_subjects": [s.strip() for s in str(row['담당_과목']).split(",") if s.strip()]
            }
            
    if input_id.strip() == "admin" and input_pw.strip() == "1234":
        return {"success": True, "teacher_id": "admin", "teacher_name": "최고관리자", "authorized_subjects": ["마스터"]}
    return {"success": False, "teacher_name": "", "authorized_subjects": []}

def get_sheet_names_id(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    safe_semester = semester_str.replace(" ", "_").replace("/", "_")
    return f"cfg_{safe_subject}_{grade}Grade", f"st_{safe_subject}_{grade}_{safe_semester}"

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict, sf_id, student_row_idx, current_df):
    st.markdown(f"<div><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True)
    st.table(pd.DataFrame(scores_dict))
    
    if "has_counted" not in st.session_state:
        try:
            current_count = int(current_df.loc[student_row_idx, "성적조회 횟수"]) if "성적조회 횟수" in current_df.columns and not pd.isna(current_df.loc[student_row_idx, "성적조회 횟수"]) else 0
        except:
            current_count = 0
            
        current_df.loc[student_row_idx, "성적조회 횟수"] = current_count + 1
        current_df.loc[student_row_idx, "최종 확인일시"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_df_to_sheet(sf_id, current_df)
        st.session_state["has_counted"] = True

    if st.button("닫기", use_container_width=True, type="primary"):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.session_state.clear()
        st.rerun()

@st.dialog("🔐 내 정보 수정")
def account_update_dialog():
    st.markdown(f"##### 👤 **{st.session_state['teacher_name']}** 선생님 정보 수정")
    df_teachers = load_sheet_to_df("teacher_accounts", ["교사_ID", "비밀번호", "교사_성명", "담당_과목"])
    
    if not df_teachers.empty and st.session_state["logged_teacher_id"] != "admin":
        target_idx = df_teachers[df_teachers['교사_ID'].astype(str).str.strip() == str(st.session_state["logged_teacher_id"]).strip()].index
        if not target_idx.empty:
            idx = target_idx[0]
            curr_pw = str(df_teachers.loc[idx, "비밀번호"]).strip()
            curr_sub = str(df_teachers.loc[idx, "담당_과목"]).strip()
            
            new_pw = st.text_input("새 비밀번호 변경", value=curr_pw, type="password")
            new_sub = st.text_input("담당 과목 변경 (콤마 분리)", value=curr_sub)
            
            if st.button("💾 변경사항 저장", use_container_width=True, type="primary"):
                if new_pw and new_sub:
                    df_teachers.loc[idx, "비밀번호"] = new_pw.strip()
                    df_teachers.loc[idx, "담당_과목"] = new_sub.strip()
                    if save_df_to_sheet("teacher_accounts", df_teachers):
                        st.success("🎉 정보가 변경되었습니다.")
                        st.session_state["allowed_subjects"] = [s.strip() for s in new_sub.split(",") if s.strip()]
                        st.rerun()
        else: st.error("계정을 찾을 수 없습니다.")
    else: st.warning("최고관리자 계정은 시트에서 직접 관리해 주세요.")

@st.dialog("➕ 학생 개별 추가")
def student_individual_add_dialog(db_df, sf_id, score_headers):
    st.markdown("##### 📝 누락 학생 개별 등록")
    ac1, ac2 = st.columns(2)
    with ac1: add_b = st.number_input("반", min_value=1, max_value=30, value=1)
    with ac2: add_n = st.number_input("번호", min_value=1, max_value=60, value=1)
    add_name = st.text_input("학생 이름")
    add_email = st.text_input("학교 이메일")
    add_pw = st.text_input("조회 비밀번호")
    
    if st.button("🚀 학생 추가 등록", use_container_width=True, type="primary"):
        if add_name and add_email and add_pw:
            new_row = {
                "반": int(add_b), "번호": int(add_n), "이름": str(add_name).strip(),
                "학교 이메일": str(add_email).strip(), "비밀번호": str(add_pw).strip(),
                "성적조회 횟수": 0, "최종 확인일시": "-"
            }
            for h in score_headers: new_row[h] = 0
            updated_df = pd.concat([db_df, pd.DataFrame([new_row])], ignore_index=True)
            if save_df_to_sheet(sf_id, updated_df):
                st.success("✅ 등록 완료!")
                st.rerun()

@st.cache_resource
def init_google_sheet_client():
    try:
        credentials_info = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        return gspread.authorize(creds)
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
        data = [df.fillna("").columns.tolist()] + df.fillna("").values.tolist()
        wks.update(range_name="A1", values=data)
        return True
    except: return False

@st.cache_data(ttl=2)
def load_sheet_to_df(sheet_name, default_cols=None):
    wks = get_google_sheet(sheet_name)
    if wks is None: return pd.DataFrame(columns=default_cols if default_cols else [])
    try:
        records = wks.get_all_records()
        if not records: return pd.DataFrame(columns=default_cols if default_cols else [])
        return pd.DataFrame(records)
    except: return pd.DataFrame(columns=default_cols if default_cols else [])

@st.cache_data(ttl=3)
def get_active_databases():
    active_list = []
    if gc is None: return active_list
    try:
        sh = gc.open(SPREADSHEET_NAME)
        for wks in sh.worksheets():
            name = wks.title
            if name.startswith("cfg_"):
                core_name = name.replace("cfg_", "")
                match = re.search(r"(.+?)_(1|2|3)_(.+)", core_name)
                if match:
                    active_list.append({
                        "subject": match.group(1).replace("_", " "),
                        "grade": f"{match.group(2)}학년",
                        "semester": match.group(3).replace("_", " ")
                    })
    except: pass
    return active_list

if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = ""
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = ""
if "allowed_subjects" not in st.session_state: st.session_state["allowed_subjects"] = []

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 지정", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]

# =========================================================================
# 🔄 CSS 스타일링 엔진 및 버튼 가독성 패키지 (강제 스펙 갱신 완료)
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] { background-color: #f1f5f9 !important; }
        [data-testid="stSidebar"] { background-color: #1e293b !important; }
        [data-testid="stSidebar"] h4, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 600; }
        div[data-testid="stSidebar"] div[role="radiogroup"] label p { color: #f8fafc !important; font-weight: 600 !important; }
        
        /* 🚨 사이드바 하단 버튼 호버 제어 완벽 마감: 모든 포커스/액티브/호버 상태에서 글자색 흰색 강제 유지 */
        div.stButton > button[key="sidebar_account_btn"] {
            background-color: #4f46e5 !important; color: #ffffff !important; border: none !important; font-weight: 700 !important;
        }
        div.stButton > button[key="sidebar_account_btn"]:hover, 
        div.stButton > button[key="sidebar_account_btn"]:active, 
        div.stButton > button[key="sidebar_account_btn"]:focus {
            background-color: #4338ca !important; color: #ffffff !important; border: none !important; box-shadow: none !important;
        }
        
        div.stButton > button[key="sidebar_logout_btn"] {
            background-color: #ef4444 !important; color: #ffffff !important; border: none !important; font-weight: 800 !important;
        }
        div.stButton > button[key="sidebar_logout_btn"]:hover, 
        div.stButton > button[key="sidebar_logout_btn"]:active, 
        div.stButton > button[key="sidebar_logout_btn"]:focus {
            background-color: #dc2626 !important; color: #ffffff !important; border: none !important; box-shadow: none !important;
        }

        /* 항목 제목 라벨 진하게 강조 */
        div[data-testid="stTextInput"] label p {
            font-weight: 900 !important; color: #1e3a8a !important; font-size: 15px !important; margin-bottom: 5px !important;
        }
        
        /* 버튼 컬러맵 정의 */
        div.stButton > button[key="btn_save_all_grid_changes"] { background-color: #3b82f6 !important; color: white !important; }
        div.stButton > button[key="btn_trigger_student_dialog"] { background-color: #10b981 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state["admin_logged_in"]:
    st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="centered")
    with st.form("master_unified_form"):
        st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        login_mode = st.radio("접속 모드", ["교사", "학생"], horizontal=True, label_visibility="collapsed")
        st.markdown("<hr>", unsafe_allow_html=True)
        if login_mode == "교사":
            admin_id = st.text_input("교사_ID", placeholder="교사 ID를 입력하세요", label_visibility="collapsed")
            admin_pw = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed")
            if st.form_submit_button("로그인", type="primary"):
                auth = verify_teacher_credentials(admin_id, admin_pw)
                if auth["success"]:
                    st.session_state.update({"admin_logged_in":True, "logged_teacher_id":auth["teacher_id"], "teacher_name":auth["teacher_name"], "allowed_subjects":auth["authorized_subjects"]})
                    st.rerun()
                else: st.error("❌ 오류")
        elif login_mode == "학생":
            active_dbs = get_active_databases()
            if active_dbs:
                opts = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs]
                sel = st.selectbox("과목", opts, label_visibility="collapsed")
                if sel != "과목 및 학기를 선택하세요.":
                    db = active_dbs[opts.index(sel)-1]
                    cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                    config = load_sheet_to_df(cf_id).iloc[0].to_dict() if not load_sheet_to_df(cf_id).empty else None
                    if config:
                        st.markdown("<hr>", unsafe_allow_html=True)
                        st_email = st.text_input("학교 이메일", placeholder="학교 이메일을 입력하세요", label_visibility="collapsed")
                        st_pw = st.text_input("비밀번호", type="password", placeholder="개인 암호 입력", label_visibility="collapsed")
                        if st.form_submit_button("점수 조회", type="primary"):
                            df_st = load_sheet_to_df(sf_id)
                            if not df_st.empty:
                                if "학교 이메일" in df_st.columns: res = df_st[(df_st['학교 이메일'].astype(str).str.strip() == str(st_email).strip()) & (df_st['비밀번호'].astype(str) == str(st_pw))]
                                else: res = df_st[(df_st['이름'].astype(str).str.strip() == str(st_email).strip()) & (df_st['비밀번호'].astype(str) == str(st_pw))]
                                if not res.empty:
                                    idx = res.index[0]
                                    scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                                    show_result_dialog(res.iloc[0].get('이름', '학생'), scores, sf_id, idx, df_st)
                                else: st.error("❌ 정보 불일치")

else:
    with st.sidebar:
        st.markdown("<h4>📋 교사 메뉴</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:12px; color:#94a3b8; margin-bottom:15px;'>👤 {st.session_state['teacher_name']} 선생님</div>", unsafe_allow_html=True)
        st.markdown("---")
        menu_selection = st.radio("메뉴", ["▶ 학생 조회 현황 모니터링", "▶ 개인별 성적 입력", "▶ 평가 대상 과목 구성", "▶ 성적 전체 일괄 업로드(CSV)"], label_visibility="collapsed")
        st.markdown("---")
        if st.button("🔐 내 정보 수정", key="sidebar_account_btn", use_container_width=True): account_update_dialog()
        if st.button("🚪 시스템 로그아웃", key="sidebar_logout_btn", use_container_width=True):
            st.session_state.update({"admin_logged_in":False, "logged_teacher_id":"", "teacher_name":"", "allowed_subjects":[]})
            st.rerun()

    st.markdown(f"<h2>수행평가 성적 관리 도우미</h2>", unsafe_allow_html=True)
    st.write(f"현재 위치: {menu_selection}")
    st.markdown("<br>", unsafe_allow_html=True)

    if menu_selection == "▶ 학생 조회 현황 모니터링":
        with st.container(border=True):
            st.markdown(f"<h3>📊 학생별 조회 이력 및 성적 현황 모니터링</h3>", unsafe_allow_html=True)
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]: registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
            if registered_dbs:
                col1, col2 = st.columns(2)
                with col1:
                    opts = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                    sel_db = st.selectbox("교과 선택", opts)
                    db = registered_dbs[opts.index(sel_db)]
                    st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester = db['subject'], db['grade'].replace("학년",""), db['semester']
                cf_id, sf_id = get_sheet_names_id(st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester)
                db_df = load_sheet_to_df(sf_id); cfg_df = load_sheet_to_df(cf_id)
                with col2:
                    cls_opts = ["전체 학급 보기"] + ([f"{x}반" for x in sorted(db_df['반'].unique())] if not db_df.empty and "반" in db_df.columns else [])
                    sel_cls = st.selectbox("학급 선택", cls_opts)
                if not db_df.empty:
                    df = db_df.copy()
                    if sel_cls != "전체 학급 보기": df = df[df['반'].astype(int) == int(sel_cls.replace("반",""))]
                    if not cfg_df.empty:
                        cfg = cfg_df.iloc[0].to_dict()
                        score_h = [cfg.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(int(cfg.get('항목개수', 3)))]
                    else: score_h = []
                    cols = ["반", "번호", "이름"] + (["학교 이메일"] if "학교 이메일" in df.columns else []) + (["비밀번호"] if "비밀번호" in df.columns else []) + score_h + ["성적조회 횟수", "최종 확인일시"]
                    st.dataframe(df[[c for c in cols if c in df.columns]].fillna("-"), use_container_width=True, hide_index=True)
            else: st.warning("배정 과목 없음")

    elif menu_selection == "▶ 개인별 성적 입력":
        with st.container(border=True):
            st.markdown(f"<h3>📝 개인별 성적 데이터 편집</h3>", unsafe_allow_html=True)
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]: registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
            if registered_dbs:
                c1, c2 = st.columns(2)
                with c1:
                    opts = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                    sel_db = st.selectbox("관리 교과", opts)
                    db = registered_dbs[opts.index(sel_db)]
                    st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester = db['subject'], db['grade'].replace("학년",""), db['semester']
                cf_id, sf_id = get_sheet_names_id(st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester)
                db_df = load_sheet_to_df(sf_id); cfg_df = load_sheet_to_df(cf_id)
                with c2:
                    cls_opts = ["전체"] + ([f"{x}반" for x in sorted(db_df['반'].unique())] if not db_df.empty and "반" in db_df.columns else [])
                    sel_cls = st.selectbox("학반 필터", cls_opts)
                if not db_df.empty:
                    if not cfg_df.empty:
                        cfg = cfg_df.iloc[0].to_dict()
                        score_h = [cfg.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(int(cfg.get('항목개수', 3)))]
                    else: score_h = []
                    valid_cols = [c for c in ["반", "번호", "이름", "학교 이메일", "비밀번호"] + score_h + ["성적조회 횟수", "최종 확인일시"] if c in db_df.columns]
                    f_idx = db_df[db_df["반"].astype(int) == int(sel_cls.replace("반",""))].index if sel_cls != "전체" else db_df.index
                    e_df = st.data_editor(db_df.loc[f_idx, valid_cols], use_container_width=True, num_rows="dynamic", disabled=["반", "번호", "이름", "성적조회 횟수", "최종 확인일시"], hide_index=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    bc_empty, bc1, bc2 = st.columns([4, 0.9, 0.9])
                    with bc1:
                        if st.button("➕ 학생 개별 추가", key="btn_trigger_student_dialog", use_container_width=True): student_individual_add_dialog(db_df, sf_id, score_h)
                    with bc2:
                        if st.button("💾 수정 사항 저장", key="btn_save_all_grid_changes", use_container_width=True):
                            for i_pos, r_idx in enumerate(f_idx):
                                for col in e_df.columns: db_df.loc[r_idx, col] = e_df.iloc[i_pos][col]
                            if save_df_to_sheet(sf_id, db_df): st.success("🎉 저장 완료!"); st.rerun()

    elif menu_selection == "▶ 평가 대상 과목 구성":
        with st.container(border=True):
            # 🚨 [요청 1 반영] 타이틀 교체 완수
            st.markdown("<h3>📁 1. 평가 과목 설정</h3>", unsafe_allow_html=True)
            r1c1, r1c2 = st.columns(2)
            with r1c1: sel_g = st.selectbox("교과군", ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"], label_visibility="collapsed")
            with r1c2: sel_gr = st.selectbox("학년", GRADE_OPTIONS, label_visibility="collapsed")
            r2c1, r2c2 = st.columns(2)
            with r2c1:
                f_sub, t_g = "", ""
                if sel_g == "➕ 신규 과목 개설": t_g = st.selectbox("분류", ["인문·사회군", "수리·과학군", "예체능군"]); f_sub = st.text_input("새 과목명")
                elif sel_g != "교과군 선택":
                    s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                    sel_s = st.selectbox("과목지정", s_opts, label_visibility="collapsed")
                    if sel_s != "과목 선택": f_sub = sel_s
            with r2c2: sel_se = st.selectbox("학기", SEMESTER_OPTIONS, label_visibility="collapsed")
            
            # 🚨 [요청 1 반영] 2번 대타이틀도 1번과 완벽하게 동일한 <h3> 태그 크기로 가독성 싱크 정렬 마감
            st.markdown("<hr style='border-top: 1px dashed #cbd5e1; margin:20px 0;'>", unsafe_allow_html=True)
            st.markdown("<h3>📁 2. 수행평가 항목 구성</h3>", unsafe_allow_html=True)
            
            ic_col, _ = st.columns([1, 2])
            with ic_col: item_cnt = st.selectbox("항목 개수", [1, 2, 3, 4, 5], index=2)
            i_titles = []
            cols = st.columns(item_cnt)
            for i in range(item_cnt):
                with cols[i]:
                    t_in = st.text_input(f"항목 {i+1} 제목", value=f"수행평가{i+1}", key=f"item_title_in_{i}")
                    i_titles.append(t_in.strip())
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 🚨 [요청 2 반영] 기본 설정 저장 버튼 명칭 교정 및 우측 정렬 완벽 이식
            _, save_col = st.columns([5, 1])
            with save_col:
                if st.button("기본 설정 저장", type="primary", use_container_width=True, key="btn_save_evaluation_config"):
                    if f_sub and sel_gr != "학년 지정" and sel_se != "학기 선택":
                        if "마스터" not in st.session_state["allowed_subjects"] and f_sub not in st.session_state["allowed_subjects"]: st.error("❌ 권한 없음")
                        else:
                            if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, f_sub)
                            cf_id, sf_id = get_sheet_names_id(f_sub, sel_gr.replace("학년",""), sel_se)
                            save_df_to_sheet(cf_id, pd.DataFrame([{"선택된반 목록": "1,2,3,4,5,6,7,8,9,10,11,12", "항목개수": item_cnt, **{f"항목{k+1}_이름": i_titles[k] for k in range(item_cnt)}}]))
                            st.success("✅ 저장되었습니다.")

    elif menu_selection == "▶ 성적 전체 일괄 업로드(CSV)":
        with st.container(border=True):
            st.markdown("<h3>📥 전체 일괄 성적 입력</h3>", unsafe_allow_html=True)
            registered_dbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]: registered_dbs = [d for d in registered_dbs if d['subject'] in st.session_state["allowed_subjects"]]
            if registered_dbs:
                opts = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                sel_db = st.selectbox("📂 성적 연동 과목 선택", opts)
                db = registered_dbs[opts.index(sel_db)]
                cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                cfg_df = load_sheet_to_df(cf_id)
                if not cfg_df.empty:
                    cfg = cfg_df.iloc[0].to_dict(); cnt = int(cfg.get('항목개수', 3))
                    dynamic_h = [cfg.get(f'항목{k+1}_이름', f'수행{k+1}') for k in range(cnt)]
                else: dynamic_h = ["수행1", "수행2", "수행3"]
                st.info(f"현재 선택된 연동 과목: **{db['subject']} ({db['grade']} / {db['semester']})**")
                csv_data = ",".join(["반", "번호", "이름", "학교 이메일", "비밀번호", "성적조회 횟수", "최종 확인일시"] + dynamic_h) + "\n1,1,홍길동,hgd@school.hs.kr,1234,0,-,20,18,25"
                st.markdown("##### 💡 양식을 다운로드하여 성적을 업로드하세요.")
                st.download_button("📥 성적 양식 다운로드", data=csv_data.encode('cp949'), file_name=f"양식_{db['subject']}.csv", mime="text/csv")
                up_f = st.file_uploader("성적 파일 CSV파일 업로드", type="csv")
                if up_f:
                    df = pd.read_csv(up_f, encoding='cp949')
                    for col in ["학교 이메일", "성적조회 횟수", "최종 확인일시"]:
                        if col not in df.columns: df[col] = "" if "일시" in col or "이메일" in col else 0
                    if save_df_to_sheet(sf_id, df): st.success("🎉 동기화 완료!")