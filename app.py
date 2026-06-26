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

# =========================================================================
# 🔐 [구글 시트 API 연동 설정] secrets.toml 기반 안전 접속 엔진 (기존 로직 보존)
# =========================================================================
@st.cache_resource
def init_google_sheet_client():
    try:
        credentials_info = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        return None

gc = init_google_sheet_client()
SPREADSHEET_NAME = "수행평가_데이터베이스"  # 👈 구글 드라이브 파일명

def get_google_sheet(sheet_name):
    if gc is None: return None
    try:
        sh = gc.open(SPREADSHEET_NAME)
        try:
            return sh.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            return sh.add_worksheet(title=sheet_name, rows="1000", cols="30")
    except:
        return None

# 원격 데이터를 긁어올 때 메모리 버퍼 캐시 보존
@st.cache_data(ttl=5)
def load_sheet_to_df(sheet_name, default_cols=None):
    wks = get_google_sheet(sheet_name)
    if wks is None: return pd.DataFrame(columns=default_cols if default_cols else [])
    try:
        records = wks.get_all_records()
        if not records: return pd.DataFrame(columns=default_cols if default_cols else [])
        return pd.DataFrame(records)
    except:
        return pd.DataFrame(columns=default_cols if default_cols else [])

def save_df_to_sheet(sheet_name, df):
    wks = get_google_sheet(sheet_name)
    if wks is None: return False
    try:
        wks.clear()
        df_filled = df.fillna("").astype(str)
        wks.update([df_filled.columns.values.tolist()] + df_filled.values.tolist())
        return True
    except:
        return False

# 메뉴 조작 및 타이핑 시 구글 트래픽 제어 캐시 보존
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
                    sub_name = match.group(1).replace("_", " ")
                    grd_name = f"{match.group(2)}학년"
                    sem_name = match.group(3).replace("_", " ")
                    active_list.append({"subject": sub_name, "grade": grd_name, "semester": sem_name})
    except: pass
    return active_list

# 마스터 데이터 로드 트래픽 캐시 보존
@st.cache_data(ttl=60)
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

@st.cache_data(ttl=60)
def load_admin_password():
    df = load_sheet_to_df("admin_meta", ["password"])
    if not df.empty:
        return str(df.iloc[0]['password']).strip()
    return "1234"

def save_admin_password(new_pw):
    df = pd.DataFrame([{"password": str(new_pw).strip()}])
    save_df_to_sheet("admin_meta", df)

def get_sheet_names_id(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    safe_semester = semester_str.replace(" ", "_").replace("/", "_")
    return f"cfg_{safe_subject}_{grade}Grade", f"st_{safe_subject}_{grade}_{safe_semester}"

def remove_subject_completely_from_disk(sub_name):
    df_m = load_sheet_to_df("master_subjects", ["교과군", "과목명"])
    if not df_m.empty:
        df_m = df_m[df_m["과목명"] != sub_name]
        save_df_to_sheet("master_subjects", df_m)
    if gc is None: return
    try:
        sh = gc.open(SPREADSHEET_NAME)
        safe_sub = sub_name.replace(" ", "_")
        for wks in sh.worksheets():
            if safe_sub in wks.title and (wks.title.startswith("cfg_") or wks.title.startswith("st_")):
                sh.del_worksheet(wks)
    except: pass

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict):
    st.markdown(f"<div style='margin-bottom:15px;'><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True)
    st.table(pd.DataFrame(scores_dict))
    if st.button("확인 후 닫기", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()

@st.dialog("🔐 관리자 암호 수정")
def password_update_dialog():
    st.markdown("<div style='padding: 5px;'></div>", unsafe_allow_html=True)
    new_pw = st.text_input("새 암호 입력", type="password", key="dialog_new_pw")
    confirm_pw = st.text_input("새 암호 확인", type="password", key="dialog_confirm_pw")
    is_valid, msg = is_strong_password(new_pw)
    if new_pw:
        if new_pw == confirm_pw and is_valid:
            st.markdown("<div style='background-color:#E8F5E9; border-radius:4px; padding:10px; color:#2E7D32; font-weight:500; margin-bottom:10px;'>✅ 두 암호가 완벽하게 일치합니다.</div>", unsafe_allow_html=True)
        elif confirm_pw and new_pw != confirm_pw:
            st.error("❌ 암호 확인 칸이 일치하지 않습니다.")
        else:
            st.warning(msg)
    st.markdown("""<div style="font-size: 13px; color: #57606a; line-height: 1.6; background: #f8f9fa; padding: 15px; border-radius: 8px;">
    <b>[안전 암호 규칙]</b><br>- 최소 12자 이상 필수<br>- 영문 + 숫자 + 특수기호 조합
    </div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    can_submit = is_valid and (new_pw == confirm_pw)
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("저장 후 적용", disabled=not can_submit, use_container_width=True, type="primary"):
            save_admin_password(new_pw); st.toast("🎉 암호가 변경되었습니다!"); st.rerun()
    with b_col2:
        if st.button("수정 취소", use_container_width=True): st.rerun()

def reset_all_data():
    st.cache_resource.clear()
    st.cache_data.clear()
    keep_keys = {
        "admin_logged_in": st.session_state.get("admin_logged_in", True),
        "sel_group_idx": st.session_state.get("sel_group_idx", 0),
        "sel_sub_idx": st.session_state.get("sel_sub_idx", 0),
        "sel_grade_idx": st.session_state.get("sel_grade_idx", 0),
        "sel_semester_idx": st.session_state.get("sel_semester_idx", 0),
        "active_subject": st.session_state.get("active_subject", None),
        "active_grade": st.session_state.get("active_grade", None),
        "active_semester": st.session_state.get("active_semester", None)
    }
    st.session_state.clear()
    for k, v in keep_keys.items(): st.session_state[k] = v
    st.session_state["saved_items_count"] = 0
    st.session_state["just_saved_success"] = False
    st.success("🎉 입력 데이터가 깨끗하게 초기화되었습니다!")
    st.rerun()

def is_strong_password(pw):
    if len(pw) < 12: return False, "❌ 최소 12자리 이상이어야 합니다."
    if not re.search("[a-zA-Z]", pw): return False, "❌ 영문자가 포함되어야 합니다."
    if not re.search("[0-9]", pw): return False, "❌ 숫자가 포함되어야 합니다."
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", pw): return False, "❌ 특수문자가 포함되어야 합니다."
    return True, "✅ 사용 가능한 안전한 암호 조건입니다."

# --- 세션 상태 초기화 및 고정 보존 ---
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "show_monitor_view" not in st.session_state: st.session_state["show_monitor_view"] = False
if "show_delete_panel" not in st.session_state: st.session_state["show_delete_panel"] = False
if "sel_group_idx" not in st.session_state: st.session_state.sel_group_idx = 0
if "sel_sub_idx" not in st.session_state: st.session_state.sel_sub_idx = 0
if "sel_grade_idx" not in st.session_state: st.session_state.sel_grade_idx = 0
if "sel_semester_idx" not in st.session_state: st.session_state.sel_semester_idx = 0
if "teacher_sidebar_menu" not in st.session_state: st.session_state["teacher_sidebar_menu"] = "과목 구성"

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 선택", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]
CURRENT_ADMIN_PW = load_admin_password()

# =========================================================================
# 🎯 [대시보드 및 일체형 로그인 허브 디자인 통합 CSS]
# =========================================================================
if not st.session_state["admin_logged_in"]:
    # 🎒 [모드 1] 로그인 전 일체형 미니 카드 레이아웃 스타일링 (두 번째 사진 완벽 동기화)
    st.markdown("""
        <style>
            .main, [data-testid="stAppViewContainer"] { background-color: #3e4f5a !important; }
            div[data-testid="stHeader"] { display: none !important; }
            footer { display: none !important; }
            
            /* 🎯 550px 하얀색 미니 카드 본체 바인딩 */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                max-width: 530px !important;
                margin: 70px auto 0 auto !important;
                background-color: #ffffff !important;
                padding: 45px 40px !important;
                border-radius: 28px !important;
                border: 1px solid #cbd5e1 !important;
                box-shadow: 0 20px 45px rgba(0,0,0,0.18) !important;
            }
            
            /* 라디오 버튼 정렬 가이드 (교사 / 학생 가로 배열) */
            div[data-testid="stRadio"] > div {
                flex-direction: row !important;
                justify-content: center !important;
                gap: 45px !important;
                margin: 20px 0 25px 0 !important;
            }
            div[data-testid="stRadio"] label p { font-size: 17px !important; font-weight: bold !important; color: #1e293b !important; }
            
            div[data-testid="stForm"] { border: none !important; padding: 0px !important; box-shadow: none !important; }
            
            h2 { font-size: 26px !important; color: #000000 !important; font-weight: 800 !important; text-align: center !important; margin: 0px 0px 8px 0px !important; }
            h3 { font-size: 20px !important; color: #000000 !important; text-align: center !important; margin: 0px 0px 10px 0px !important; font-weight: 700 !important; }
            
            /* 파란색 로그인/조회 버튼 최적화 스타일링 */
            div.stButton button {
                background-color: #5c7cfa !important;
                color: white !important;
                border: none !important;
                font-weight: bold !important;
                padding: 10px 0px !important;
                border-radius: 8px !important;
                font-size: 16px !important;
                width: 100% !important;
            }
            
            .card-footer-notice {
                text-align: center; font-size: 12px; color: #94a3b8; margin-top: 35px; border-top: 1px solid #f1f5f9; padding-top: 15px; font-weight: 500;
            }
        </style>
    """, unsafe_allow_html=True)
else:
    # 👨‍🏫 [모드 2] 로그인 후 개방되는 통합 대시보드 ERP 스타일링 (첫 번째 사진 양식 매핑)
    st.markdown("""
        <style>
            .main, [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
            div[data-testid="stHeader"] { display: none !important; }
            footer { display: none !important; }
            .block-container { padding-top: 0rem !important; padding-left: 0rem !important; padding-right: 0rem !important; }
            
            /* 🔵 상단 파란색 전체 메뉴 네비게이션 탑 바 시스템 */
            .blue-top-nav-bar {
                background-color: #0056b3 !important;
                color: #ffffff !important;
                padding: 12px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 14px;
                font-family: sans-serif;
                border-bottom: 2px solid #004094;
                box-shadow: 0 4px 10px rgba(0,0,0,0.06);
                width: 100% !important;
                position: relative;
            }
            .top-bar-left { font-weight: bold; font-size: 16px; display: flex; align-items: center; gap: 12px; }
            .top-bar-right { display: flex; align-items: center; gap: 25px; color: #e2e8f0; }
            .top-bar-right b { color: #ffffff !important; }
            
            /* 본문 폼 디자인 정돈 */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border: none !important; padding: 25px 35px !important; box-shadow: none !important; background-color: transparent !important; max-width: 100% !important;
            }
            div[data-testid="stForm"] { border: none !important; padding: 0px !important; box-shadow: none !important; }
            
            /* 좌측 트리형 메뉴 사이드바 색상 가이드 */
            [data-testid="stSidebar"] { background-color: #f1f5f9 !important; border-right: 1px solid #cbd5e1 !important; }
            [data-testid="stSidebar"] h3 { font-size: 16px !important; font-weight: 800 !important; color: #334155 !important; margin-bottom: 12px !important; }
            
            div.stButton button[key="side_logout_btn"] { background-color: #ef4444 !important; color: white !important; border: none !important; font-weight: bold !important; }
            div.stButton button { transition: all 0.15s ease-in-out !important; }
            
            div.custom-guide-bar { background-color: #eff6ff !important; border: 2px dashed #93c5fd !important; padding: 10px !important; border-radius: 8px !important; margin-top: 15px !important; color: #1e3a8a !important; font-size: 14px !important; text-align: center !important; font-weight: 500 !important; }
            div.next-step-box { background-color: #f0fdf4 !important; border: 2px solid #bbf7d0 !important; padding: 15px !important; border-radius: 10px !important; margin-top: 15px !important; color: #166534 !important; font-size: 14px !important; line-height: 1.6 !important; }
        </style>
    """, unsafe_allow_html=True)


# =========================================================================
# 구역 1. 로그인 전 일체형 분기 스위칭 허브 (두 번째 이미지 구조 적용)
# =========================================================================
if not st.session_state["admin_logged_in"]:
    
    st.markdown("<h2>양현고등학교</h2>", unsafe_allow_html=True)
    st.markdown("<h3>학내망(온라인) 성적처리 시스템</h3>", unsafe_allow_html=True)
    
    # 🎯 [핵심 교정]: 라디오 단추 기어로 '교사' / '학생' 기능을 완벽 분리 전환
    login_mode = st.radio("접속 권한 선택", ["교사", "학생"], label_visibility="collapsed")
    st.markdown("<hr style='margin: 15px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
    
    # 👨‍🏫 Case 1. 교과 통합 관리자 로그인 작동
    if login_mode == "교사":
        with st.form("teacher_login_secure_form"):
            st.markdown("<div style='font-size:14px; font-weight:700; color:#1e293b; margin-bottom:6px;'>사용자 ID</div>", unsafe_allow_html=True)
            st.text_input("아이디", value="hushpark", disabled=True, label_visibility="collapsed")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            st.markdown("<div style='font-size:14px; font-weight:700; color:#1e293b; margin-bottom:6px;'>비밀번호 입력</div>", unsafe_allow_html=True)
            admin_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed", key="ti_admin_password_field")
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            
            if st.form_submit_button("로그인", use_container_width=True, type="primary"):
                if admin_pw == CURRENT_ADMIN_PW:
                    st.session_state["admin_logged_in"] = True
                    st.rerun()
                else:
                    st.error("❌ 관리자 인증 비밀번호가 틀렸습니다.")

    # 🎒 Case 2. 학생용 개인 성적 조회 시스템 작동
    elif login_mode == "학생":
        active_dbs = get_active_databases()
        if not active_dbs:
            st.warning("현재 공시된 성적 데이터 세트가 존재하지 않습니다.")
        else:
            st.markdown("<div style='font-size:14px; font-weight:700; color:#1e293b; margin-bottom:6px;'>🎯 대상 과목 및 학기 선택</div>", unsafe_allow_html=True)
            opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs]
            sel_s = st.selectbox("조회할 과목 선택", opts_s, label_visibility="collapsed", key="student_select_sub")
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            if sel_s != "과목 및 학기를 선택하세요.":
                db = active_dbs[opts_s.index(sel_s)-1]
                cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                df_load = load_sheet_to_df(cf_id)
                config = df_load.iloc[0].to_dict() if not df_load.empty else None
                
                if config:
                    sub_title = config.get('교과명', config.get('과목명', '미정'))
                    st.markdown(f"<div style='background:#f8fafc; border:1px solid #e2e8f0; padding:10px 12px; border-radius:8px; margin-bottom:15px; font-size:13px;'><span style='font-weight:600; color:#475569;'>교과 특이사항:</span> &nbsp;🧬 <b>{sub_title}</b> ({config.get('학기통합명','')})</div>", unsafe_allow_html=True)
                    
                    with st.form("student_inner_login_form"):
                        st.markdown("<div style='font-size:14px; font-weight:700; color:#1e293b; margin-bottom:6px;'>🔐 학생 조회 인적 정보 입력</div>", unsafe_allow_html=True)
                        classes = [f"{x.strip()}반" for x in str(config.get('선택된반 목록', '1')).split(",") if x.strip()]
                        if not classes: classes = ["1반"]
                        
                        c1, c2, c3 = st.columns(3)
                        with c1: b_in = st.selectbox("반", classes)
                        with c2: n_in = st.number_input("번호", 1, 50, 1)
                        with c3: name_in = st.text_input("이름", placeholder="이름")
                        
                        pw_in = st.text_input("조회 비밀번호", type="password", placeholder="학생 개인 암호")
                        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                        
                        if st.form_submit_button("점수 조회하기", use_container_width=True, type="primary"):
                            df_st = load_sheet_to_df(sf_id)
                            if df_st.empty:
                                st.error("성적 상세 기록 데이터가 비어 있습니다.")
                            else:
                                if '확인여부' in df_st.columns: df_st['확인여부'] = df_st['확인여부'].astype(str).replace(['nan', 'None', ''], '미확인')
                                if '확인시간' in df_st.columns: df_st['확인시간'] = df_st['확인시간'].astype(str).replace(['nan', 'None', ''], '')
                                res = df_st[(df_st['반'].astype(int)==int(b_in.replace("반",""))) & (df_st['번호'].astype(int)==n_in) & (df_st['이름'].astype(str)==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                                if not res.empty:
                                    idx = res.index[0]
                                    scores, total_sum = {}, 0
                                    for i in range(int(config['항목개수'])):
                                        h_name = config.get(f'항목{i+1}_이름', f'항목{i+1}')
                                        if h_name in df_st.columns:
                                            val = df_st.loc[idx, h_name]; scores[h_name] = [val]
                                            try:
                                                if pd.notna(val): total_sum += float(val)
                                            except: pass
                                    if float(total_sum).is_integer(): scores['합계'] = [int(total_sum)]
                                    else: scores['합계'] = [round(total_sum, 2)]
                                    
                                    df_st.loc[idx, '확인여부'] = str("확인 완료")
                                    df_st.loc[idx, '확인시간'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                    save_df_to_sheet(sf_id, df_st)
                                    show_result_dialog(name_in, scores)
                                else:
                                    st.error("❌ 입력한 인적 사항 또는 학생 비밀번호가 틀렸습니다.")
                                    
    # 하단 카피라이트 이미지 맞춤 적용
    st.markdown("<div class='card-footer-notice'>copyright hushpark @ 재미니 </div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================
# 구역 2. 로그인 성공 후 개방되는 와이드 ERP 제어판 (첫 번째 이미지 프레임 적용)
# =========================================================================
else:
    # 🎯 [첫 번째 이미지 양식]: 파란색 와이드 마스터 네비게이션 탑 바 배치
    st.markdown("""
        <div class="blue-top-nav-bar">
            <div class="top-bar-left">
                <span>💻 v2.2611.1_PRO</span><span style="color:#93c5fd; margin:0 12px;">|</span><span>양현고등학교 성적처리 데이터 포털</span>
            </div>
            <div class="top-bar-right">
                <span>접속계정: 박성제 [ <b>hushpark</b> ]</span>
                <span style="color:#93c5fd;">|</span>
                <span>권한: 과목 통합 관리자</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 🎯 [첫 번째 이미지 양식]: 좌측 메뉴 트리 사이드바 대시보드 구조화
    with st.sidebar:
        st.markdown("### 📋 서담형 채점 제어")
        choice = st.radio("메뉴 트리 구성", ["과목 구성 지정", "평가 기본 세팅", "데이터 연동(CSV)", "통합 관리 센터"], label_visibility="collapsed")
        st.session_state["teacher_sidebar_menu"] = choice
        
        st.markdown("<br><hr style='margin:10px 0;'><br>", unsafe_allow_html=True)
        if st.button("🔐 마스터 암호 변경", use_container_width=True): password_update_dialog()
        if st.button("🎒 시스템 로그아웃", key="side_logout_btn", use_container_width=True):
            st.session_state["admin_logged_in"] = False
            st.session_state["show_monitor_view"] = False
            st.session_state["show_delete_panel"] = False
            st.rerun()

    # 우측 실시간 본문 영역 가동
    st.markdown(f"<h3 style='text-align:left !important; font-size:22px !important; font-weight:800 !important; color:#0f172a; margin-top:-10px;'>📌 현재 메뉴: {st.session_state['teacher_sidebar_menu']}</h3>", unsafe_allow_html=True)
    has_active = "active_subject" in st.session_state and st.session_state.active_subject
    
    frame_left, frame_right = st.columns([1.5, 4.2])
    
    with frame_left:
        with st.container(border=True):
            st.markdown("<h4>📂 제어판 작동 스위치</h4>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
            
            sel_g = st.selectbox("1단계: 교과군 분류", options=g_opts, index=st.session_state.sel_group_idx, key="dashboard_sel_g")
            
            final_sub, t_g = "", ""
            if sel_g == "➕ 신규 과목 개설":
                t_g = st.selectbox("추가 위치 지정", ["인문·사회군", "수리·과학군", "예체능군"])
                final_sub = st.text_input("✏️ 새 과목명 입력", placeholder="과목명 입력", key="dashboard_new_sub_input").strip()
            elif sel_g != "교과군 선택":
                s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                idx_s = st.session_state.sel_sub_idx if st.session_state.sel_sub_idx < len(s_opts) else 0
                sel_s = st.selectbox("2단계: 세부 과목 선택", options=s_opts, index=idx_s, key="dashboard_sel_s")
                if sel_s != "과목 선택": final_sub = sel_s
            else: st.selectbox("2단계: 세부 과목 선택", ["과목 선택 대기"], disabled=True, key="dashboard_sel_s_disabled")
                
            sel_gr = st.selectbox("3단계: 관리 학년 지정", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx, key="dashboard_sel_gr")
            grd = sel_gr.replace("학년", "") if sel_gr != "학년 선택" else ""
            sel_se = st.selectbox("4단계: 대상 학기 선택", options=SEMESTER_OPTIONS, index=st.session_state.sel_semester_idx, key="dashboard_sel_se")
            sem = sel_se if sel_se != "학기 선택" else ""
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 대상 과목 활성화", use_container_width=True, key="side_activate_btn", type="primary"):
                if final_sub and grd and sem:
                    if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub)
                    st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester = final_sub, grd, sem
                    st.session_state.sel_group_idx = g_opts.index(sel_g)
                    if sel_g != "➕ 신규 과목 개설": st.session_state.sel_sub_idx = s_opts.index(final_sub)
                    st.session_state.sel_grade_idx = GRADE_OPTIONS.index(sel_gr)
                    st.session_state.sel_semester_idx = SEMESTER_OPTIONS.index(sel_se)
                    
                    cf_id, sf_id = get_sheet_names_id(final_sub, grd, sem)
                    df_init = load_sheet_to_df(cf_id)
                    if not df_init.empty:
                        r_dict = df_init.iloc[0].to_dict()
                        st.session_state["saved_classes_list"] = str(r_dict.get('선택된반 목록', ''))
                        st.session_state["saved_items_count"] = int(r_dict.get('항목개수', 0))
                    else:
                        st.session_state["saved_classes_list"] = ''
                        st.session_state["saved_items_count"] = 0
                        
                    st.session_state["just_saved_success"] = False
                    st.session_state["show_delete_panel"] = False; st.rerun()
                else: st.warning("과목 정보를 빠짐없이 선택해 주세요.")

    with frame_right:
        # [메뉴 1] 과목 구성 지정
        if st.session_state["teacher_sidebar_menu"] == "과목 구성 지정":
            if has_active:
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                cf_id, sf_id = get_sheet_names_id(sub, grd, sem)
                df_load_main = load_sheet_to_df(cf_id)
                conf = {}
                if not df_load_main.empty:
                    raw_dict = df_load_main.iloc[0].to_dict()
                    conf['과목명'] = raw_dict.get('과목명', raw_dict.get('교과명', sub))
                    conf['학년'] = raw_dict.get('학년', grd)
                    conf['학기통합명'] = raw_dict.get('학기통합명', sem)
                    conf['선택된반 목록'] = str(raw_dict.get('선택된반 목록', ''))
                    conf['항목개수'] = raw_dict.get('항목개수', 0)
                    for k, v in raw_dict.items():
                        if '항목' in k: conf[k] = v
                
                st.markdown(f"<div style='background-color:#eff6ff; border:1px solid #bfdbfe; padding:10px 15px; border-radius:8px; margin-bottom:15px; font-size:14px; font-weight:600; color:#1e40af;'>📍 현재 로드된 데이터베이스 파티션: [{sub}] {grd}학년 ({sem})</div>", unsafe_allow_html=True)
                
                with st.form(key=f"right_config_form_secure_{sub}"):
                    saved_cl_str = st.session_state.get("saved_classes_list", conf.get('선택된반 목록', ''))
                    saved_cl = []
                    if saved_cl_str:
                        saved_cl = [int(x.strip()) for x in str(saved_cl_str).split(",") if x.strip().isdigit()]
                    
                    default_items_count = st.session_state.get("saved_items_count", int(conf.get('항목개수', 0)))

                    st.markdown("<div style='font-size:13px; font-weight:700; color:#334155; margin-bottom:6px;'>🏫 담당 학급(반) 지정</div>", unsafe_allow_html=True)
                    sel_cl = []
                    cols_cl = st.columns(6)
                    for i in range(1, 13):
                        with cols_cl[(i-1)%6]:
                            if st.checkbox(f"{i}반", value=(i in saved_cl), key=f"chk_class_{i}"): sel_cl.append(i)

                    st.markdown("<div style='margin-top:12px; font-size:13px; font-weight:700; color:#334155; margin-bottom:6px;'>✍️ 평가 수행 항목 수 설정</div>", unsafe_allow_html=True)
                    n_item = st.number_input("평가 항목 개수", min_value=0, max_value=10, value=default_items_count, key="num_items_input")
                    
                    item_names = []
                    if n_item > 0:
                        for i in range(n_item):
                            if i % 2 == 0:
                                cols_i = st.columns(2)
                                with cols_i[0]: name = st.text_input(f"{i+1}번 항목명", value=conf.get(f'항목{i+1}_이름', ""), placeholder=f"수행평가{i+1}", key=f"item_name_input_{sub}_{i+1}")
                            else:
                                with cols_i[1]: name = st.text_input(f"{i+1}번 항목명", value=conf.get(f'항목{i+1}_이름', ""), placeholder=f"수행평가{i+1}", key=f"item_name_input_{sub}_{i+1}")
                            item_names.append(name.strip())

                        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                        if st.form_submit_button("💾 구글 클라우드에 과목 설정 최종 저장", type="primary", use_container_width=True):
                            if sel_cl and all(item_names):
                                classes_string = ",".join(map(str, sorted(sel_cl)))
                                d = {"과목명": sub, "교과명": sub, "학년": grd, "학기통합명": sem, "선택된반 목록": classes_string, "항목개수": n_item}
                                for i, name_val in enumerate(item_names): d[f"항목{i+1}_이름"] = name_val
                                
                                get_google_sheet(cf_id)
                                save_df_to_sheet(cf_id, pd.DataFrame([d]))
                                get_google_sheet(sf_id)
                                
                                st.session_state["saved_classes_list"] = classes_string
                                st.session_state["saved_items_count"] = n_item
                                st.session_state["just_saved_success"] = True
                                st.toast("💾 과목 사양이 완벽히 마운트되었습니다!"); st.rerun()
                            else: st.error("❌ 반 지정 및 항목명 입력을 완료해 주세요.")
                            
                if st.session_state.get("just_saved_success", False):
                    st.markdown(f"""
                        <div class="next-step-box">
                            <b>✅ 구조 세팅 완료!</b> 다음 작업을 차례대로 수행하세요:<br>
                            1️⃣ 왼쪽 메뉴에서 <b>[평가 기본 세팅]</b>으로 이동하여 양식을 확보합니다.<br>
                            2️⃣ 성적 데이터 연동 탭을 통해 일괄 성적 대장을 마운트해 주세요.
                        </div>
                    """, unsafe_allow_html=True)
            else: st.info("👈 왼쪽 서랍창에서 과목 사양 분류를 맞추신 뒤 [🚀 대상 과목 활성화] 버튼을 실행해 주세요.")

        # [메뉴 2] 평가 기본 세팅
        elif st.session_state["teacher_sidebar_menu"] == "평가 기본 세팅":
            if has_active:
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                cf_id, sf_id = get_sheet_names_id(sub, grd, sem)
                
                n_current = st.session_state.get("num_items_input", 0)
                live_item_names = []
                for idx in range(n_current):
                    val_live = st.session_state.get(f"item_name_input_{sub}_{idx+1}", f"수행{idx+1}").strip()
                    live_item_names.append(val_live if val_live else f"수행{idx+1}")

                with st.container(border=True):
                    st.markdown("<h4>📥 CSV 일괄 연동용 매트릭스 다운로드</h4>", unsafe_allow_html=True)
                    st.markdown("<p style='font-size:13px; color:#64748b;'>구글 시트 업로드 전용 양식 템플릿입니다.</p>", unsafe_allow_html=True)
                    
                    base_headers = ["반", "번호", "이름", "비밀번호", "확인여부", "확인시간"]
                    final_headers = base_headers + live_item_names
                    sample_row = ["1", "1", "홍길동", "1234", "미확인", ""] + ["0"] * len(live_item_names)
                    
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(final_headers)
                    writer.writerow(sample_row)
                    csv_data = output.getvalue().encode('utf-8-sig')
                    
                    st.download_button(label="📥 전용 CSV 포맷 템플릿 파일 다운로드", data=csv_data, file_name=f"upload_format_{sub}_{sem}.csv", mime="text/csv", use_container_width=True)
            else: st.info("과목을 먼저 활성화한 후 템플릿을 생성할 수 있습니다.")

        # [메뉴 3] 데이터 연동(CSV)
        elif st.session_state["teacher_sidebar_menu"] == "데이터 연동(CSV)":
            if has_active:
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                cf_id, sf_id = get_sheet_names_id(sub, grd, sem)
                
                with st.container(border=True):
                    st.markdown("<h4>📤 성적 대장 일괄 마운트 (CSV 직송)</h4>", unsafe_allow_html=True)
                    up_f = st.file_uploader("성적 데이터 업로드", type="csv", label_visibility="collapsed")
                    if up_f:
                        try:
                            df_up = pd.read_csv(up_f, encoding='cp949')
                            if save_df_to_sheet(sf_id, df_up): st.success("🎉 성적 데이터베이스가 구글 클라우드에 성공적으로 바인딩되었습니다!"); st.rerun()
                            else: st.error("시트 기록 실패")
                        except: st.error("인코딩 타입을 확인하세요. (ANSI/CP949 포맷 필수)")
            else: st.info("대상을 먼저 연동 및 활성화해 주세요.")

        # [메뉴 4] 통합 관리 센터
        elif st.session_state["teacher_sidebar_menu"] == "통합 관리 센터":
            tab_del, tab_mon = st.tabs(["🔒 데이터 삭제 및 클렌징", "📊 실시간 연동 현황 확인"])
            
            with tab_del:
                existing_dbs = get_active_databases()
                if not existing_dbs: st.info("폐기할 클라우드 파티션이 없습니다.")
                else:
                    sem_opts = [f"📚 {d['subject']} | {d['grade']} | {d['semester']}" for d in existing_dbs]
                    selected_sem_str = st.selectbox("삭제 대상 선택", options=sem_opts, label_visibility="collapsed")
                    t_db = existing_dbs[sem_opts.index(selected_sem_str)]
                    verify_code = f"{t_db['subject']}_{t_db['grade'].replace('학년','')}_{t_db['semester'].replace('학년도','').replace(' ', '')}"
                    
                    st.markdown(f"<div style='font-size:12px; margin-bottom:4px;'>인증코드 재입력: <code style='color:#ef4444;'>{verify_code}</code></div>", unsafe_allow_html=True)
                    user_confirm = st.text_input("인증코드 입력", label_visibility="collapsed")
                    if st.button("🚨 해당 데이터 파티션 영구 폐기 실행", disabled=(user_confirm != verify_code), type="primary", use_container_width=True):
                        cf_id, sf_id = get_sheet_names_id(t_db['subject'], t_db['grade'].replace("학년",""), t_db['semester'])
                        if gc:
                            try:
                                sh = gc.open(SPREADSHEET_NAME)
                                for n in [cf_id, sf_id]: sh.del_worksheet(sh.worksheet(n))
                            except: pass
                        st.toast("정상 제거 완료!"); st.rerun()
            
            with tab_mon:
                if has_active:
                    sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                    cf_id, sf_id = get_sheet_names_id(sub, grd, sem)
                    df_monitor = load_sheet_to_df(sf_id)
                    if not df_monitor.empty: st.dataframe(df_monitor, use_container_width=True, hide_index=True)
                    else: st.warning("현재 학기 연동 기록 테이블이 비어 있습니다.")
                else: st.info("활성화된 대상이 없습니다.")

        st.markdown("<div class='custom-guide-bar'>💡 <b>[🚀 대상 과목 활성화]</b> 단추를 누르시면 상호 동기화 처리를 진행합니다.</div>", unsafe_allow_html=True)