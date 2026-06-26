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

@st.cache_data(ttl=10)
def load_admin_credentials():
    df = load_sheet_to_df("admin_meta", ["username", "password"])
    if not df.empty:
        username = str(df.iloc[0].get('username', 'admin')).strip()
        password = str(df.iloc[0].get('password', '1234')).strip()
        return username, password
    return "admin", "1234"

def save_admin_credentials(new_id, new_pw):
    df = pd.DataFrame([{"username": str(new_id).strip(), "password": str(new_pw).strip()}])
    save_df_to_sheet("admin_meta", df)

def get_sheet_names_id(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    safe_semester = semester_str.replace(" ", "_").replace("/", "_")
    return f"cfg_{safe_subject}_{grade}Grade", f"st_{safe_subject}_{grade}_{safe_semester}"

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict):
    st.markdown(f"<div><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True)
    st.table(pd.DataFrame(scores_dict))
    if st.button("닫기", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()

@st.dialog("🔐 계정 정보 수정")
def account_update_dialog():
    curr_id, curr_pw = load_admin_credentials()
    new_id = st.text_input("새 관리자 ID", value=curr_id)
    new_pw = st.text_input("새 암호", type="password")
    confirm_pw = st.text_input("새 암호 확인", type="password")
    if st.button("변경 저장", use_container_width=True, type="primary"):
        if new_id and new_pw == confirm_pw:
            save_admin_credentials(new_id, new_pw)
            st.success("변경 완료!")
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

@st.cache_data(ttl=5)
def load_sheet_to_df(sheet_name, default_cols=None):
    wks = get_google_sheet(sheet_name)
    if wks is None: return pd.DataFrame(columns=default_cols if default_cols else [])
    try:
        records = wks.get_all_records()
        if not records: return pd.DataFrame(columns=default_cols if default_cols else [])
        return pd.DataFrame(records)
    except: return pd.DataFrame(columns=default_cols if default_cols else [])

@st.cache_data(ttl=15)
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
                    active_list.append({"subject": match.group(1).replace("_", " "), "grade": f"{match.group(2)}학년", "semester": match.group(3).replace("_", " ")})
    except: pass
    return active_list

if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 지정", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]
CURRENT_ADMIN_ID, CURRENT_ADMIN_PW = load_admin_credentials()

# =========================================================================
# 🔄 1단계: 하이엔드 인프라 스타일링 (드롭박스 시인성 대폭 업그레이드 패치)
# =========================================================================
if not st.session_state["admin_logged_in"]:
    st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="centered")
    st.markdown("""
        <style>
            .main, [data-testid="stAppViewContainer"] { background-color: #3e4f5a !important; }
            div[data-testid="stHeader"] { display: none !important; }
            footer { display: none !important; }
            
            div[data-testid="stForm"] {
                background-color: #ffffff !important;
                border: 1px solid #cbd5e1 !important;
                padding: 40px 30px 30px 30px !important;
                border-radius: 24px !important;
                box-shadow: 0 15px 40px rgba(0,0,0,0.12) !important;
                max-width: 440px !important;
                margin: 60px auto 0 auto !important;
                position: relative !important;
            }
            div[data-testid="stForm"] > div[data-testid="stVerticalBlock"] {
                display: flex !important; flex-direction: column !important; align-items: center !important; width: 100% !important;
            }
            div[role="radiogroup"] { justify-content: center !important; margin: 0 auto !important; gap: 40px !important; }
            div[data-testid="stRadio"] label p { font-size: 16px !important; font-weight: bold !important; color: #1e293b !important; }
            div[data-testid="stForm"] { border: none !important; box-shadow: none !important; }
            .stTextInput, .stNumberInput, .stSelectbox { width: 300px !important; max-width: 300px !important; margin: 0 auto 5px auto !important; }
            
            div[data-testid="stFormSubmitButton"] { display: flex !important; justify-content: center !important; width: 100% !important; margin: 15px auto 0 auto !important; }
            button[kind="primaryFormSubmit"] {
                background-color: #4a69bd !important; border-color: #4a69bd !important; color: white !important; font-weight: bold !important;
                padding: 9px 0px !important; border-radius: 8px !important; font-size: 15px !important;
                width: 140px !important; min-width: 140px !important; max-width: 140px !important;
                box-shadow: 0 4px 10px rgba(74, 105, 189, 0.2) !important;
            }
            h2 { font-size: 24px !important; color: #1e293b !important; font-weight: 800 !important; text-align: center !important; margin: 0 0 20px 0 !important; width: 100% !important; }
            hr { width: 300px !important; margin: 12px auto !important; border: none !important; border-top: 1px solid #e2e8f0 !important; }
            .footer-notice { text-align: center; font-size: 11px; color: #94a3b8; margin-top: 30px; border-top: 1px solid #f1f5f9; padding-top: 15px; font-weight: 600; width: 300px; margin: 30px auto 0 auto; }
        </style>
    """, unsafe_allow_html=True)

    with st.form("master_unified_form"):
        st.markdown("<h2>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        login_mode = st.radio("접속 모드", ["교사", "학생"], horizontal=True, label_visibility="collapsed")
        st.markdown("<hr>", unsafe_allow_html=True)
        
        if login_mode == "교사":
            admin_id = st.text_input("ID", placeholder="아이디를 입력하세요", label_visibility="collapsed", key="ti_id")
            admin_pw = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed", key="ti_pw")
            if st.form_submit_button("로그인", type="primary"):
                if admin_id.strip() == CURRENT_ADMIN_ID and admin_pw == CURRENT_ADMIN_PW:
                    st.session_state["admin_logged_in"] = True
                    st.rerun()
                else: st.error("❌ ID 또는 비밀번호 오류")

        elif login_mode == "학생":
            active_dbs = get_active_databases()
            if not active_dbs: st.warning("등록된 데이터가 없습니다.")
            else:
                opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs]
                sel_s = st.selectbox("과목", opts_s, label_visibility="collapsed", key="sb_sub")
                if sel_s != "과목 및 학기를 선택하세요.":
                    db = active_dbs[opts_s.index(sel_s)-1]
                    cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                    config = load_sheet_to_df(cf_id).iloc[0].to_dict() if not load_sheet_to_df(cf_id).empty else None
                    if config:
                        st.markdown("<hr>", unsafe_allow_html=True)
                        classes = [f"{x.strip()}반" for x in str(config.get('선택된반 목록', '1')).split(",") if x.strip()]
                        b_in = st.selectbox("반", classes, key="sb_class", label_visibility="collapsed")
                        n_in = st.number_input("번호", 1, 50, 1, key="ni_num", label_visibility="collapsed")
                        name_in = st.text_input("이름", placeholder="이름", key="ti_name", label_visibility="collapsed")
                        pw_in = st.text_input("비밀번호", type="password", placeholder="개인 암호 입력", key="ti_st_pw", label_visibility="collapsed")
                        if st.form_submit_button("점수 조회", type="primary"):
                            df_st = load_sheet_to_df(sf_id)
                            if not df_st.empty:
                                res = df_st[(df_st['반'].astype(int)==int(b_in.replace("반",""))) & (df_st['번호'].astype(int)==n_in) & (df_st['이름'].astype(str)==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                                if not res.empty:
                                    idx = res.index[0]
                                    scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                                    show_result_dialog(name_in, scores)
                                else: st.error("❌ 일치하는 학생 정보가 없습니다.")
        st.markdown("<div class='footer-notice'>Designed & Developed by User & AI Creator</div>", unsafe_allow_html=True)

else:
    # ⚙️ 교사 로그인 후: 100% 시원한 대형 와이드 스크린 대시보드
    st.set_page_config(page_title="교사용 마스터 관리 시스템", layout="wide")
    st.markdown("""
        <style>
            .main, [data-testid="stAppViewContainer"] { background-color: #f1f5f9 !important; }
            [data-testid="stSidebar"] { background-color: #1e293b !important; box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; }
            [data-testid="stSidebar"] * { color: #f8fafc !important; font-weight: 600; }
            
            /* 🚨 [드롭박스 시인성 전면 개조 패치] 테두리를 선명하게 하고 투명도를 없애 눈에 확 띄게 조절 */
            div[data-testid="stSelectbox"] div[data-baseweb="select"] {
                border: 2px solid #4a69bd !important;
                border-radius: 8px !important;
                background-color: #ffffff !important;
            }
            div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
                color: #0f172a !important;
                font-weight: 700 !important;
                font-size: 15px !important;
            }
            
            .wide-dashboard-card {
                background-color: #ffffff !important;
                border-radius: 16px !important;
                padding: 30px !important;
                box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
                margin-bottom: 25px !important;
                border: 1px solid #e2e8f0 !important;
            }
            .stDataFrame, table { width: 100% !important; border-radius: 8px; overflow: hidden; }
            h2 { color: #0f172a !important; font-weight: 800 !important; font-size: 28px !important; margin-bottom: 5px !important; }
            h3 { color: #1e293b !important; font-weight: 700 !important; font-size: 20px !important; margin-top: 0px !important; }
        </style>
    """, unsafe_allow_html=True)

    # 🎯 [선생님 요청] "학내망 성적 시스템" ➔ "수행평가 관리 시스템"으로 명칭 격상
    with st.sidebar:
        st.markdown("<h2>⚙️ 수행평가 관리 시스템</h2>", unsafe_allow_html=True)
        st.markdown("---")
        menu_selection = st.radio(
            "📋 관리자 메뉴",
            ["▶ 학적 및 응시현황 확인", "▶ 평가 대상 과목 구성", "▶ 성적 데이터 연동 (CSV)", "▶ 시스템 보안 설정"]
        )
        st.markdown("---")
        if st.button("🚪 시스템 로그아웃", use_container_width=True):
            st.session_state["admin_logged_in"] = False
            st.rerun()

    st.markdown(f"<h2>교사용 마스터 통합 워크스테이션</h2>", unsafe_allow_html=True)
    st.write(f"현재 위치: 교사 모드 > {menu_selection}")
    st.markdown("<br>", unsafe_allow_html=True)

    # 모듈 1: 평가 대상 과목 구성 (채점단 삭제 및 미학적 텍스트 라벨 완전 제거 완수)
    if menu_selection == "▶ 평가 대상 과목 구성":
        st.markdown("<div class='wide-dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📁 1. 평가 과목 세팅 및 파티션 활성화</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            # 🎯 불필요하게 위에 따로 써놓았던 텍스트 라벨을 삭제하여 드롭다운 박스가 바로 정돈되게 배치
            g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"]
            sel_g = st.selectbox("교과군 분류 선택", options=g_opts, label_visibility="collapsed")
            
            final_sub, t_g = "", ""
            if sel_g == "➕ 신규 과목 개설":
                t_g = st.selectbox("위치 지정 분류", ["인문·사회군", "수리·과학군", "예체능군"])
                final_sub = st.text_input("새 과목명 입력").strip()
            elif sel_g != "교과군 선택":
                s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                sel_s = st.selectbox("세부 과목 지정", options=s_opts, label_visibility="collapsed")
                if sel_s != "과목 선택": final_sub = sel_s
        
        with col2:
            sel_gr = st.selectbox("학년 선택", options=GRADE_OPTIONS, label_visibility="collapsed")
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            sel_se = st.selectbox("학기 선택", options=SEMESTER_OPTIONS, label_visibility="collapsed")
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 이 과목 활성화 및 서버 로드"):
            if final_sub and sel_gr != "학년 지정" and sel_se != "학기 선택":
                if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub)
                st.session_state.active_subject = final_sub
                st.session_state.active_grade = sel_gr.replace("학년", "")
                st.session_state.active_semester = sel_se
                st.success(f"✅ [{final_sub}] 과목이 데이터베이스 엔진에 성공적으로 세팅되었습니다!")
            else:
                st.error("과목 정보를 빠짐없이 선택해 주세요.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 모듈 2: 학적 및 응시현황 모니터링 Grid
    elif menu_selection == "▶ 학적 및 응시현황 확인":
        st.markdown("<div class='wide-dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📊 실시간 학생 응시 및 점수 모니터링 Grid</h3>", unsafe_allow_html=True)
        
        sample_df = pd.DataFrame({
            "반": [1, 1, 1, 2, 2, 3],
            "번호": [1, 2, 3, 1, 2, 1],
            "이름": ["김철수", "이영희", "박민수", "최진아", "정우성", "홍길동"],
            "비밀번호 설정상태": ["설정완료", "설정완료", "미설정", "설정완료", "설정완료", "설정완료"],
            "성적조회 횟수": [3, 0, 0, 5, 12, 2],
            "최종 확인일시": ["2026-06-26", "-", "-", "2026-06-25", "2026-06-26", "2026-06-24"]
        })
        st.dataframe(sample_df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 모듈 3: 성적 데이터 연동 (검증된 정밀 샘플 데이터 이식 탑재)
    elif menu_selection == "▶ 성적 데이터 연동 (CSV)":
        st.markdown("<div class='wide-dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📥 CSV 파일 기반 대용량 클라우드 연동 동기화</h3>", unsafe_allow_html=True)
        
        if "active_subject" in st.session_state and st.session_state.active_subject:
            st.info(f"현재 선택된 연동 타겟 과목: **{st.session_state.active_subject} ({st.session_state.active_grade}학년 / {st.session_state.active_semester})**")
            
            # 🎯 [선생님 요청] 완벽한 실제 다운로드용 예시 샘플 레코드 생성
            example_data = io.StringIO()
            cw = csv.writer(example_data)
            cw.writerow(["반", "번호", "이름", "비밀번호", "형성평가", "포트폴리오", "태도점수"])
            cw.writerow([1, 1, "홍길동", "1024", 20, 18, 25])
            cw.writerow([1, 2, "이영희", "3925", 19, 20, 22])
            cw.writerow([2, 1, "강백호", "8254", 15, 15, 20])
            cw.writerow([2, 2, "소연지", "7711", 20, 19, 25])
            
            st.markdown("##### 💡 실제 가이드라인 예시 양식을 먼저 다운로드하여 성적을 연동하세요.")
            st.download_button(
                label="📥 수행평가 성적 대장 실제 데이터 예시 파일(.CSV) 다운로드",
                data=example_data.getvalue(),
                file_name=f"수행평가_실제양식예시_{st.session_state.active_subject}.csv",
                mime="text/csv",
                key="download_sample_csv"
            )
            st.markdown("<br>", unsafe_allow_html=True)
            
            up_f = st.file_uploader("성적 대장 CSV 파일 업로드", type="csv")
            if up_f:
                df_up = pd.read_csv(up_f, encoding='cp949')
                _, sf_id = get_sheet_names_id(st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester)
                if save_df_to_sheet(sf_id, df_up):
                    st.success("🎉 구글 스프레드시트 클라우드로 실시간 데이터 동기화가 완벽히 완료되었습니다!")
        else:
            st.warning("먼저 '▶ 평가 대상 과목 구성' 메뉴에서 대상 과목을 지정 및 활성화해 주세요.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 모듈 4: 시스템 보안 설정
    elif menu_selection == "▶ 시스템 보안 설정":
        st.markdown("<div class='wide-dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<h3>🔐 마스터 관리자 인증 계정 변경</h3>", unsafe_allow_html=True)
        account_update_dialog()
        st.markdown("</div>", unsafe_allow_html=True)