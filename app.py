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
import profile_pop

# 🚨 [최상단 규칙 엄수] 순정 와이드 레이아웃 및 타이틀 고정
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="wide")

# =========================================================================
# 🔄 [우주 최강 철벽 CSS] 팝업창 위젯이 사이드바를 오염시키는 현상을 원천 차단
# =========================================================================
st.markdown("""
    <style>
        /* 우측 본문 전체 배경색 연회색 고정 */
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { 
            background-color: #f1f5f9 !important; 
        }
        div[data-testid="stHeader"] { display: none !important; }
        
        /* 사이드바 자체 가로 폭 너비 고정 */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] {
            min-width: 260px !important;
            max-width: 260px !important;
            background-color: #1e293b !important;
            box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important;
        }
        [data-testid="stAppViewContainer"] { margin-left: 0px !important; }

        [data-testid="stSidebar"] h4 { color: #ffffff !important; font-weight: 800; font-size: 24px !important; margin-top: 10px !important; }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 700 !important; font-size: 16px !important; }
        div[data-testid="stSidebar"] div[role="radiogroup"] label p { color: #f8fafc !important; font-weight: 700 !important; font-size: 16px !important; }

        /* 🚨 [최종 진압 마스터피스] 사이드바 내부의 모든 button 위젯 스타일을 강제로 통합 박제 */
        div[data-testid="stSidebar"] button,
        div[data-testid="stSidebar"] button:hover,
        div[data-testid="stSidebar"] button:focus,
        div[data-testid="stSidebar"] button:active {
            background-color: #2b3a4a !important;       /* 🛠️ 무슨 일이 있어도 무조건 클래식 다크 블루 */
            color: #ffffff !important;                  /* 🛠️ 무슨 일이 있어도 무조건 흰색 글자 */
            border: 2px solid #3f5164 !important;       /* 🛠️ 단정한 사각형 회색 선 테두리 상시 고정 */
            border-radius: 6px !important;
            padding: 10px 16px !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            box-shadow: none !important;                
            transform: none !important;                 
            width: 100% !important;
            display: block !important;
            text-align: center !important;
        }

        div[data-testid="stSelectbox"] div[data-baseweb="select"] { border: 2px solid #4a69bd !important; border-radius: 8px !important; background-color: #ffffff !important; }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] * { color: #0f172a !important; font-weight: 700 !important; font-size: 15px !important; }
        .stDataFrame, table { width: 100% !important; border-radius: 8px; overflow: hidden; }
        
        h2 { color: #0f172a !important; font-weight: 800 !important; font-size: 26px !important; margin-bottom: 3px !important; margin-top: 0px !important; }
        h3 { color: #1e293b !important; font-weight: 700 !important; font-size: 20px !important; margin-top: 0px !important; margin-bottom: 5px !important; }
        
        div[data-testid="stTextInput"] div[data-baseweb="input"], div[data-testid="stNumberInput"] div[data-baseweb="input"] {
            border: 2px solid #cbd5e1 !important;
            border-radius: 6px !important;
            background-color: #ffffff !important;
        }

        div[data-testid="stForm"] button[data-testid="baseButton-secondary"] {
            background-color: #4a69bd !important;
            color: #ffffff !important;
            font-weight: bold !important;
            border: none !important;
            width: 100% !important;
            padding: 0.6rem 0 !important;
            border-radius: 8px !important;
            font-size: 16px !important;
            box-shadow: 0 4px 10px rgba(74, 105, 189, 0.2) !important;
        }
        
        div.stButton > button[key="btn_save_all_grid_changes"] { background-color: #3b82f6 !important; color: white !important; font-weight: bold !important; border: none !important; }
        div.stButton > button[key="btn_trigger_student_dialog"] { background-color: #10b981 !important; color: white !important; font-weight: bold !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# 파일 경로 정의
CONFIG_FILE_MAIN = "master_subjects.csv"
META_FILE = "admin_meta.csv"

# --- 데이터 로드/저장 시스템 ---
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

# 🚨 완벽히 격리 기동되는 독립 다이얼로그 바인딩
@st.dialog("🔐 내 정보 수정")
def launch_isolated_profile_dialog():
    profile_pop.render_isolated_dialog(load_sheet_to_df, save_df_to_sheet)

@st.dialog("➕ 학생 개별 추가")
def student_individual_add_dialog(db_df, sf_id, score_headers):
    st.markdown("##### 📝 신규 누락 학생 1명 개별 등록")
    st.write("아래 인적사항을 입력하시면 현재 성적부 하단에 즉시 추가됩니다.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    ac1, ac2 = st.columns(2)
    with ac1: add_b = st.number_input("반", min_value=1, max_value=30, value=1)
    with ac2: add_n = st.number_input("번호", min_value=1, max_value=60, value=1)
    
    add_name = st.text_input("학생 이름", placeholder="성명 입력")
    add_email = st.text_input("학교 이메일", placeholder="아이디@도메인.hs.kr")
    add_pw = st.text_input("개인 비밀번호", placeholder="학생 전용 조회 암호")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 학생 추가 등록", use_container_width=True, type="primary"):
        if add_name and add_email and add_pw:
            new_student_row = {
                "반": int(add_b), "번호": int(add_n), "이름": str(add_name).strip(),
                "school_email": str(add_email).strip(), "비밀번호": str(add_pw).strip(),
                "성적조회 횟수": 0, "최종 확인일시": "-"
            }
            for h in score_headers: new_student_row[h] = 0
            
            updated_master_df = pd.concat([db_df, pd.DataFrame([new_student_row])], ignore_index=True)
            if save_df_to_sheet(sf_id, updated_master_df):
                st.success(f"✅ [{add_b}반 {add_n}번 {add_name}] 학생이 클라우드 성적 대장에 안전하게 추가 등록 완료되었습니다!")
                st.rerun()
        else:
            st.error("학생의 이름, 이메일, 비밀번호를 빠짐없이 채워주세요.")

if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = ""
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = ""
if "allowed_subjects" not in st.session_state: st.session_state["allowed_subjects"] = []

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 지정", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]

# 세션 팅김 방지용 역방향 온클릭 리스너 분기 매핑
def sidebar_logout_callback():
    st.session_state["admin_logged_in"] = False
    st.session_state["logged_teacher_id"] = ""
    st.session_state["teacher_name"] = ""
    st.session_state["allowed_subjects"] = []

if "open_profile_popup" not in st.session_state:
    st.session_state["open_profile_popup"] = False

if st.session_state["open_profile_popup"]:
    st.session_state["open_profile_popup"] = False
    launch_isolated_profile_dialog()

if not st.session_state["admin_logged_in"]:
    st.markdown("""
        <style>
            .main, [data-testid="stAppViewContainer"] { background-color: #3e4f5a !important; }
            div[data-testid="stHeader"] { display: none !important; }
            footer { display: none !important; }
            div[data-testid="stForm"] {
                background-color: #ffffff !important; border: 1px solid #cbd5e1 !important;
                padding: 40px 30px 30px 30px !important; border-radius: 24px !important;
                box-shadow: 0 15px 40px rgba(0,0,0,0.12) !important; max-width: 440px !important; margin: 60px auto 0 auto !important; position: relative !important;
            }
            div[data-testid="stForm"] > div[data-testid="stVerticalBlock"] { display: flex !important; flex-direction: column !important; align-items: center !important; width: 100% !important; }
        </style>
    """, unsafe_allow_html=True)
    
    with st.form("master_unified_form"):
        st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        login_mode = st.radio("접속 모드", ["교사", "학생"], horizontal=True, label_visibility="collapsed")
        st.markdown("<h4 style='height: 10px; border:none;'></h4>", unsafe_allow_html=True)
        
        if login_mode == "교사":
            admin_id = st.text_input("교사_ID", placeholder="교사 ID를 입력하세요", label_visibility="collapsed", key="ti_id")
            admin_pw = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed", key="ti_pw")
            if st.form_submit_button("로그인"):
                auth_result = verify_teacher_credentials(admin_id, admin_pw)
                if auth_result["success"]:
                    st.session_state["admin_logged_in"] = True
                    st.session_state["logged_teacher_id"] = auth_result["teacher_id"]
                    st.session_state["teacher_name"] = auth_result["teacher_name"]
                    st.session_state["allowed_subjects"] = auth_result["authorized_subjects"]
                    st.rerun()
                else: st.error("❌ ID 또는 비밀번호 오류")

        elif login_mode == "학생":
            active_dbs = get_active_databases()
            if not active_dbs: st.warning("등록된 데이터가 없습니다.")
            else:
                opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in active_dbs]
                sel_s = st.selectbox("과목", opts_s, label_visibility="collapsed", key="sb_sub")
                if sel_s != "과목 및 학기를 선택하세요.":
                    db = active_dbs[opts_s.index(sel_s)-1]
                    cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                    config = load_sheet_to_df(cf_id).iloc[0].to_dict() if not load_sheet_to_df(cf_id).empty else None
                    if config:
                        st.markdown("<h4 style='height: 5px; border:none;'></h4>", unsafe_allow_html=True)
                        st_email_in = st.text_input("학교 이메일", placeholder="학교 이메일을 입력하세요", label_visibility="collapsed", key="ti_st_email")
                        st_pw = st.text_input("비밀번호", type="password", placeholder="개인 암호 입력", label_visibility="collapsed", key="ti_st_pw")
                        
                        if st.form_submit_button("점수 조회"):
                            df_st = load_sheet_to_df(sf_id)
                            if not df_st.empty:
                                if "school_email" in df_st.columns:
                                    res = df_st[(df_st['school_email'].astype(str).str.strip() == str(st_email_in).strip()) & (df_st['비밀번호'].astype(str) == str(st_pw))]
                                else:
                                    res = df_st[(df_st['이름'].astype(str).str.strip() == str(st_email_in).strip()) & (df_st['비밀번호'].astype(str) == str(st_pw))]
                                    
                                if not res.empty:
                                    idx = res.index[0]
                                    st_name = res.iloc[0].get('이름', '학생')
                                    scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                                    show_result_dialog(st_name, scores, sf_id, idx, df_st)
                                else: st.error("❌ 정보가 일치하지 않습니다. 입력값을 다시 확인해 주세요.")
        st.markdown("<div style='text-align:center; font-size:11px; color:#94a3b8; margin-top:30px;'>Designed & Developed by User & AI Creator</div>", unsafe_allow_html=True)

else:
    with st.sidebar:
        st.markdown("<h4>📋 교사 메뉴</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:12px; color:#94a3b8; margin-bottom:15px;'>👤 {st.session_state['teacher_name']} 선생님 접속 중</div>", unsafe_allow_html=True)
        st.markdown("---")
        menu_selection = st.radio(
            "메뉴 선택",
            ["▶ 학생 조회 현황 모니터링", "▶ 개인별 성적 입력", "▶ 평가 대상 과목 구성", "▶ 성적 전체 일괄 업로드(CSV)"],
            label_visibility="collapsed"
        )
        st.markdown("---")
        
        # 🚨 순정 컴포넌트 호출 방식을 유지하되 상단에 선언된 블랙홀 CSS 지시문이 무조건 덮어씌움
        if st.button("🔐 내 정보 수정", key="account_pure_btn", use_container_width=True):
            st.session_state["open_profile_popup"] = True
            st.rerun()
            
        st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)
        st.button("🚪 시스템 로그아웃", key="logout_pure_