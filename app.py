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
# 🔐 [구글 시트 API 연동 설정] 비밀키 내부 찌꺼기를 원천 청소하는 무적 엔진
# =========================================================================
@st.cache_resource
def init_google_sheet_client():
    try:
        raw_secrets = st.secrets.get("gcp_service_account", None)
        if raw_secrets is None:
            return None
            
        credentials_info = dict(raw_secrets)
        
        # 🌟 [긴급 특수 처방]: 스트림릿 secrets 입력창에서 오염된 private_key 문자열을 원본으로 완전 강제 복원
        if "private_key" in credentials_info:
            pk = str(credentials_info["private_key"]).strip()
            # 따옴표 찌꺼기나 양끝 공백 전면 제거
            pk = pk.strip('"').strip("'").strip()
            # 역슬래시 n 문자로 깨진 줄바꿈 강제 교정
            pk = pk.replace("\\n", "\n")
            # 여러 줄로 쪼개지면서 유실된 헤더/푸터 양식 강제 복원 및 단일화
            if "-----BEGIN PRIVATE KEY-----" not in pk:
                pk = "-----BEGIN PRIVATE KEY-----\n" + pk
            if "-----END PRIVATE KEY-----" not in pk:
                pk = pk + "\n-----END PRIVATE KEY-----"
            # 내부 연속 줄바꿈 기호 깔끔하게 단일 정렬
            pk = re.sub(r'\n+', '\n', pk)
            credentials_info["private_key"] = pk
            
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

def reset_all_data():
    st.cache_resource.clear()
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

# --- 🎯 layout 설정을 centered로 고정하여 기본 프레임 최적화 ---
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="centered")

# =========================================================================
# 🎯 [CSS 최종 완결판] 데이터 삭제 버튼 단독 레드 조준 및 내부 탭 스타일링
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
        div[data-testid="stHeader"] { display: none !important; background: transparent !important; }
        footer { display: none !important; }
        .block-container { padding-top: 2.5rem !important; padding-bottom: 0.5rem !important; }
        
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
        with st.container(border=True): div.stButton button { white-space: nowrap !important; }
        div.stButton button { margin: 0px auto !important; padding-top: 5px !important; padding-bottom: 5px !important; transition: all 0.15s ease-in-out !important; }
        
        div.stButton > button[key='side_toggle_delete_btn'] p, div.stButton > button[key='side_toggle_delete_btn'] span {
            color: #ef4444 !important; text-decoration: underline !important; font-weight: 700 !important;
        }
        div.stDownloadButton, div.stDownloadButton button { font-size: 11px !important; white-space: nowrap !important; }
        div.compact-upload-box { padding: 6px 10px !important; }
        
        div.custom-guide-bar {
            background-color: #eff6ff !important; border: 2px dashed #93c5fd !important; padding: 10px !important; border-radius: 8px !important; margin-top: 15px !important; color: #1e3a8a !important; font-size: 14px; text-align: center; font-weight: 500;
        }
        div.next-step-box {
            background-color: #f0fdf4 !important; border: 2px solid #bbf7d0 !important; padding: 15px !important; border-radius: 10px !important; margin-top: 15px; color: #166534; font-size: 14px; line-height: 1.6;
        }
        div.monitor-table table th, div.monitor-table table td { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

def is_strong_password(pw):
    if len(pw) < 12: return False, "❌ 최소 12자리 이상이어야 합니다."
    if not re.search("[a-zA-Z]", pw): return False, "❌ 영문자가 포함되어야 합니다."
    if not re.search("[0-9]", pw): return False, "❌ 숫자가 포함되어야 합니다."
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", pw): return False, "❌ 특수문자가 포함되어야 합니다."
    return True, "✅ 사용 가능한 안전한 암호 조건입니다."

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
    return f"cfg_{safe_subject}_{grade}_{safe_semester}", f"st_{safe_subject}_{grade}_{safe_semester}"

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

if "page_status" not in st.session_state: st.session_state["page_status"] = "student_main"
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "show_monitor_view" not in st.session_state: st.session_state["show_monitor_view"] = False
if "show_delete_panel" not in st.session_state: st.session_state["show_delete_panel"] = False
if "sel_group_idx" not in st.session_state: st.session_state.sel_group_idx = 0
if "sel_sub_idx" not in st.session_state: st.session_state.sel_sub_idx = 0
if "sel_grade_idx" not in st.session_state: st.session_state.sel_grade_idx = 0
if "sel_semester_idx" not in st.session_state: st.session_state.sel_semester_idx = 0

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년 선택", "1학년", "2학년", "3학년"]
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]]
CURRENT_ADMIN_PW = load_admin_password()

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
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 5px 0px;'>🎒 수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; margin: 0px 0px 10px 0px; color: #475569;'>📝 개인별 성적 조회</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:14px; color:#64748b; margin-bottom:20px;'>과목과 해당 학기를 선택하고 정보를 입력해 주세요.</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        
        if not active_dbs:
            st.warning("현재 등록된 성적 데이터가 없습니다.")
        else:
            st.markdown("<div style='font-size:14px; font-weight:700; color:#0f172a; margin-bottom:8px;'>🎯 대상 과목 및 학기 선택</div>", unsafe_allow_html=True)
            opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs]
            sel_s = st.selectbox("과목 선택", opts_s, label_visibility="collapsed", key="student_select_sub")
            
            if sel_s != "과목 및 학기를 선택하세요.":
                db = active_dbs[opts_s.index(sel_s)-1]
                cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                config = load_sheet_to_df(cf_id).iloc[0].to_dict() if not load_sheet_to_df(cf_id).empty else None
                
                if config:
                    sub_title = config.get('교과명', config.get('과목명', '미정'))
                    st.markdown(f"<div style='background:#f1f5f9; padding:12px 15px; border-radius:8px;'><span style='font-weight:600;'>선택된 교과:</span> 🧬 <b>{sub_title}</b></div>", unsafe_allow_html=True)
                    
                    with st.form("login_form"):
                        classes = [f"{x.strip()}반" for x in str(config.get('선택된반 목록', '1')).split(",") if x.strip()]
                        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
                        with c1: b_in = st.selectbox("반", classes)
                        with c2: n_in = st.number_input("번호", 1, 50, 1)
                        with c3: name_in = st.text_input("이름")
                        with c4: pw_in = st.text_input("비밀번호", type="password")
                        
                        if st.form_submit_button("🔍 내 점수 확인하기", use_container_width=True, type="primary"):
                            df_st = load_sheet_to_df(sf_id)
                            if not df_st.empty:
                                res = df_st[(df_st['반'].astype(int)==int(b_in.replace("반",""))) & (df_st['번호'].astype(int)==n_in) & (df_st['이름'].astype(str)==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                                if not res.empty:
                                    idx = res.index[0]
                                    scores = {}
                                    for i in range(int(config['항목개수'])):
                                        h_name = config.get(f'항목{i+1}_이름', f'항목{i+1}')
                                        if h_name in df_st.columns: scores[h_name] = [df_st.loc[idx, h_name]]
                                    st.dialog("🎉 결과")(scores)

elif st.session_state["page_status"] == "teacher_auth":
    with st.form("admin_login_form"):
        admin_pw = st.text_input("비밀번호", type="password")
        if st.form_submit_button("로그인"):
            if admin_pw == CURRENT_ADMIN_PW: st.session_state["admin_logged_in"] = True; st.session_state["page_status"] = "teacher_main"; st.rerun()

elif st.session_state["page_status"] == "teacher_main":
    col_empty, col_logout = st.columns([6, 1.4])
    with col_logout:
        if st.button("🎒 학생 화면"): st.session_state["page_status"] = "student_main"; st.session_state["admin_logged_in"] = False; st.rerun()

    with st.container(border=True):
        st.markdown("<h2 style='text-align:center;'>⚙️ 교과·학년 통합 제어 센터</h2>", unsafe_allow_html=True)
        
        # =========================================================================
        # 🟢 실시간 연결 진단 보정 알림 신호등
        # =========================================================================
        if gc is None:
            st.markdown("<div style='background-color:#FDE8E8; border:1px solid #F8B4B4; padding:10px; border-radius:6px; color:#9B1C1C; font-weight:bold; font-size:13px; text-align:center;'>❌ [연결 실패] 스트림릿 secrets 설정에 구글 비밀 열쇠(gcp_service_account)가 완전히 누락되었거나 형식이 깨졌습니다!</div>", unsafe_allow_html=True)
        else:
            try:
                test_sh = gc.open(SPREADSHEET_NAME)
                st.markdown(f"<div style='background-color:#E1F5FE; border:1px solid #B3E5FC; padding:10px; border-radius:6px; color:#01579B; font-weight:bold; font-size:13px; text-align:center;'>🟢 [원격 연결 성공] 구글 API 연동 완료! 현재 파일 [ {SPREADSHEET_NAME} ]에 접근할 수 있습니다.</div>", unsafe_allow_html=True)
            except Exception as connect_err:
                st.markdown(f"<div style='background-color:#FEF08A; border:1px solid #FDE047; padding:10px; border-radius:6px; color:#713F12; font-weight:bold; font-size:13px; text-align:center;'>🟡 [반쪽 연결 실패] 열쇠는 있으나, 구글 드라이브에서 '{SPREADSHEET_NAME}' 엑셀 파일을 찾지 못했습니다! (에러내용: {str(connect_err)})</div>", unsafe_allow_html=True)

        frame_left, frame_right = st.columns([1.4, 4.2])
        has_active = "active_subject" in st.session_state and st.session_state.active_subject
        
        with frame_left:
            g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군"]
            sel_g = st.selectbox("1단계 분류", options=g_opts, index=st.session_state.sel_group_idx)
            final_sub = ""
            if sel_g != "교과군 선택":
                s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                sel_s = st.selectbox("2단계 과목", options=s_opts, index=st.session_state.sel_sub_idx)
                if sel_s != "과목 선택": final_sub = sel_s
            else: st.selectbox("2단계 과목", ["과목 선택 대기"], disabled=True)
                
            sel_gr = st.selectbox("3단계 학년", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx)
            final_gr = sel_gr.replace("학년", "") if sel_gr != "학년 선택" else ""
            sel_se = st.selectbox("4단계 학기", options=SEMESTER_OPTIONS, index=st.session_state.sel_semester_idx)
            final_se = sel_se if sel_se != "학기 선택" else ""
            
            if st.button("🚀 과목 활성화", use_container_width=True):
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

            if has_active:
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                cf_id, sf_id = get_sheet_names_id(sub, grd, sem)
                n_current = st.session_state.get("num_items_input", 0)
                live_item_names = [st.session_state.get(f"item_name_input_{sub}_{idx+1}", f"수행{idx+1}").strip() for idx in range(n_current)]

                with st.container(border=True):
                    base_headers = ["반", "번호", "이름", "비밀번호", "확인여부", "확인시간"]
                    final_headers = base_headers + live_item_names
                    sample_row = ["1", "1", "홍길동", "1234", "미확인", ""] + ["0"] * len(live_item_names)
                    output = io.StringIO()
                    csv.writer(output).writerow(final_headers)
                    csv.writer(output).writerow(sample_row)
                    st.download_button(label="📥 예시 파일 다운로드", data=output.getvalue().encode('utf-8-sig'), file_name=f"sample_{sub}.csv", mime="text/csv")
                    
                    up_f = st.file_uploader("성적 CSV 업로드", type="csv", label_visibility="collapsed")
                    if up_f:
                        df_up = pd.read_csv(up_f, encoding='cp949')
                        if save_df_to_sheet(sf_id, df_up): st.success("🎉 성적 연동 성공!"); st.rerun()
            if st.button("🗑️ 시스템 초기화"): reset_all_data()

        with frame_right:
            if has_active:
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                cf_id, sf_id = get_sheet_names_id(sub, grd, sem)
                df_load_main = load_sheet_to_df(cf_id)
                conf = df_load_main.iloc[0].to_dict() if not df_load_main.empty else {}
                
                st.markdown(f"<div style='background-color:#eff6ff; border:1px solid #bfdbfe; padding:8px 12px; border-radius:6px; margin-bottom:12px; text-align:center; font-size:13px; font-weight:600; color:#1e40af;'>📍 작업 구역: [{sub}] {grd}학년 ({sem})</div>", unsafe_allow_html=True)

                with st.container(border=True):
                    saved_cl_str = st.session_state.get("saved_classes_list", str(conf.get('선택된반 목록', '')))
                    saved_cl = [int(x) for x in str(saved_cl_str).replace("[","").replace("]","").split(",") if str(x).strip()] if saved_cl_str else []
                    default_items_count = st.session_state.get("saved_items_count", int(conf.get('항목개수', 0)))

                    st.markdown("<div style='font-size:12px; font-weight:600;'>🏫 담당 학급(반) 지정</div>", unsafe_allow_html=True)
                    sel_cl = []
                    cols_cl = st.columns(6)
                    for i in range(1, 13):
                        with cols_cl[(i-1)%6]:
                            if st.checkbox(f"{i}반", value=i in saved_cl, key=f"chk_class_{i}"): sel_cl.append(i)

                    st.markdown("<div style='margin-top:8px; font-size:12px; font-weight:600;'>✍️ 평가 항목 설정</div>", unsafe_allow_html=True)
                    n_item = st.number_input("평가 항목 개수", min_value=0, max_value=10, value=default_items_count, key="num_items_input")
                    
                    item_names = []
                    if n_item > 0:
                        for i in range(n_item):
                            cols_i = st.columns(2) if i % 2 == 0 else cols_i
                            with cols_i[i%2]:
                                name = st.text_input(f"{i+1}번 항목명", value=conf.get(f'항목{i+1}_이름', ""), placeholder=f"예: 수행평가{i+1}", key=f"item_name_input_{sub}_{i+1}")
                            item_names.append(name.strip())

                        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                        if st.button(f"💾 [{sub}] 과목 사양 최종 저장하기", type="primary", use_container_width=True):
                            if sel_cl and all(item_names):
                                classes_string = ",".join(map(str, sorted(sel_cl)))
                                d = {"과목명": sub, "교과명": sub, "학년": grd, "학기통합명": sem, "선택된반 목록": classes_string, "항목개수": n_item}
                                for i, name_val in enumerate(item_names): d[f"항목{i+1}_이름"] = name_val
                                
                                get_google_sheet(cf_id)
                                save_df_to_sheet(cf_id, pd.DataFrame([d]))
                                get_google_sheet(sf_id)
                                save_df_to_sheet(sf_id, pd.DataFrame(columns=["반", "번호", "이름", "비밀번호", "확인여부", "확인시간"] + item_names))
                                
                                st.session_state["saved_classes_list"] = classes_string
                                st.session_state["saved_items_count"] = n_item
                                st.session_state["just_saved_success"] = True; st.toast("💾 구글 연동 완료!"); st.rerun()

                if st.session_state.get("just_saved_success", False):
                    st.markdown(f"""<div class="next-step-box"><b>✅ [{sub}] 과목 사양 설정 완료!</b><br>1️⃣ 왼쪽 하단 <b>📥 예시 파일 다운로드</b> 버튼 클릭<br>2️⃣ CSV 파일에 성적 기입<br>3️⃣ 성적 파일 업로드!</div>""", unsafe_allow_html=True)
            else:
                st.info("👈 왼쪽 제어판에서 과목 사양을 선택한 뒤 [🚀 과목 활성화]를 눌러주세요.")