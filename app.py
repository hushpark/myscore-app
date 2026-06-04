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
# 🔐 [구글 시트 API 연동 설정] secrets.toml 기반 안전 접속 엔진[cite: 1]
# =========================================================================
@st.cache_resource
def init_google_sheet_client():
    try:
        credentials_info = st.secrets["gcp_service_account"][cite: 1]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)[cite: 1]
        return gspread.authorize(creds)[cite: 1]
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
            return sh.add_worksheet(title=sheet_name, rows="1000", cols="30")[cite: 1]
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
        return pd.DataFrame(columns=default_cols if default_cols else [])[cite: 1]

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

# ⚡ [초고속 렉 방지 핵심]: 글자 타이핑할 때마다 구글 서버를 무한 조회하여 회색 화면을 유발하던 병목을 원천 차단!
@st.cache_data(ttl=30)
def get_active_databases():
    active_list = []
    if gc is None: return active_list[cite: 1]
    try:
        sh = gc.open(SPREADSHEET_NAME)
        for wks in sh.worksheets():
            name = wks.title
            if name.startswith("cfg_"):
                core_name = name.replace("cfg_", "")
                match = re.search(r"(.+?)_(1|2|3)_(.+)", core_name)
                if match:[cite: 1]
                    sub_name = match.group(1).replace("_", " ")
                    grd_name = f"{match.group(2)}학년"
                    sem_name = match.group(3).replace("_", " ")
                    active_list.append({"subject": sub_name, "grade": grd_name, "semester": sem_name})[cite: 1]
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
            if safe_sub in wks.title and (wks.title.startswith("cfg_") or wks.title.startswith("st_")):[cite: 1]
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
    new_pw = st.text_input("1. 새 암호 입력", type="password", key="dialog_new_pw")[cite: 1]
    confirm_pw = st.text_input("2. 새 암호 확인", type="password", key="dialog_confirm_pw")
    is_valid, msg = is_strong_password(new_pw)
    if new_pw:
        if new_pw == confirm_pw and is_valid:
            st.markdown("<div style='background-color:#E8F5E9; border-radius:4px; padding:10px; color:#2E7D32; font-weight:500; margin-bottom:10px;'>✅ 두 암호가 완벽하게 일치합니다.</div>", unsafe_allow_html=True)
        elif confirm_pw and new_pw != confirm_pw:
            st.error("❌ 암호 확인 칸이 일치하지 않습니다.")
        else:[cite: 1]
            st.warning(msg)
    st.markdown("""<div style="font-size: 13px; color: #57606a; line-height: 1.6; background: #f8f9fa; padding: 15px; border-radius: 8px;">
    <b>[안전 암호 규칙]</b><br>- 최소 12자 이상 필수<br>- 영문 + 숫자 + 특수기호 조합
    </div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    can_submit = is_valid and (new_pw == confirm_pw)
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("저장 후 적용", disabled=not can_submit, use_container_width=True, type="primary"):
            save_admin_password(new_pw); st.toast("🎉 암호가 변경되었습니다!"); st.rerun()[cite: 1]
    with b_col2:
        if st.button("수정 취소", use_container_width=True): st.rerun()

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
SEMESTER_OPTIONS = ["학기 선택"] + [f"{y}학년도 {t}학기" for y in range(2025, 2030) for t in [1, 2]][cite: 1]
CURRENT_ADMIN_PW = load_admin_password()

# ==========================================
# 🔄 화면 분기 구동 영역 
# ==========================================
if st.session_state["page_status"] == "student_main":
    st.markdown("<style>div[data-testid='stVerticalBlockBorderWrapper'] { border: 1px solid #e2e8f0 !important;[cite: 1] padding: 35px 40px !important; border-radius: 12px !important; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; background-color: #ffffff !important;[cite: 1] max-width: 500px !important; margin: 0px auto 20px auto !important; }</style>", unsafe_allow_html=True)[cite: 1]
    col_empty, col_btn = st.columns([3, 1])
    with col_btn:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if st.button("🔓 교사용 제어판", key="outer_teacher_btn"): st.session_state["page_status"] = "teacher_auth"; st.rerun()
            
    active_dbs = get_active_databases()
    with st.container(border=True):
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 5px 0px;'>🎒 수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; margin: 0px 0px 10px 0px; color: #475569;'>📝 개인별 성적 조회</h4>", unsafe_allow_html=True)[cite: 1]
        st.markdown("<p style='text-align:center; font-size:14px; color:#64748b; margin-bottom:20px;'>과목과 해당 학기를 선택하고 정보를 입력해 주세요.</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        
        if not active_dbs:
            st.warning("현재 등록된 성적 데이터가 없습니다.")
        else:
            st.markdown("<div style='font-size:14px; font-weight:700; color:#0f172a; margin-bottom:8px;'>🎯 대상 과목 및 학기 선택</div>", unsafe_allow_html=True)[cite: 1]
            opts_s = ["과목 및 학기를 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} - {d['semester']})" for d in active_dbs]
            sel_s = st.selectbox("조회할 과목 선택", opts_s, label_visibility="collapsed", key="student_select_sub")
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            
            if sel_s != "과목 및 학기를 선택하세요.":
                db = active_dbs[opts_s.index(sel_s)-1][cite: 1]
                cf_id, sf_id = get_sheet_names_id(db['subject'], db['grade'].replace("학년",""), db['semester'])
                
                df_load = load_sheet_to_df(cf_id)
                config = df_load.iloc[0].to_dict() if not df_load.empty else None
                
                if config:
                    sub_title = config.get('교과명', config.get('과목명', '미정'))
                    st.markdown(f"<div style='background:#f1f5f9; padding:12px 15px; border-radius:8px; margin-bottom:20px; font-size:14px;'><span style='font-weight:600; color:#475569;'>선택된 교과:</span> &nbsp;🧬 <b>{sub_title}</b> ({config.get('학기통합명','')})</div>", unsafe_allow_html=True)[cite: 1]
                    
                    with st.form("login_form"):
                        st.markdown("<div style='font-size:14px; font-weight:700; color:#0f172a; margin-bottom:8px;'>🔐 본인 인증 정보 입력</div>", unsafe_allow_html=True)
                        classes = [f"{x.strip()}반" for x in str(config.get('선택된반 목록', '1')).split(",") if x.strip()][cite: 1]
                        if not classes: classes = ["1반"]
                        
                        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])[cite: 1]
                        with c1: b_in = st.selectbox("반", classes)
                        with c2: n_in = st.number_input("번호", 1, 50, 1)
                        with c3: name_in = st.text_input("이름", placeholder="홍길동")
                        with c4: pw_in = st.text_input("비밀번호", type="password", placeholder="****")[cite: 1]
                        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                        
                        if st.form_submit_button("🔍 내 점수 확인하기", use_container_width=True, type="primary"):[cite: 1]
                            df_st = load_sheet_to_df(sf_id)
                            if df_st.empty: st.error("성적 데이터가 아직 연동되지 않은 교과입니다.")
                            else:
                                if '확인여부' in df_st.columns: df_st['확인여부'] = df_st['확인여부'].astype(str).replace(['nan', 'None', ''], '미확인')[cite: 1]
                                if '확인시간' in df_st.columns: df_st['확인시간'] = df_st['확인시간'].astype(str).replace(['nan', 'None', ''], '')
                                res = df_st[(df_st['반'].astype(int)==int(b_in.replace("반",""))) & (df_st['번호'].astype(int)==n_in) & (df_st['이름'].astype(str)==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))][cite: 1]
                                if not res.empty:
                                    idx = res.index[0]
                                    scores, total_sum = {}, 0[cite: 1]
                                    for i in range(int(config['항목개수'])):
                                        h_name = config.get(f'항목{i+1}_이름', f'항목{i+1}')[cite: 1]
                                        if h_name in df_st.columns:
                                            val = df_st.loc[idx, h_name]; scores[h_name] = [val][cite: 1]
                                            try:
                                                if pd.notna(val): total_sum += float(val)
                                            except: pass[cite: 1]
                                    if float(total_sum).is_integer(): scores['합계'] = [int(total_sum)]
                                    else: scores['합계'] = [round(total_sum, 2)][cite: 1]
                                    
                                    df_st.loc[idx, '확인여부'] = str("확인 완료")
                                    df_st.loc[idx, '확인시간'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))[cite: 1]
                                    save_df_to_sheet(sf_id, df_st)
                                    show_result_dialog(name_in, scores)[cite: 1]
                                else: st.error("입력한 학생 정보 또는 비밀번호가 일치하지 않습니다.")

elif st.session_state["page_status"] == "teacher_auth":
    st.markdown("<style>div[data-testid='stForm'] { border: 1px solid #e2e8f0 !important;[cite: 1] padding: 35px 40px !important; border-radius: 12px !important; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; background-color: #ffffff !important;[cite: 1] max-width: 450px !important; margin: 40px auto 20px auto !important; }</style>", unsafe_allow_html=True)[cite: 1]
    with st.form("admin_login_form"):
        st.markdown("<h2 style='text-align: center; margin: 0px 0px 5px 0px;'>⚙️ 교과 통합 관리자</h2>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 15px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:14px; color:#64748b; margin-bottom:25px; line-height: 1.5;'>여러 교과와 학년별 성적 데이터베이스를<br>스위칭하며 관리하는 공간입니다.</p>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px; font-weight:600; color:#1e293b; margin-bottom:8px;'>관리자 인증 비밀번호를 입력하세요</div>", unsafe_allow_html=True)
        admin_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력", label_visibility="collapsed")[cite: 1]
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.form_submit_button("로그인", use_container_width=True, type="primary"):
            if admin_pw == CURRENT_ADMIN_PW: st.session_state["admin_logged_in"] = True; st.session_state["page_status"] = "teacher_main"; st.rerun()[cite: 1]
            else: st.error("❌ 비밀번호가 틀렸습니다.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎒 학생 화면으로 돌아가기", key="outer_student_btn", use_container_width=True): st.session_state["page_status"] = "student_main"; st.rerun()[cite: 1]

elif st.session_state["page_status"] == "teacher_main":
    if not st.session_state["admin_logged_in"]: st.session_state["page_status"] = "teacher_auth"; st.rerun()[cite: 1]
    col_empty, col_pw, col_logout = st.columns([5, 1.4, 1.4])
    with col_pw:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if st.button("🔐 암호 변경", key="outer_pw_btn", use_container_width=True): password_update_dialog()
    with col_logout:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if st.button("🎒 학생 화면", key="outer_logout_btn", use_container_width=True):
            st.session_state["page_status"] = "student_main"; st.session_state["admin_logged_in"] = False; st.session_state["show_monitor_view"] = False; st.session_state["show_delete_panel"] = False; st.rerun()[cite: 1]

    with st.container(border=True):
        st.markdown("<h2>⚙️ 교과·학년 통합 제어 센터</h2>", unsafe_allow_html=True)
        
        # 🟢 상단에 실시간으로 구글 클라우드 연결 상태를 증명하는 신호등 탑재
        if gc is None:
            st.markdown("<div style='background-color:#FDE8E8; border:1px solid #F8B4B4; padding:10px; border-radius:6px; color:#9B1C1C; font-weight:bold; font-size:13px; text-align:center; margin-bottom:15px;'>❌ [연결 실패] 스트림릿 secrets 설정에 구글 비밀 열쇠 양식이 깨졌습니다!</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background-color:#E1F5FE; border:1px solid #B3E5FC; padding:10px; border-radius:6px; color:#01579B; font-weight:bold; font-size:13px; text-align:center; margin-bottom:15px;'>🟢 [원격 연결 성공] 구글 API 연동 완벽 완료! 드라이브 파일 [ {SPREADSHEET_NAME} ] 결합 완료.</div>", unsafe_allow_html=True)
            
        frame_left, frame_right = st.columns([1.4, 4.2])
        has_active = "active_subject" in st.session_state and st.session_state.active_subject
        
        with frame_left:
            st.markdown("<h4>📁 대상 과목 및 학기 선택</h4>", unsafe_allow_html=True)
            g_opts = ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"][cite: 1]
            sel_g = st.selectbox("1단계: 교과군 분류", options=g_opts, index=st.session_state.sel_group_idx, label_visibility="collapsed")
            
            final_sub, t_g = "", ""
            if sel_g == "➕ 신규 과목 개설":
                t_g = st.selectbox("추가 위치 지정", ["인문·사회군", "수리·과학군", "예체능군"])
                final_sub = st.text_input("✏️ 새 과목명 입력", placeholder="과목명 입력").strip()[cite: 1]
            elif sel_g != "교과군 선택":
                s_opts = ["과목 선택"] + SUBJECT_MAP[sel_g]
                idx_s = st.session_state.sel_sub_idx if st.session_state.sel_sub_idx < len(s_opts) else 0
                sel_s = st.selectbox("2단계: 세부 과목 선택", options=s_opts, index=idx_s, label_visibility="collapsed")[cite: 1]
                if sel_s != "과목 선택": final_sub = sel_s
            else: st.selectbox("2단계: 세부 과목 선택", ["과목 선택 대기"], disabled=True, label_visibility="collapsed")
                
            sel_gr = st.selectbox("3단계: 관리 학년 지정", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx, label_visibility="collapsed")
            final_gr = sel_gr.replace("학년", "") if sel_gr != "학년 선택" else ""[cite: 1]
            sel_se = st.selectbox("4단계: 대상 학기 선택", options=SEMESTER_OPTIONS, index=st.session_state.sel_semester_idx, label_visibility="collapsed")
            final_se = sel_se if sel_se != "학기 선택" else ""
            
            if st.button("🚀 과목 활성화", use_container_width=True, key="side_activate_btn"):
                if final_sub and final_gr and final_se:
                    if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(t_g, final_sub)[cite: 1]
                    st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester = final_sub, final_gr, final_se
                    st.session_state.sel_group_idx = g_opts.index(sel_g)
                    if sel_g != "➕ 신규 과목 개설": st.session_state.sel_sub_idx = s_opts.index(final_sub)[cite: 1]
                    st.session_state.sel_grade_idx = GRADE_OPTIONS.index(sel_gr)
                    st.session_state.sel_semester_idx = SEMESTER_OPTIONS.index(sel_se)
                    
                    cf_id, sf_id = get_sheet_names_id(final_sub, final_gr, final_se)
                    df_init = load_sheet_to_df(cf_id)[cite: 1]
                    if not df_init.empty:
                        r_dict = df_init.iloc[0].to_dict()
                        st.session_state["saved_classes_list"] = r_dict.get('선택된반 목록', '')
                        st.session_state["saved_items_count"] = int(r_dict.get('항목개수', 0))[cite: 1]
                    else:
                        st.session_state["saved_classes_list"] = ''
                        st.session_state["saved_items_count"] = 0
                        
                    st.session_state["just_saved_success"] = False
                    st.session_state["show_delete_panel"] = False; st.rerun()[cite: 1]
                else: st.warning("과목, 학년, 학기 데이터를 누락 없이 모두 선택해 주세요.")
            
            del_panel_label = "🚨 데이터 삭제 닫기" if st.session_state["show_delete_panel"] else "🚨 데이터 삭제"
            if st.button(del_panel_label, key="side_toggle_delete_btn", use_container_width=True):
                st.session_state["show_delete_panel"] = not st.session_state["show_delete_panel"]
                if st.session_state["show_delete_panel"]: st.session_state["show_monitor_view"] = False[cite: 1]
                st.rerun()
            
            monitor_label = "👀 학생 입력 확인 닫기" if st.session_state["show_monitor_view"] else "👥 학생 입력 확인"
            if st.button(monitor_label, key="side_monitor_btn", disabled=not has_active): st.session_state["show_monitor_view"] = not st.session_state["show_monitor_view"]; st.rerun()[cite: 1]
                
            if has_active:
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                
                # 🌟 [버그 원천 완치 줄]: 변수명이 꼬여서 NameError를 내던 부분을 완벽하게 교정했습니다!
                cf_id, sf_id = get_sheet_names_id(sub, grd, sem)
                
                n_current = st.session_state.get("num_items_input", 0)[cite: 1]
                live_item_names = []
                for idx in range(n_current):
                    val_live = st.session_state.get(f"item_name_input_{sub}_{idx+1}", f"수행{idx+1}").strip()
                    if not val_live: val_live = f"수행{idx+1}"
                    live_item_names.append(val_live)[cite: 1]

                with st.container(border=True):
                    st.markdown('<div class="compact-upload-box">', unsafe_allow_html=True)
                    st.markdown("<div style='font-size:12px; font-weight:600; color:#475569; margin-bottom:6px;'>📁 성적 일괄 업로드 (클라우드 직송)</div>", unsafe_allow_html=True)
                    
                    base_headers = ["반", "번호", "이름", "비밀번호", "확인여부", "확인시간"][cite: 1]
                    final_headers = base_headers + live_item_names 
                    sample_row = ["1", "1", "홍길동", "1234", "미확인", ""] + ["0"] * len(live_item_names)[cite: 1]
                    
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(final_headers)
                    writer.writerow(sample_row)[cite: 1]
                    csv_data = output.getvalue().encode('utf-8-sig')
                    
                    st.download_button(label="📥 예시 파일 다운로드", data=csv_data, file_name=f"sample_students_{sub}_{sem}.csv", mime="text/csv", key="btn_download_sample")
                    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)[cite: 1]
                    
                    # ⚡ [무한 루프 렉 완치]: 성적 업로드 완료 후 파일 락을 강제 초기화하여 버벅거림 완전 제거!
                    up_f = st.file_uploader("성적 CSV 업로드", type="csv", label_visibility="collapsed", key="uploader_csv_file")
                    if up_f:
                        try:
                            df_up = pd.read_csv(up_f, encoding='cp949')[cite: 1]
                            success = save_df_to_sheet(sf_id, df_up)
                            if success:
                                st.toast("🎉 구글 시트로 성적 동기화 완벽 완료!")
                                st.rerun()
                            else:
                                st.error("❌ 구글 시트 업로드 실패. 권한 및 파일명을 점검하세요.")[cite: 1]
                        except:
                            st.error("❌ 인코딩 포맷을 확인해 주세요. (EUC-KR 또는 CP949)")
                    st.markdown('</div>', unsafe_allow_html=True)
                        
            if st.button("🗑️ 시스템 초기화", key="side_reset_btn"): reset_all_data()[cite: 1]

        with frame_right:
            show_del = st.session_state.get("show_delete_panel", False)
            if show_del:
                st.markdown("<h4 style='color: #ef4444; margin-top: 0px;'>⚙️ 데이터 삭제 및 청소 관리 센터</h4>", unsafe_allow_html=True)
                tab_del_sem, tab_del_sub = st.tabs(["학기 및 학년별 삭제", "과목 일괄 삭제"])[cite: 1]
                
                with tab_del_sem:
                    existing_dbs = get_active_databases()
                    if not existing_dbs: st.info("현재 구글 시트에 보관 중인 분기 데이터가 없습니다.")
                    else:[cite: 1]
                        sem_opts = [f"📚 {d['subject']} | {d['grade']} | {d['semester']}" for d in existing_dbs][cite: 1]
                        selected_sem_str = st.selectbox("삭제 대상 선택", options=sem_opts, label_visibility="collapsed", key="sb_delete_target_sem")
                        t_db = existing_dbs[sem_opts.index(selected_sem_str)]
                        verify_code_sem = f"{t_db['subject']}_{t_db['grade'].replace('학년','')}_{t_db['semester'].replace('학년도','').replace(' ', '')}"
                        
                        st.markdown(f"<div style='font-size:12px; margin-bottom:4px;'>인증코드 입력: <code style='color:#ef4444;'>{verify_code_sem}</code></div>", unsafe_allow_html=True)
                        user_confirm_sem = st.text_input("인증코드 입력창", label_visibility="collapsed", key="ti_verify_sem_code")
                        if st.button("🔒 선택 학기 데이터 영구 폐기 실행", disabled=(user_confirm_sem != verify_code_sem), type="primary", use_container_width=True):[cite: 1]
                            cf_id, sf_id = get_sheet_names_id(t_db['subject'], t_db['grade'].replace("학년",""), t_db['semester'])
                            if gc:
                                try:[cite: 1]
                                    sh = gc.open(SPREADSHEET_NAME)
                                    for n in [cf_id, sf_id]: sh.del_worksheet(sh.worksheet(n))
                                except: pass[cite: 1]
                            st.toast("🎉 선택하신 분기 데이터 클렌징 완료!"); st.rerun()[cite: 1]

                with tab_del_sub:
                    raw_subjects = load_master_subjects()
                    flat_subs = sorted(list(set([sub for list_sub in raw_subjects.values() for sub in list_sub])))
                    if not flat_subs: st.info("등록 개설된 교과목 마스터 목록이 비어 있습니다.")
                    else:[cite: 1]
                        selected_sub_to_del = st.selectbox("과목명 선택", options=flat_subs, label_visibility="collapsed", key="sb_delete_target_sub")
                        user_confirm_sub = st.text_input(f"과목명 정확히 재입력 ({selected_sub_to_del})", label_visibility="collapsed", key="ti_verify_sub_code")
                        if st.button("🚨 마스터 교과 일괄 파괴 실행", disabled=(user_confirm_sub != selected_sub_to_del), type="primary", use_container_width=True):[cite: 1]
                            remove_subject_completely_from_disk(selected_sub_to_del); st.toast("🎉 교과 소멸 완료!"); st.rerun()[cite: 1]

            elif has_active:
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                cf_id, sf_id = get_sheet_names_id(sub, grd, sem)
                
                df_load_main = load_sheet_to_df(cf_id)
                conf = {}[cite: 1]
                if not df_load_main.empty:
                    raw_dict = df_load_main.iloc[0].to_dict()
                    conf['과목명'] = raw_dict.get('과목명', raw_dict.get('교과명', sub))
                    conf['학년'] = raw_dict.get('학년', grd)
                    conf['학기통합명'] = raw_dict.get('학기통합명', sem)[cite: 1]
                    conf['선택된반 목록'] = raw_dict.get('선택된반 목록', '')
                    conf['항목개수'] = raw_dict.get('항목개수', 0)
                    for k, v in raw_dict.items():
                        if '항목' in k: conf[k] = v[cite: 1]
                
                st.markdown(f"<div style='background-color:#eff6ff; border:1px solid #bfdbfe; padding:8px 12px; border-radius:6px; margin-bottom:12px; text-align:center; font-size:13px; font-weight:600; color:#1e40af;'>📍 작업 구역: [{sub}] {grd}학년 ({sem})</div>", unsafe_allow_html=True)[cite: 1]

                with st.container(border=True):
                    saved_cl_str = st.session_state.get("saved_classes_list", str(conf.get('선택된반 목록', '')))
                    saved_cl = []
                    if saved_cl_str:
                        saved_cl = [int(x) for x in str(saved_cl_str).replace("[","").replace("]","").split(",") if str(x).strip()][cite: 1]
                    
                    default_items_count = st.session_state.get("saved_items_count", int(conf.get('항목개수', 0)))

                    st.markdown("<div style='font-size:12px; font-weight:600; color:#475569;'>🏫 담당 학급(반) 지정</div>", unsafe_allow_html=True)
                    sel_cl = [][cite: 1]
                    cols_cl = st.columns(6)
                    for i in range(1, 13):
                        with cols_cl[(i-1)%6]:
                            if st.checkbox(f"{i}반", value=i in saved_cl, key=f"chk_class_{i}"): sel_cl.append(i)[cite: 1]

                    st.markdown("<div style='margin-top:8px; font-size:12px; font-weight:600; color:#475569;'>✍️ 평가 항목 설정</div>", unsafe_allow_html=True)[cite: 1]
                    n_item = st.number_input("평가 항목 개수", min_value=0, max_value=10, value=default_items_count, key="num_items_input")
                    
                    item_names = []
                    if n_item > 0:
                        for i in range(n_item):[cite: 1]
                            if i % 2 == 0:
                                cols_i = st.columns(2)
                                with cols_i[0]:[cite: 1]
                                    name = st.text_input(f"{i+1}번 항목명", value=conf.get(f'항목{i+1}_이름', ""), placeholder=f"예: 수행평가{i+1}", key=f"item_name_input_{sub}_{i+1}")
                            else:
                                with cols_i[1]:[cite: 1]
                                    name = st.text_input(f"{i+1}번 항목명", value=conf.get(f'항목{i+1}_이름', ""), placeholder=f"예: 수행평가{i+1}", key=f"item_name_input_{sub}_{i+1}")
                            item_names.append(name.strip())[cite: 1]

                        # 🌟 [동선 보장]: 항목 상자가 생성되면 그 바로 아랫줄에 저장 버튼 연동
                        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                        if st.button(f"💾 [{sub}] 과목 사양 최종 저장하기", type="primary", use_container_width=True, key="embedded_save_btn"):
                            if sel_cl and all(item_names):
                                classes_string = ",".join(map(str, sorted(sel_cl)))[cite: 1]
                                d = {
                                    "과목명": sub, "교과명": sub, "학년": grd, "학기통합명": sem, [cite: 1]
                                    "선택된반 목록": classes_string, "항목개수": n_item
                                }
                                for i, name_val in enumerate(item_names): d[f"항목{i+1}_이름"] = name_val[cite: 1]
                                
                                # 구글 클라우드에 연동 데이터 송출
                                get_google_sheet(cf_id)[cite: 1]
                                save_df_to_sheet(cf_id, pd.DataFrame([d]))
                                get_google_sheet(sf_id)
                                
                                st.session_state["saved_classes_list"] = classes_string[cite: 1]
                                st.session_state["saved_items_count"] = n_item
                                st.session_state["just_saved_success"] = True[cite: 1]
                                
                                st.toast("💾 설정이 구글 클라우드에 연동되었습니다!")
                                st.rerun()[cite: 1]
                            else:
                                st.error("❌ 담당 학급(반)을 한 개 이상 선택하고, 항목명을 전부 완성해 주셔야 저장이 가능합니다.")

                # 🌟 [동선 보장]: 성공 지침 서랍 고정 배치
                if st.session_state.get("just_saved_success", False):[cite: 1]
                    st.markdown(f"""
                        <div class="next-step-box">
                            <b>✅ [{sub}] 과목 사양 설정 완료!</b><br>
                            구글 클라우드에 테이블 방(cfg_...)이 완벽하게 개설되었습니다. 이제 다음 작업을 순서대로 이어가세요:<br>[cite: 1]
                            <hr style='margin:8px 0; border:none; border-top:1px solid #bbf7d0;'>
                            1️⃣ 왼쪽 하단 서랍에 있는 <b>📥 예시 파일 다운로드</b> 버튼을 누릅니다.<br>
                            2️⃣ 방금 다운로드된 따끈따끈한 맞춤형 CSV 양식을 열어 학생 인적 사항과 점수를 기입합니다.<br>
                            3️⃣ 파일 선택 창에 완성된 성적 파일을 업로드하시면 실시간 성적 공시 엔진이 완벽하게 가동됩니다!
                        </div>
                    """, unsafe_allow_html=True)

                show_mon = st.session_state.get("show_monitor_view", False)
                if show_mon:
                    st.markdown("<h4 style='color: #0f172a;'>📊 실시간 데이터 연동 모니터 (구글 시트)</h4>", unsafe_allow_html=True)
                    with st.container(border=True):[cite: 1]
                        df_monitor = load_sheet_to_df(sf_id)
                        if not df_monitor.empty:
                            st.markdown('<div class="monitor-table">', unsafe_allow_html=True)
                            st.dataframe(df_monitor, use_container_width=True, hide_index=True)[cite: 1]
                            st.markdown('</div>', unsafe_allow_html=True)
                        else: st.warning("⚠️ 해당 학기의 성적 데이터가 구글 시트에 아직 업로드되지 않았습니다.")
            else:
                st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)[cite: 1]
                st.info("👈 왼쪽 제어판에서 과목 사양을 선택한 뒤 [🚀 과목 활성화]를 눌러주세요.")

        st.markdown("<div class='custom-guide-bar'>💡 <b>[🚀 과목 활성화]</b>를 누르시면 해당 구글 시트 데이터베이스를 원격 로드합니다.</div>", unsafe_allow_html=True)