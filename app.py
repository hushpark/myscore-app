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
# 🔐 [구글 시트 API 연동 설정] secrets.toml 기반 안전 접속 엔진
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

# ⚡ [초고속 렉 방지]: 데이터 로드 시 구글 서버의 과부하를 막는 캐싱 엔진
@st.cache_data(ttl=10)
def load_sheet_to_df(sheet_name):
    wks = get_google_sheet(sheet_name)
    if wks is None: return pd.DataFrame()
    try:
        records = wks.get_all_records()
        if not records: return pd.DataFrame()
        return pd.DataFrame(records)
    except:
        return pd.DataFrame()

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

# ⚡ [초고속 렉 방지]: 활성화된 과목 스위칭 목록 조회 딜레이 차단
@st.cache_data(ttl=30)
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

def load_master_subjects_local():
    return {
        "인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"],
        "수리·과학군": ["수학", "과학", "기술·가정", "정보"],
        "예체능군": ["음악", "미술", "체육"]
    }

def reset_all_data():
    st.cache_resource.clear()
    st.cache_data.clear()
    keep_keys = {
        "page_status": st.session_state.get("page_status", "teacher_main"),
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
    for k, v in keep_keys.items():
        st.session_state[k] = v
    st.session_state["saved_items_count"] = 0
    st.session_state["just_saved_success"] = False
    st.success("🎉 현재 구역의 입력 데이터가 깨끗하게 초기화되었습니다!")
    st.rerun()

# --- layout 설정을 centered로 고정하여 기본 프레임 최적화 ---
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="centered")

# =========================================================================
# 🎯 [CSS 최종 완결판] 미니 로그인 박스 및 모던 UI 스타일 복원
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
        div[data-testid="stHeader"] { display: none !important; background: transparent !important; }
        footer { display: none !important; }
        .block-container { padding-top: 2.5rem !important; padding-bottom: 0.5rem !important; }
        
        /* 메인 콘텐츠 카드 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #e2e8f0 !important;
            padding: 20px 25px 30px 25px !important; 
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            background-color: #ffffff !important;
            max-width: 1450px !important; 
            margin: 0px auto !important; 
        }
        div[data-testid="stForm"] { border: none !important; padding: 0px !important; box-shadow: none !important; background-color: transparent !important; }
        h2 { font-size: 22px !important; color: #0f172a !important; font-weight: 800 !important; margin: 5px 0 10px 0 !important; white-space: nowrap !important; text-align: center; }
        h4 { font-size: 14px !important; font-weight: 700 !important; color: #475569 !important; margin-top: 0px !important; margin-bottom: 2px !important; white-space: nowrap !important; }
        
        div.stButton > button[key="outer_teacher_btn"],
        div.stButton > button[key="outer_student_btn"],
        div.stButton > button[key="outer_logout_btn"] {
            width: fit-content !important; min-width: auto !important; padding: 3px 12px !important; font-size: 12px !important; border-radius: 6px !important; border: 1px solid #cbd5e1 !important; color: #475569 !important; background-color: #ffffff !important; white-space: nowrap !important;
        }
        div[data-testid="stHorizontalBlock"] div.stButton button { white-space: nowrap !important; word-break: keep-all !important; }
        div[data-testid="stVerticalBlock"] > div:has(div.stButton), div[data-testid="stVerticalBlock"] > div:has(div.stSelectbox) { padding-bottom: 0px !important; margin-bottom: -4px !important; }
        div.stButton button { margin: 0px auto !important; padding-top: 5px !important; padding-bottom: 5px !important; transition: all 0.15s ease-in-out !important; }
        
        div.stDownloadButton, div.stDownloadButton button, div.stDownloadButton button * { font-size: 11px !important; white-space: nowrap !important; word-break: keep-all !important; }
        div.stDownloadButton button { padding: 4px 6px !important; }
        div.stDownloadButton { margin-bottom: -15px !important; }
        div.compact-upload-box { padding: 6px 10px !important; margin-top: 2px !important; margin-bottom: 2px !important; }
        div[data-testid="stFileUploader"] { padding-top: 0px !important; margin-top: -10px !important; }
        
        div.custom-guide-bar {
            background-color: #eff6ff !important; border: 2px dashed #93c5fd !important; padding: 10px !important; border-radius: 8px !important; margin-top: 15px !important; margin-bottom: 10px !important; color: #1e3a8a !important; font-size: 14px !important; text-align: center !important; font-weight: 500 !important; white-space: nowrap !important;
        }
        div.next-step-box {
            background-color: #f0fdf4 !important; border: 2px solid #bbf7d0 !important; padding: 15px !important; border-radius: 10px !important; margin-top: 15px !important; margin-bottom: 15px !important; color: #166534 !important; font-size: 14px !important; line-height: 1.6 !important;
        }
    </style>
""", unsafe_allow_html=True)

def get_sheet_names_id(subject, grade, semester_str):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    safe_semester = semester_str.replace(" ", "_").replace("/", "_")
    return f"cfg_{safe_subject}_{grade}_{safe_semester}", f"st_{safe_subject}_{grade}_{safe_semester}"

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_name, scores_dict):
    st.markdown(f"<div style='margin-bottom:15px;'><b>{student_name}</b> 학생의 성적 내역입니다.</div>", unsafe_allow_html=True)
    st.table(pd.DataFrame(scores_dict))
    if st.button("확인 후 닫기", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()

# 세션 초기화 처리 안전장치
if "page_status" not in st.session_state: st.session_state["page_status"] = "student_main"
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "sel_group_idx" not in st.session_state: st.session_state.sel_group_idx = 0
if "sel_sub_idx" not in st.session_state: st.session_state.sel_sub_idx = 0
if "sel_grade_idx" not in st.session_state: st.session_state.sel_grade_idx = 0
if "sel_semester_idx" not in st.session_state: st.session_state.sel_semester_idx = 0

SUBJECT_MAP = load_master_subjects_local()
GRADE_OPTIONS = ["학년 선택", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]

# ==========================================
# 🔄 화면 분기 구동 영역 
# ==========================================
if st.session_state["page_status"] == "student_main":
    st.markdown("<style>div[data-testid='stVerticalBlockBorderWrapper'] { border: 1px solid #e2e8f0 !important; padding: 35px 40px !important; border-radius: 12px !important; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; background-color: #ffffff !important; max-width: 500px !important; margin: 0px auto 20px auto !important; }</style>", unsafe_allow_html=True)
    col_empty, col_btn = st.columns([3, 1])
    with col_btn:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if st.button("🔓 교사용 제어판", key="outer_teacher_btn"): st.session_state["page_status"] = "teacher_auth"; st.rerun()
            
    active_dbs = get_active_databases()
    with st.container(border=True):
        st.markdown("<h2>🎒 수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        
        if not active_dbs:
            st.warning("현재 등록된 성적 데이터가 없습니다.")
        else:
            opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs]
            sel_s = st.selectbox("조회할 과목 선택", opts_s, label_visibility="collapsed", key="student_select_sub")
            
            if sel_s != "과목 및 학기를 선택하세요.":
                db = active_dbs[opts_s.index(sel_s)-1]
                cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                
                df_load = load_sheet_to_df(cf_id)
                config = df_load.iloc[0].to_dict() if not df_load.empty else None
                
                if config:
                    sub_title = config.get('교과명', config.get('과목명', '미정'))
                    st.markdown(f"<div style='background:#f1f5f9; padding:12px 15px; border-radius:8px; margin-bottom:20px; font-size:14px;'>선택된 교과: &nbsp;🧬 <b>{sub_title}</b></div>", unsafe_allow_html=True)
                    
                    with st.form("login_form"):
                        classes = [f"{x.strip()}반" for x in str(config.get('선택된반 목록', '1')).split(",") if x.strip()]
                        if not classes: classes = ["1반"]
                        
                        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
                        with c1: b_in = st.selectbox("반", classes)
                        with c2: n_in = st.number_input("번호", 1, 50, 1)
                        with c3: name_in = st.text_input("이름", placeholder="홍길동")
                        with c4: pw_in = st.text_input("비밀번호", type="password", placeholder="****")
                        
                        if st.form_submit_button("🔍 내 점수 확인하기", use_container_width=True, type="primary"):
                            df_st = load_sheet_to_df(sf_id)
                            if df_st.empty: st.error("성적 데이터가 아직 연동되지 않은 교과입니다.")
                            else:
                                res = df_st[(df_st['반'].astype(int)==int(b_in.replace("반",""))) & (df_st['번호'].astype(int)==n_in) & (df_st['이름'].astype(str)==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                                if not res.empty:
                                    idx = res.index[0]
                                    scores = {}
                                    for i in range(int(config['항목개수'])):
                                        h_name = config.get(f'항목{i+1}_이름', f'항목{i+1}')
                                        if h_name in df_st.columns:
                                            scores[h_name] = [df_st.loc[idx, h_name]]
                                    show_result_dialog(name_in, scores)
                                else: st.error("입력한 학생 정보 또는 비밀번호가 일치하지 않습니다.")

elif st.session_state["page_status"] == "teacher_auth":
    # 🌟 [그림1 복원]: 와이드 화면을 컴팩트한 미니 로그인 폼 상자로 완벽 복원
    st.markdown("<style>div[data-testid='stVerticalBlockBorderWrapper'] { border: 1px solid #e2e8f0 !important; padding: 35px 40px !important; border-radius: 12px !important; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; background-color: #ffffff !important; max-width: 450px !important; margin: 80px auto 20px auto !important; }</style>", unsafe_allow_html=True)
    with st.form("admin_login_form"):
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 15px 0px;'>⚙️ 교과 통합 관리자</h2>", unsafe_allow_html=True)
        admin_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력", label_visibility="collapsed")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.form_submit_button("로그인", use_container_width=True, type="primary"):
            if admin_pw == "1234": st.session_state["admin_logged_in"] = True; st.session_state["page_status"] = "teacher_main"; st.rerun()
            else: st.error("❌ 비밀번호가 틀렸습니다.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎒 학생 화면으로 돌아가기", key="outer_student_btn", use_container_width=True): st.session_state["page_status"] = "student_main"; st.rerun()

elif st.session_state["page_status"] == "teacher_main":
    if not st.session_state["admin_logged_in"]: st.session_state["page_status"] = "teacher_auth"; st.rerun()
    col_empty, col_logout = st.columns([6, 1.4])
    with col_logout:
        if st.button("🎒 학생 화면", key="outer_logout_btn", use_container_width=True):
            # 🌟 [그림2 스위칭 복원]: 학생 화면에 갔다 와도 활성화 과목 락(Lock)을 유지하기 위해 핵심 값 유지 보존
            st.session_state["page_status"] = "student_main"
            st.rerun()

    with st.container(border=True):
        st.markdown("<h2>⚙️ 교과·학년 통합 제어 센터</h2>", unsafe_allow_html=True)
        
        # 원격 안전 신호등 고정
        if gc is None:
            st.markdown("<div style='background-color:#FDE8E8; border:1px solid #F8B4B4; padding:10px; border-radius:6px; color:#9B1C1C; font-weight:bold; font-size:13px; text-align:center; margin-bottom:15px;'>❌ [연결 실패] 스트림릿 secrets 열쇠 양식이 올바르지 않습니다.</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background-color:#E1F5FE; border:1px solid #B3E5FC; padding:10px; border-radius:6px; color:#01579B; font-weight:bold; font-size:13px; text-align:center; margin-bottom:15px;'>🟢 [원격 연결 성공] 구글 API 연동 완벽 완료! 드라이브 파일 [ {SPREADSHEET_NAME} ] 결합 완료.</div>", unsafe_allow_html=True)

        frame_left, frame_right = st.columns([1.4, 4.2])
        has_active = "active_subject" in st.session_state and st.session_state.active_subject
        
        with frame_left:
            st.markdown("<h4>📁 대상 과목 및 학기 선택</h4>", unsafe_allow_html=True)
            g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군"]
            sel_g = st.selectbox("1단계: 교과군 분류", options=g_opts, index=st.session_state.sel_group_idx, label_visibility="collapsed")
            
            final_sub = ""
            if sel_g != "교과군 선택":
                s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                idx_s = st.session_state.sel_sub_idx if st.session_state.sel_sub_idx < len(s_opts) else 0
                sel_s = st.selectbox("2단계: 세부 과목 선택", options=s_opts, index=idx_s, label_visibility="collapsed")
                if sel_s != "과목 선택": final_sub = sel_s
            else: st.selectbox("2단계: 세부 과목 선택", ["과목 선택 대기"], disabled=True, label_visibility="collapsed")
                
            sel_gr = st.selectbox("3단계: 관리 학년 지정", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx, label_visibility="collapsed")
            final_gr = sel_gr.replace("학년", "") if sel_gr != "학년 선택" else ""
            sel_se = st.selectbox("4단계: 대상 학기 선택", options=SEMESTER_OPTIONS, index=st.session_state.sel_semester_idx, label_visibility="collapsed")
            final_se = sel_se if sel_se != "학기 선택" else ""
            
            if st.button("🚀 과목 활성화", use_container_width=True, key="side_activate_btn"):
                if final_sub and final_gr and final_se:
                    st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester = final_sub, final_gr, final_se
                    st.session_state.sel_group_idx = g_opts.index(sel_g)
                    st.session_state.sel_sub_idx = s_opts.index(final_sub)
                    st.session_state.sel_grade_idx = GRADE_OPTIONS.index(sel_gr)
                    st.session_state.sel_semester_idx = SEMESTER_OPTIONS.index(sel_se)
                    
                    cf_id, sf_id = get_sheet_names_id(final_sub, final_gr, final_se)
                    df_init = load_sheet_to_df(cf_id)
                    if not df_init.empty:
                        r_dict = df_init.iloc[0].to_dict()
                        st.session_state["saved_classes_list"] = r_dict.get('선택된반 목록', '')
                        st.session_state["saved_items_count"] = int(r_dict.get('항목개수', 0))
                    else:
                        st.session_state["saved_classes_list"] = ''
                        st.session_state["saved_items_count"] = 0
                        
                    st.session_state["just_saved_success"] = False; st.rerun()
                else: st.warning("과목, 학년, 학기 데이터를 누락 없이 모두 선택해 주세요.")

            if has_active:
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                cf_id, sf_id = get_sheet_names_id(sub, grd, sem)
                
                n_current = st.session_state.get("num_items_input", 0)
                live_item_names = [st.session_state.get(f"item_name_input_{sub}_{idx+1}", f"수행{idx+1}").strip() for idx in range(n_current)]

                with st.container(border=True):
                    st.markdown('<div class="compact-upload-box">', unsafe_allow_html=True)
                    st.markdown("<div style='font-size:12px; font-weight:600; color:#475569; margin-bottom:6px;'>📁 성적 일괄 업로드 (클라우드 직송)</div>", unsafe_allow_html=True)
                    
                    base_headers = ["반", "번호", "이름", "비밀번호", "확인여부", "확인시간"]
                    final_headers = base_headers + live_item_names 
                    sample_row = ["1", "1", "홍길동", "1234", "미확인", ""] + ["0"] * len(live_item_names)
                    
                    output = io.StringIO()
                    csv.writer(output).writerow(final_headers)
                    csv.writer(output).writerow(sample_row)
                    
                    st.download_button(label="📥 예시 파일 다운로드", data=output.getvalue().encode('utf-8-sig'), file_name=f"sample_students_{sub}_{sem}.csv", mime="text/csv", key="btn_download_sample")
                    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
                    
                    up_f = st.file_uploader("성적 CSV 업로드", type="csv", label_visibility="collapsed", key="csv_uploader_reset")
                    if up_f:
                        try:
                            df_up = pd.read_csv(up_f, encoding='cp949')
                            if save_df_to_sheet(sf_id, df_up):
                                st.toast("🎉 구글 시트로 성적 동기화 완벽 완료!")
                                del st.session_state["csv_uploader_reset"]
                                st.rerun()
                        except:
                            st.error("❌ 인코딩 포맷을 확인해 주세요. (EUC-KR 또는 CP949)")
                    st.markdown('</div>', unsafe_allow_html=True)
                        
            if st.button("🗑️ 시스템 초기화", key="side_reset_btn"): reset_all_data()

        with frame_right:
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
                    conf['선택된반 목록'] = raw_dict.get('선택된반 목록', '')
                    conf['항목개수'] = raw_dict.get('항목개수', 0)
                    for k, v in raw_dict.items():
                        if '항목' in k: conf[k] = v
                
                st.markdown(f"<div style='background-color:#eff6ff; border:1px solid #bfdbfe; padding:8px 12px; border-radius:6px; margin-bottom:12px; text-align:center; font-size:13px; font-weight:600; color:#1e40af;'>📍 작업 구역: [{sub}] {grd}학년 ({sem})</div>", unsafe_allow_html=True)

                # ⚡ [회색 화면 완치 폼 격리]: 글자를 타이핑할 때 원격 조회를 끊어내어 초고속 메모장 스피드 구현 완료
                with st.form(key=f"right_config_form_{sub}"):
                    saved_cl_str = st.session_state.get("saved_classes_list", str(conf.get('선택된반 목록', '')))
                    saved_cl = [int(x) for x in str(saved_cl_str).replace("[","").replace("]","").split(",") if str(x).strip()] if saved_cl_str else []
                    default_items_count = st.session_state.get("saved_items_count", int(conf.get('항목개수', 0)))

                    st.markdown("<div style='font-size:12px; font-weight:600; color:#475569;'>🏫 담당 학급(반) 지정</div>", unsafe_allow_html=True)
                    sel_cl = []
                    cols_cl = st.columns(6)
                    for i in range(1, 13):
                        with cols_cl[(i-1)%6]:
                            if st.checkbox(f"{i}반", value=i in saved_cl, key=f"chk_class_{i}"): sel_cl.append(i)

                    st.markdown("<div style='margin-top:8px; font-size:12px; font-weight:600; color:#475569;'>✍️ 평가 항목 설정</div>", unsafe_allow_html=True)
                    n_item = st.number_input("평가 항목 개수", min_value=0, max_value=10, value=default_items_count, key="num_items_input")
                    
                    item_names = []
                    if n_item > 0:
                        for i in range(n_item):
                            if i % 2 == 0:
                                cols_i = st.columns(2)
                                with cols_i[0]:
                                    name = st.text_input(f"{i+1}번 항목명", value=conf.get(f'항목{i+1}_이름', ""), placeholder=f"예: 수행평가{i+1}", key=f"item_name_input_{sub}_{i+1}")
                            else:
                                with cols_i[1]:
                                    name = st.text_input(f"{i+1}번 항목명", value=conf.get(f'항목{i+1}_이름', ""), placeholder=f"예: 수행평가{i+1}", key=f"item_name_input_{sub}_{i+1}")
                            item_names.append(name.strip())

                    # ✨ [선생님의 동선 배치 복원]: 항목창이 끝나는 줄 바로 아랫줄에 자연스럽게 버튼 결합
                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    submit_btn = st.form_submit_button(f"💾 [{sub}] 과목 사양 최종 저장하기", type="primary", use_container_width=True)
                    
                    if submit_btn:
                        if sel_cl and all(item_names):
                            classes_string = ",".join(map(str, sorted(sel_cl)))
                            d = {
                                "과목명": sub, "교과명": sub, "학년": grd, "학기통합명": sem, 
                                "선택된반 목록": classes_string, "항목개수": n_item
                            }
                            for i, name_val in enumerate(item_names): d[f"항목{i+1}_이름"] = name_val
                            
                            get_google_sheet(cf_id)
                            save_df_to_sheet(cf_id, pd.DataFrame([d]))
                            get_google_sheet(sf_id)
                            
                            st.session_state["saved_classes_list"] = classes_string
                            st.session_state["saved_items_count"] = n_item
                            st.session_state["just_saved_success"] = True
                            st.toast("💾 설정이 구글 클라우드에 연동되었습니다!")
                            st.rerun()
                        else:
                            st.error("❌ 담당 학급(반)을 한 개 이상 선택하고, 항목명을 전부 완성해 주셔야 저장이 가능합니다.")

                # ✨ [선생님 전용 안내판]: 저장 성공 후 버튼 바로 아랫줄에 착 감겨서 송출되는 지침서
                if st.session_state.get("just_saved_success", False):
                    st.markdown(f"""
                        <div class="next-step-box">
                            <b>🎉 [{sub}] 과목의 평가 사양이 구글 클라우드 데이터베이스에 최종 설정(저장)되었습니다!</b><br>
                            임무가 성공적으로 완료되었으니 다음 작업을 순서대로 진행해 주세요:<br>
                            <hr style='margin:8px 0; border:none; border-top:1px solid #bbf7d0;'>
                            1️⃣ 왼쪽 하단 서랍에 있는 <b>📥 예시 파일 다운로드</b> 버튼을 누릅니다.<br>
                            2️⃣ 다운로드된 CSV 파일 양식을 열어 학생 인적 사항과 점수를 기입합니다.<br>
                            3️⃣ 파일 선택 창에 완성된 성적 파일을 업로드하시면 실시간 공시 서비스가 즉시 활성화됩니다!
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                st.info("👈 왼쪽 제어판에서 과목 사양을 선택한 뒤 [🚀 과목 활성화]를 눌러주세요.")

        st.markdown("<div class='custom-guide-bar'>💡 <b>[🚀 과목 활성화]</b>를 누르시면 해당 구글 시트 데이터베이스를 원격 로드합니다.</div>", unsafe_allow_html=True)