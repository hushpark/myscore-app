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

        /* 모든 메뉴 버튼 간의 세로 유격을 완전히 당겨서 초밀착 정렬 */
        div[data-testid="stVerticalBlock"] > div:has(div.stButton) {
            margin-bottom: -12px !important; 
            padding-bottom: 0px !important;
        }
        
        /* 데이터 삭제 메인 버튼 - 빨간색 글자 + 빨간색 밑줄 처리 */
        div:has(> button[key='side_toggle_delete_btn']) p, 
        div:has(> button[key='side_toggle_delete_btn']) span {
            color: #ef4444 !important;
            text-decoration: underline !important;
            text-decoration-color: #ef4444 !important;
            text-underline-offset: 5px !important;
            font-weight: 700 !important;
        }

        /* 데이터 삭제 내부 '탭(Tab)' 디자인 - 선택 시 강렬한 빨간색 강조 및 밑줄 지정 */
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
@st.dialog("🎉 수행평가 조회 결과")
def show_result_dialog(student_name, scores_dict):
    st.markdown(f"<h5>🎯 <b>{student_name}</b> 학생의 수행평가 점수 내역입니다.</h5>", unsafe_allow_html=True)
    st.table(pd.DataFrame(scores_dict))
    if st.button("확인 후 닫기", use_container_width=True, type="primary"): 
        st.session_state.clear()
        st.rerun()

@st.dialog("🔐 관리자 암호 수정")
def password_update_dialog():
    new_pw = st.text_input("1. 새 암호 입력", type="password")
    confirm_pw = st.text_input("2. 새 암호 확인", type="password")
    is_valid, msg = is_strong_password(new_pw)
    if new_pw and new_pw == confirm_pw and is_valid: st.success("✅ 암호 조건 일치")
    if st.button("저장 후 적용", disabled=not (is_valid and new_pw == confirm_pw), type="primary", use_container_width=True):
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
                        with c4: pw_in = st.text_input("비밀번호", type="password")
                        if st.form_submit_button("🔍 내 점수 확인하기", use_container_width=True, type="primary"):
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
                            else: st.error("❌ 정보가 올바르지 않습니다.")

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
            sel_g = st.selectbox("교과군", ["교과군 선택", "인문·사회군", "수리·과학군", "예체능군", "➕ 신규 과목 개설"], label_visibility="collapsed")
            final_sub = ""
            if sel_g == "➕ 신규 과목 개설": final_sub = st.text_input("새 과목명 입력")
            elif sel_g != "교과군 선택":
                sel_s = st.selectbox("과목", ["과목 선택"] + SUBJECT_MAP[sel_g], label_visibility="collapsed")
                if sel_s != "과목 선택": final_sub = sel_s
            sel_gr = st.selectbox("학년", GRADE_OPTIONS, label_visibility="collapsed")
            sel_se = st.selectbox("학기", SEMESTER_OPTIONS, label_visibility="collapsed")

            if st.button("🚀 과목 활성화", use_container_width=True, type="primary", key="side_activate_btn"):
                if final_sub and sel_gr != "학년 선택" and sel_se != "학기 선택":
                    if sel_g == "➕ 신규 과목 개설": save_new_subject_to_master(sel_g, final_sub)
                    st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester = final_sub, sel_gr.replace("학년",""), sel_se
                    st.rerun()
                else: st.warning("모든 항목을 선택하세요.")

            del_label = "🚨 데이터 삭제 닫기" if st.session_state["show_delete_panel"] else "🚨 데이터 삭제"
            if st.button(del_label, key="side_toggle_delete_btn", use_container_width=True):
                st.session_state["show_delete_panel"] = not st.session_state["show_delete_panel"]
                st.session_state["show_monitor_view"] = False; st.rerun()

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            if st.button(f"💾 설정 저장", disabled=not has_active, use_container_width=True, key="side_save_btn"):
                st.session_state["trigger_save"] = True
            if st.button("👥 학생 입력 확인", disabled=not has_active, use_container_width=True, key="side_monitor_btn"):
                st.session_state["show_monitor_view"] = not st.session_state["show_monitor_view"]; st.rerun()
            if st.button("➕ 과목 추가", use_container_width=True): 
                st.session_state.active_subject = None; st.rerun()
            if st.button("🗑️ 시스템 초기화", use_container_width=True): reset_all_data()

        with frame_right:
            if st.session_state["show_delete_panel"]:
                st.markdown("<h4 style='color: #ef4444;'>⚙️ 데이터 삭제 및 청소 관리 센터</h4>", unsafe_allow_html=True)
                tab_sem, tab_sub = st.tabs(["학기 및 학년별 삭제", "과목 일괄 삭제"])
                with tab_sem:
                    existing = get_active_databases()
                    if not existing: st.info("현재 누적 보관 중인 분기 데이터베이스가 없습니다.")
                    else:
                        target = st.selectbox("폐기 대상 지정", [f"📚 {d['subject']} | {d['grade']} | {d['semester']}" for d in existing])
                        verify = target.split("|")[0].replace("📚 ","").strip()
                        user_code = st.text_input(f"인증코드: {verify}")
                        if st.button("🔥 폐기 실행", disabled=user_code != verify, type="primary", use_container_width=True):
                            cf, sf = get_file_names(verify, target.split("|")[1].replace("학년","").strip(), target.split("|")[2].strip())
                            if os.path.exists(cf): os.remove(cf)
                            if os.path.exists(sf): os.remove(sf)
                            st.success("선택하신 분기 학기 데이터 클렌징 완료!"); st.rerun()
                with tab_sub:
                    raw = load_master_subjects()
                    flat = sorted(list(set([s for l in raw.values() for s in l])))
                    target_sub = st.selectbox("완전 말소할 과목 선택", flat)
                    user_sub = st.text_input(f"과목명 정확히 재입력: {target_sub}")
                    if st.button("🚨 마스터 교과 및 하위 데이터 연쇄 일괄 파괴 실행", disabled=user_sub != target_sub, type="primary", use_container_width=True):
                        remove_subject_completely_from_disk(target_sub); st.rerun()

            elif has_active:
                sub, grd, sem = st.session_state.active_subject, st.session_state.active_grade, st.session_state.active_semester
                cf, sf = get_file_names(sub, grd, sem)
                conf = load_config(cf)
                
                # 🎒 [복구 1]: 상단 현재 작업 구역 안내창 복구
                st.markdown(f"<div style='background-color:#eff6ff; padding:10px; border-radius:6px; font-weight:600; color:#1e40af; text-align:center; margin-bottom:12px;'>📍 작업 구역: [{sub}] {grd}학년 ({sem})</div>", unsafe_allow_html=True)
                st.markdown("<h4>📌 학기 및 평가 세팅</h4>", unsafe_allow_html=True)
                
                # 🎒 [복구 2, 3]: 반 선택 체크박스 및 평가 항목 이름 기입 구조 복구
                with st.container(border=True):
                    st.markdown("<div style='font-size:12px; font-weight:600; color:#475569;'>🏫 담당 학급(반) 지정</div>", unsafe_allow_html=True)
                    sel_cl = []
                    saved_cl = [int(x) for x in str(conf.get('선택된반 목록','')).split(",") if x.strip()] if conf else []
                    cols = st.columns(6)
                    for i in range(1, 13):
                        with cols[(i-1)%6]:
                            if st.checkbox(f"{i}반", value=i in saved_cl, key=f"cl_{i}"): sel_cl.append(i)
                            
                    st.markdown("<div style='margin-top:8px; font-size:12px; font-weight:600; color:#475569;'>✍️ 평가 항목 설정</div>", unsafe_allow_html=True)
                    n_item = st.number_input("평가 항목 개수 지정", 1, 10, int(conf.get('항목개수', 1)) if conf else 1)
                    item_names = []
                    cols_i = st.columns(2)
                    for i in range(n_item):
                        with cols_i[i%2]:
                            item_names.append(st.text_input(f"{i+1}번 항목명 입력", value=conf.get(f'항목{i+1}_이름','') if conf else ""))

                # 🎒 [복구 4]: 성적 CSV 일괄 업로드 및 샘플 다운로드 구역 완전 복구
                with st.container(border=True):
                    st.markdown("<div style='font-size:12px; font-weight:600; color:#475569;'>📁 성적 일괄 업로드 관리</div>", unsafe_allow_html=True)
                    sample_columns = ["반", "번호", "이름", "비밀번호", "확인여부", "확인시간"] + [name for name in item_names if name]
                    sample_df = pd.DataFrame([[1, 1, "홍길동", "1234", "미확인", ""] + [0]*len([name for name in item_names if name])], columns=sample_columns)
                    csv_buffer = io.StringIO()
                    sample_df.to_csv(csv_buffer, index=False, encoding='cp949')
                    
                    st.download_button(
                        label="📥 성적 연동 예시 파일 다운로드",
                        data=csv_buffer.getvalue().encode('cp949'),
                        file_name=f"sample_{sub}_{grd}grade_{sem}.csv",
                        mime="text/csv"
                    )
                    
                    up_f = st.file_uploader("성적 성적 결과 CSV 데이터 업로드", type="csv", label_visibility="collapsed")
                    if up_f:
                        try:
                            df_up = pd.read_csv(up_f, encoding='cp949')
                            df_up.to_csv(sf, index=False)
                            st.success("🎉 파일 연동 및 성적 베이스 연동 완료!")
                            st.rerun()
                        except: st.error("❌ 파일 인코딩 형식을 확인하세요. (CSV 형식 권장)")

                if st.session_state.get("trigger_save"):
                    st.session_state["trigger_save"] = False
                    if sel_cl and all(item_names):
                        d = {"교과명":sub, "학년":grd, "학기통합명":sem, "선택된반 목록":",".join(map(str, sorted(sel_cl))), "항목개수":n_item}
                        for i, name in enumerate(item_names): d[f"항목{i+1}_이름"] = name
                        pd.DataFrame([d]).to_csv(cf, index=False); st.success("🎉 학기별 세팅 저장 완료!"); st.rerun()
                    else: st.error("❌ 반 선택 및 평가 항목 명칭을 채워주세요.")

                if st.session_state["show_monitor_view"]:
                    st.markdown("<h4>📊 실시간 데이터 연동 모니터</h4>", unsafe_allow_html=True)
                    df_m = load_students(sf)
                    if not df_m.empty: 
                        st.markdown('<div class="monitor-table">', unsafe_allow_html=True)
                        st.dataframe(df_m, use_container_width=True, hide_index=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    else: st.info("⚠️ 해당 학기의 성적 CSV 파일이 아직 업로드되지 않았습니다.")
            else:
                st.info("👈 왼쪽 제어판에서 과목 사양을 선택한 뒤 [🚀 과목 활성화] 또는 [🛠️ 데이터 삭제]를 클릭해 주세요.")
                st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

        # 🎒 [복구 5]: 최하단 파란색 가이드 바 복구
        st.markdown("<div class='custom-guide-bar'>💡 <b>[🚀 과목 활성화]</b>를 누르시면 해당 과목의 <b style='color:#ef4444; font-size:15px; background-color:#ffe4e6; padding:3px 6px; border-radius:4px;'>[만들기 및 불러오기]</b>가 됩니다.</div>", unsafe_allow_html=True)