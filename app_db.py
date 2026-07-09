import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import time
import io
from supabase import create_client, Client

# 🚨 와이드 레이아웃 고정 설정
st.set_page_config(page_title="수행평가 점수 확인 시스템", layout="wide")

# =========================================================================
# 🎨 UI/UX 디자인 관통 스타일 시트 (버튼 위치 및 스크롤 고정 최적화)
# =========================================================================
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"], .main {
            overflow: hidden !important;
            height: 100vh !important;
        }
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        .stSidebar, section[data-testid="stSidebar"] { min-width: 280px !important; max-width: 280px !important; background-color: #1e293b !important; }
        [data-testid="stSidebar"] .stRadio label p, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[role="radiogroup"] * { color: #ffffff !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 15px !important; font-weight: 700 !important; line-height: 2.2 !important; }
        .sidebar-title { font-size: 22px !important; font-weight: 800 !important; color: #ffffff; display: block; margin-bottom: 5px; }
        .user-info { color: #38bdf8 !important; font-size: 14px !important; font-weight: 600; margin-bottom: 25px; }
        
        /* 상단 타이틀 컴팩트 구조 */
        .header-title-main { font-size: 28px !important; font-weight: 800 !important; color: #1e293b !important; margin-bottom: 2px; }
        .header-nav-sub { font-size: 14px !important; font-weight: 600 !important; color: #475569 !important; margin-bottom: 15px; }
        .menu-title-container { border-bottom: 2px solid #cbd5e1 !important; padding-bottom: 8px; margin-bottom: 15px; }
        .menu-title-text { font-size: 20px !important; font-weight: 800 !important; color: #0f172a !important; margin: 0 !important; }

        /* 가이드라인 박스 스타일링 */
        .guide-box { background-color: #f8fafc !important; border-left: 4px solid #3b82f6 !important; padding: 12px 16px !important; border-radius: 4px; margin-bottom: 15px; font-size: 14px; color: #334155; font-weight: 600; line-height: 1.5; }
        
        /* 버튼 규격 표준화 */
        div.stButton > button[kind="primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 700 !important; border-radius: 6px !important; border: none !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #2563eb !important; }
        div.stButton > button[kind="secondary"] { background-color: #ffffff !important; color: #0f172a !important; font-weight: 700 !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
        
        /* 로그인 화면 */
        div[data-testid="stForm"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; padding: 40px !important; border-radius: 16px !important; max-width: 420px !important; margin: 80px auto 0 auto !important; box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important; }
        div[data-testid="stForm"] h2 { font-size: 24px !important; text-align: center !important; font-weight: 800 !important; }
        div[data-testid="stAlert"] * { font-size: 14px !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 🔑 Supabase 클라우드 연동 정보
# =========================================================================
SUPABASE_URL = "https://jwkvojfmhorndnnhscwl.supabase.co"
SUPABASE_KEY = "sb_publishable_6--SHGogHaHSEVO7g3rNjQ_FOHO-XlN"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

student_table = "student_scores" 
teacher_table = "teacher_accounts"
config_table = "subject_configs"

SUBJECT_MAP = {
    "인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"], 
    "수리·과학군": ["수학", "과학", "기술·가정", "정보"], 
    "예체능군": ["음악", "미술", "체육"]
}

def load_db_df(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

def get_active_databases():
    cfg_df = load_db_df(config_table)
    active_list = []
    if not cfg_df.empty and "subject_key" in cfg_df.columns:
        for _, row in cfg_df.iterrows():
            subj_key = str(row["subject_key"])
            parts = subj_key.split("_")
            if len(parts) >= 3:
                subj = parts[0]
                grade = parts[1]
                sem = "_".join(parts[2:])
                active_list.append({"subject": subj, "grade": grade, "semester": sem.replace("_", " "), "key": subj_key})
    return active_list

def get_subject_item_names(subject_key):
    cfg_df = load_db_df(config_table)
    if not cfg_df.empty and "subject_key" in cfg_df.columns:
        match = cfg_df[cfg_df["subject_key"] == subject_key]
        if not match.empty:
            row = match.iloc[0]
            count = int(row.get("item_count", 3))
            titles = [
                row.get("item1_name", "수행평가1"), 
                row.get("item2_name", "수행평가2"), 
                row.get("item3_name", "수행평가3"),
                row.get("item4_name", "수행평가4"),
                row.get("item5_name", "수행평가5")
            ]
            return count, titles
    return 3, ["수행평가1", "수행평가2", "수행평가3", "수행평가4", "수행평가5"]

# =========================================================================
# ➕ 다이얼로그 기능 모듈
# =========================================================================
@st.dialog("➕ 담당 교사 개별 추가")
def show_add_teacher_dialog():
    st.markdown("새로 등록할 선생님의 권한 정보를 입력해 주세요.")
    with st.form("add_teacher_form", border=False):
        t_id = st.text_input("교사 전용 ID")
        t_name = st.text_input("교사 성명")
        t_pw = st.text_input("초기 임시 비밀번호")
        t_subs = st.text_input("담당 과목 지정 (쉼표 분리)", placeholder="예: 정보, 수학")
        submit_btn = st.form_submit_button("💾 이 교사 계정 활성화하기", use_container_width=True)
        if submit_btn:
            if not t_id or not t_name or not t_pw or not t_subs: st.error("❌ 모든 항목을 입력해야 합니다.")
            else:
                try:
                    supabase.table(teacher_table).upsert({"교사_ID": t_id.strip(), "교사_성명": t_name.strip(), "비밀번호": t_pw.strip(), "담당_과목": t_subs.strip()}).execute()
                    st.success("🎉 교사 계정이 활성화되었습니다!")
                    time.sleep(0.3); st.rerun()
                except: st.error("❌ 등록 실패")

@st.dialog("➕ 학생 개별 추가")
def show_add_student_dialog(subject_key):
    st.markdown("명단에 추가할 학생의 기본 정보를 입력해 주세요.")
    with st.form("add_student_form", border=False):
        c1, c2, c3 = st.columns(3)
        with c1: new_ban = st.text_input("반")
        with c2: new_num = st.text_input("번호")
        with c3: new_name = st.text_input("이름")
        c4, c5 = st.columns(2)
        with c4: new_email = st.text_input("학교 이메일")
        with c5: new_pw = st.text_input("초기 비밀번호", value="1234")
        submit_btn = st.form_submit_button("💾 학생 명단에 추가하기", use_container_width=True)
        if submit_btn:
            if not new_ban.strip() or not new_num.strip() or not new_name.strip(): st.error("❌ 필수 항목을 채워주세요.")
            else:
                try:
                    supabase.table(student_table).upsert({
                        "subject_key": subject_key, "반": int(new_ban.strip()), "번호": int(new_num.strip()), "이름": new_name.strip(),
                        "학교 이메일": new_email.strip(), "비밀번호": new_pw.strip(),
                        "수행평가1": 0, "수행평가2": 0, "수행평가3": 0, "수행평가4": 0, "수행평가5": 0, "성적조회 횟수": 0, "최종 확인일시": "-"
                    }).execute()
                    st.rerun()
                except Exception as e: st.error(f"❌ 오류 발생: {e}")

@st.dialog("🎉 나의 성적 검증 결과")
def show_result_dialog(student_data, item_count, item_titles):
    st.markdown(f"<div><b>{student_data['이름']}</b> 학생의 실시간 점수 내역입니다.</div><br>", unsafe_allow_html=True)
    cols = st.columns(item_count + 1)
    
    total_score = 0
    for i in range(item_count):
        val = int(student_data.get(f"수행평가{i+1}", 0))
        total_score += val
        cols[i].metric(item_titles[i], f"{val} 점")
        
    # 💡 학생용 팝업창에도 실시간 자동합계 메트릭 출력
    cols[item_count].metric("💯 실시간 합계", f"{total_score} 점")
    
    if "has_counted" not in st.session_state:
        new_count = int(student_data.get("성적조회 횟수", 0)) + 1
        supabase.table(student_table).update({
            "성적조회 횟수": new_count, "최종 확인일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).eq("subject_key", student_data["subject_key"]).eq("반", int(student_data["반"])).eq("번호", int(student_data["번호"])).execute()
        st.session_state["has_counted"] = True
    
    if st.button("확인 완료", type="primary", use_container_width=True):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.rerun()

# 세션 상태 관리 초기화
for k, v in [("admin_logged_in", False), ("student_logged_in", False), ("logged_student_id", ""), ("logged_student_pw", ""), ("logged_teacher_id", ""), ("logged_teacher_pw", ""), ("teacher_name", ""), ("allowed_subjects", [])]:
    if k not in st.session_state: st.session_state[k] = v

# =========================================================================
# 🔓 [1단계] 통합 로그인 인증 체계
# =========================================================================
if not st.session_state["admin_logged_in"] and not st.session_state["student_logged_in"]:
    with st.form("unified_login_form"):
        st.markdown("<h2 style='text-align:center; color:#1e293b;'>수행평가 점수 검증 시스템</h2>", unsafe_allow_html=True)
        login_mode = st.radio("접속 권한", ["학생", "교사"], horizontal=True, label_visibility="collapsed")
        u_id = st.text_input("ID / 이메일", placeholder="계정을 입력하세요", label_visibility="collapsed")
        u_pw = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed")
        if st.form_submit_button("로그인 계정 인증", use_container_width=True):
            cid, cpw = u_id.strip(), u_pw.strip()
            if login_mode == "학생":
                res = supabase.table(student_table).select("*").eq("학교 이메일", cid).eq("비밀번호", cpw).execute()
                if res.data:
                    st.session_state["student_logged_in"] = True
                    st.session_state["logged_student_id"], st.session_state["logged_student_pw"] = cid, cpw
                    st.rerun()
                else: st.error("❌ 정보가 올바르지 않습니다.")
            else:
                if cid == "admin" and cpw == "1234":
                    st.session_state["admin_logged_in"] = True
                    st.session_state["logged_teacher_id"], st.session_state["logged_teacher_pw"] = "admin", "1234"
                    st.session_state["teacher_name"], st.session_state["allowed_subjects"] = "최고관리자", ["마스터"]
                    st.session_state["current_menu"] = "학생 조회 현황 모니터링"; st.rerun()
                else:
                    df_tc = load_db_df(teacher_table)
                    match = df_tc[(df_tc['교사_ID'] == cid) & (df_tc['비밀번호'] == cpw)]
                    if not match.empty:
                        row = match.iloc[0]
                        st.session_state["admin_logged_in"] = True
                        st.session_state["logged_teacher_id"], st.session_state["logged_teacher_pw"] = cid, cpw
                        st.session_state["teacher_name"] = str(row['교사_성명']).strip()
                        st.session_state["allowed_subjects"] = [s.strip() for s in str(row['담당_과목']).split(",") if s.strip()]
                        st.session_state["current_menu"] = "학생 조회 현황 모니터링"; st.rerun()
                    else: st.error("❌ 교사 인증 실패")

# =========================================================================
# 🎓 [2단계-A] 학생 점수 조회 모드
# =========================================================================
elif st.session_state["student_logged_in"]:
    st.markdown("<h2>수행평가 성적 확인 (학생 화면)</h2>", unsafe_allow_html=True)
    if st.button("🚪 안전 로그아웃", type="secondary"): st.session_state.clear(); st.rerun()
    
    active_dbs = get_active_databases()
    if not active_dbs: st.warning("현재 개설된 수행평가 교과과정이 존재하지 않습니다.")
    else:
        opts = ["과목을 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in active_dbs]
        sel_s = st.selectbox("평가 점수를 조회할 대상 교과 선택", opts)
        if sel_s != "과목을 선택하세요.":
            if st.button("🚀 실시간 내 수행평가 점수 확인하기", type="primary", use_container_width=True):
                db_info = active_dbs[opts.index(sel_s)-1]
                res = supabase.table(student_table).select("*").eq("subject_key", db_info['key']).eq("학교 이메일", st.session_state["logged_student_id"]).execute()
                if res.data:
                    cnt, titles = get_subject_item_names(db_info['key'])
                    show_result_dialog(res.data[0], cnt, titles)
                else: st.error("❌ 해당 교과에 등록된 학생 성적 데이터가 없습니다.")

# =========================================================================
# 🔒 [2단계-B] 교사용 통합 관제 모드
# =========================================================================
elif st.session_state["admin_logged_in"]:
    menus = ["학생 조회 현황 모니터링", "수행 평가 성적 입력", "학생 정보 관리", "평가 대상 과목 구성"]
    if st.session_state["logged_teacher_id"] == "admin": menus.append("👑 교사 계정 관리 대장")
    if "current_menu" not in st.session_state: st.session_state["current_menu"] = menus[0]

    with st.sidebar:
        st.markdown('<span class="sidebar-title">📋 교사진 메뉴</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="user-info">👤 {st.session_state["teacher_name"]} 선생님 담당</div>', unsafe_allow_html=True)
        sel_menu = st.radio("메뉴이동", menus, index=menus.index(st.session_state["current_menu"]), label_visibility="collapsed")
        if sel_menu != st.session_state["current_menu"]:
            st.session_state["current_menu"] = sel_menu; st.rerun()
        if st.button("🚪 로그아웃", use_container_width=True): st.session_state.clear(); st.rerun()

    st.markdown(f'<div class="header-title-main">수행평가 점수 확인 시스템</div><div class="header-nav-sub">교사 세션 > {st.session_state["current_menu"]}</div>', unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 1. 학생 조회 현황 모니터링 (💡 자동 합계 실시간 계산 계산대 주입)
    # ---------------------------------------------------------------------
    if st.session_state["current_menu"] == "학생 조회 현황 모니터링":
        with st.container(border=True):
            st.markdown('<div class="menu-title-container"><h4 class="menu-title-text">📊 학생별 조회 이력 및 수행 합계 모니터링</h4></div>', unsafe_allow_html=True)
            rdbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]:
                rdbs = [d for d in rdbs if d['subject'].strip() in st.session_state["allowed_subjects"]]
            
            if not rdbs: st.info("📢 할당되었거나 활성화된 교과 세팅이 없습니다.")
            else:
                l_col, r_col = st.columns([3, 7])
                with l_col:
                    s_opts = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in rdbs]
                    sel_db = rdbs[s_opts.index(st.selectbox("📂 대상 교과 선택", s_opts))]
                    df = pd.DataFrame(supabase.table(student_table).select("*").eq("subject_key", sel_db['key']).execute().data)
                    if not df.empty: df = df.sort_values(by=["반", "번호"]).reset_index(drop=True)
                    
                    c_opts = ["전체 학급 보기"] + [f"{x}반" for x in sorted(df['반'].unique())] if not df.empty else ["전체 학급 보기"]
                    sel_c = st.selectbox("🎯 학급 필터링", c_opts)
                
                with r_col:
                    if df.empty: st.info("📢 등록된 학생 명단이 없습니다.")
                    else:
                        v_df = df.copy()
                        if sel_c != "전체 학급 보기": v_df = v_df[v_df['반'].astype(int) == int(sel_c.replace("반",""))]
                        cnt, titles = get_subject_item_names(sel_db['key'])
                        
                        disp_cols = ["반", "번호", "이름"]
                        ren_map = {}
                        align = {"반": st.column_config.TextColumn(alignment="center"), "번호": st.column_config.TextColumn(alignment="center"), "이름": st.column_config.TextColumn(alignment="center")}
                        
                        # 💡 DB를 건드리지 않고, 가져온 각 행의 점수를 실시간 가산하여 자동합계 계산 열 주입
                        v_df["합계"] = 0
                        for i in range(cnt):
                            db_col = f"수행평가{i+1}"
                            if db_col in v_df.columns:
                                v_df[db_col] = v_df[db_col].fillna(0).astype(int)
                                v_df["합계"] += v_df[db_col]
                                disp_cols.append(db_col)
                                ren_map[db_col] = titles[i]
                                align[titles[i]] = st.column_config.NumberColumn(alignment="center")
                        
                        # 합계 열을 수행평가 항목 뒤쪽에 이쁘게 배치
                        disp_cols.append("합계")
                        align["합계"] = st.column_config.NumberColumn(alignment="center", format="%d 점")
                        
                        disp_cols += ["성적조회 횟수", "최종 확인일시"]
                        align["성적조회 횟수"] = st.column_config.NumberColumn(alignment="center")
                        align["최종 확인일시"] = st.column_config.TextColumn(alignment="center")
                        
                        st.dataframe(v_df[disp_cols].rename(columns=ren_map), use_container_width=True, hide_index=True, column_config=align, height=480)

    # ---------------------------------------------------------------------
    # 2. 수행 평가 성적 입력 (💡 요구사항 1~2번 완벽 반영 구조)
    # ---------------------------------------------------------------------
    elif st.session_state["current_menu"] == "수행 평가 성적 입력":
        with st.container(border=True):
            st.markdown('<div class="menu-title-container"><h4 class="menu-title-text">📝 수행 평가 성적 입력</h4></div>', unsafe_allow_html=True)
            rdbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]:
                rdbs = [d for d in rdbs if d['subject'].strip() in st.session_state["allowed_subjects"]]

            if not rdbs: st.info("📢 활성화된 교과가 없습니다.")
            else:
                l_col, r_col = st.columns([3, 7])
                with l_col:
                    s_opts = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in rdbs]
                    sel_db = rdbs[s_opts.index(st.selectbox("📂 대장 교과 선택", s_opts, key="ent_s"))]
                    cnt, titles = get_subject_item_names(sel_db['key'])
                    
                    df_base = pd.DataFrame(supabase.table(student_table).select("*").eq("subject_key", sel_db['key']).execute().data)
                    if not df_base.empty: df_base = df_base.sort_values(by=["반", "번호"]).reset_index(drop=True)
                    
                    c_opts = ["전체 학급 보기"] + [f"{x}반" for x in sorted(df_base['반'].unique())] if not df_base.empty else ["전체 학급 보기"]
                    sel_c = st.selectbox("🎯 학급 필터링", c_opts, key="ent_c")
                    
                    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
                    # 💡 요구사항 2번: 명칭 다운로드 양식 변경 반영
                    st.markdown("💡 **양식 샘플 내려받기**")
                    t_cols = ["반", "번호", "이름", "학교 이메일", "비밀번호"] + titles[:cnt]
                    t_df = pd.DataFrame({"반":[1,1],"번호":[1,2],"이름":["샘플1","샘플2"],"학교 이메일":["s1@sc.kr","s2@sc.kr"],"비밀번호":["1234","1234"]})
                    for title in titles[:cnt]: t_df[title] = [0, 0]
                    st.download_button("📥 일괄 업로드용 성적 양식(.CSV / .XLSX) 다운로드", data=t_df.to_csv(index=False).encode('utf-8-sig'), file_name=f"성적양식_{sel_db['subject']}.csv", mime="text/csv", use_container_width=True)
                    
                    st.markdown("<br>📂 **외부 대량 파일 가져오기**", unsafe_allow_html=True)
                    up_f = st.file_uploader("파일 올리기", type=["csv","xlsx"], label_visibility="collapsed")
                    excel_df = None
                    if up_f:
                        try:
                            excel_df = pd.read_csv(up_f) if up_f.name.endswith(".csv") else pd.read_excel(up_f)
                            excel_df.columns = [c.strip() for c in excel_df.columns]
                            for idx, title in enumerate(titles[:cnt]):
                                if title in excel_df.columns: excel_df[f"수행평가{idx+1}"] = excel_df[title]
                            for c in ["수행평가1","수행평가2","수행평가3","수행평가4","수행평가5"]: 
                                if c not in excel_df.columns: excel_df[c] = 0
                            if "비밀번호" not in excel_df.columns: excel_df["비밀번호"] = "1234"
                            if "학교 이메일" not in excel_df.columns: excel_df["학교 이메일"] = "-"
                            excel_df["subject_key"] = sel_db['key']
                        except Exception as e: st.error(f"파일 양식 매핑 실패: {e}")
                
                with r_col:
                    # 💡 요구사항 1번: 엑셀 바로 윗줄에 배치 및 문구 다듬어 주입
                    st.markdown('<div class="guide-box">💡 개인별로 성적을 입력하고 싶으면 아래 테이블(엑셀) 영역의 점수 칸을 더블클릭하여 직접 점수를 수정하신 뒤, 우측 상단의 [💾 성적 저장하기] 버튼을 누르시면 클라우드에 최종 반영됩니다.</div>', unsafe_allow_html=True)
                    
                    btn_space, act_space = st.columns([7.5, 2.5])
                    with act_space:
                        save_trigger = st.button("💾 성적 저장하기", type="primary", use_container_width=True)
                    
                    df_curr = excel_df.copy() if excel_df is not None else df_base.copy()
                    if df_curr.empty: st.info("📢 등록된 학생 명단이 없습니다.")
                    else:
                        f_idx = df_curr[df_curr["반"].astype(int) == int(sel_c.replace("반",""))].index if sel_c != "전체 학급 보기" else df_curr.index
                        t_cols = ["반", "번호", "이름", "학교 이메일"]
                        ren_map = {}
                        align = {"반": st.column_config.TextColumn(alignment="center"), "번호": st.column_config.TextColumn(alignment="center"), "이름": st.column_config.TextColumn(alignment="center"), "학교 이메일": st.column_config.TextColumn(alignment="center")}
                        
                        for i in range(cnt):
                            db_c = f"수행평가{i+1}"
                            t_cols.append(db_c)
                            ren_map[db_c] = titles[i]
                            align[titles[i]] = st.column_config.NumberColumn(alignment="center")
                        
                        for h in ["성적조회 횟수", "최종 확인일시"]:
                            if h not in df_curr.columns: df_curr[h] = 0 if h=="성적조회 횟수" else "-"
                            t_cols.append(h)
                        align["성적조회 횟수"] = st.column_config.NumberColumn(alignment="center")
                        align["최종 확인일시"] = st.column_config.TextColumn(alignment="center")
                        
                        sub_df = df_curr.loc[f_idx, t_cols].rename(columns=ren_map)
                        edited_df = st.data_editor(sub_df, use_container_width=True, disabled=["반","번호","이름","학교 이메일","성적조회 횟수","최종 확인일시"], hide_index=True, column_config=align, height=440)
                        
                        if save_trigger:
                            if excel_df is not None:
                                supabase.table(student_table).delete().eq("subject_key", sel_db['key']).execute()
                            for idx_p, r_idx in enumerate(f_idx):
                                rec = df_curr.loc[r_idx].to_dict()
                                rec["subject_key"] = sel_db['key']
                                for i in range(cnt):
                                    rec[f"수행평가{i+1}"] = edited_df.iloc[idx_p][titles[i]]
                                supabase.table(student_table).upsert(rec).execute()
                            st.success("🎉 성적 대장이 원격 데이터베이스에 완벽히 동기화 보존되었습니다!"); time.sleep(0.4); st.rerun()

    # ---------------------------------------------------------------------
    # 3. 학생 정보 관리
    # ---------------------------------------------------------------------
    elif st.session_state["current_menu"] == "학생 정보 관리":
        with st.container(border=True):
            st.markdown('<div class="menu-title-container"><h4 class="menu-title-text">📇 학생 인적 사항 대장 서류 관리</h4></div>', unsafe_allow_html=True)
            rdbs = get_active_databases()
            if "마스터" not in st.session_state["allowed_subjects"]:
                rdbs = [d for d in rdbs if d['subject'].strip() in st.session_state["allowed_subjects"]]
            
            if not rdbs: st.info("📢 권한 연동된 과목이 없습니다.")
            else:
                l_col, r_col = st.columns([3, 7])
                with l_col:
                    s_opts = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in rdbs]
                    sel_db = rdbs[s_opts.index(st.selectbox("📂 대상 교과 관리", s_opts, key="inf_s"))]
                    df = pd.DataFrame(supabase.table(student_table).select("*").eq("subject_key", sel_db['key']).execute().data)
                    if not df.empty: df = df.sort_values(by=["반", "번호"]).reset_index(drop=True)
                    
                    c_opts = ["전체"] + [f"{x}반" for x in sorted(df['반'].unique())] if not df.empty else ["전체"]
                    sel_c = st.selectbox("👥 학반 필터", c_opts)
                    
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    if st.button("➕ 학생 개별 수동 추가", use_container_width=True): show_add_student_dialog(sel_db['key'])
                    save_inf = st.button("💾 학생 인적 정보 저장", type="primary", use_container_width=True)
                
                with r_col:
                    if df.empty: st.info("📢 학생 명단이 비어 있습니다.")
                    else:
                        f_idx = df[df["반"].astype(int) == int(sel_c.replace("반",""))].index if sel_c != "전체" else df.index
                        align = {"반": st.column_config.NumberColumn(alignment="center", format="%d"), "번호": st.column_config.NumberColumn(alignment="center", format="%d"), "이름": st.column_config.TextColumn(alignment="center"), "학교 이메일": st.column_config.TextColumn(alignment="center"), "비밀번호": st.column_config.TextColumn(alignment="center")}
                        edited_inf = st.data_editor(df.loc[f_idx, ["반","번호","이름","학교 이메일","비밀번호"]], use_container_width=True, hide_index=True, column_config=align, height=450)
                        
                        if save_inf:
                            for idx_p, r_idx in enumerate(f_idx):
                                rec = df.loc[r_idx].to_dict()
                                for c in edited_inf.columns: rec[c] = edited_inf.iloc[idx_p][c]
                                supabase.table(student_table).upsert(rec).execute()
                            st.success("🎉 학생 기본 인적 정보 수정 완료!"); time.sleep(0.3); st.rerun()

    # ---------------------------------------------------------------------
    # 4. 평가 대상 과목 구성 (💡 실시간 세팅 값 노출 & 다중 과목 매칭 로직 완벽 보완)
    # ---------------------------------------------------------------------
    elif st.session_state["current_menu"] == "평가 대상 과목 구성":
        with st.container(border=True):
            st.markdown('<div class="menu-title-container"><h4 class="menu-title-text">🎯 담당 평가 교과목 정보 및 수행평가 세부 기준 설계</h4></div>', unsafe_allow_html=True)
            
            l_layout, r_layout = st.columns(2)
            with l_layout:
                with st.container(border=True):
                    st.markdown("<h5 style='font-weight:800; color:#0f172a;'>⚙️ 1단계: 담당 과목 설정 선택</h5>", unsafe_allow_html=True)
                    st.caption("선생님께 부여된 담당 교과 중 세팅/수정할 과목 조건을 정확히 지정해 주세요.")
                    
                    g_opts = ["교과군을 선택하세요.", "인문·사회군", "수리·과학군", "예체능군"]
                    sel_g = st.selectbox("교과군 선택", g_opts)
                    
                    # 💡 선생님의 소속 권한 과목군만 노출되도록 드롭다운을 유기적으로 통제
                    if sel_g != "교과군을 선택하세요.":
                        pool = SUBJECT_MAP.get(sel_g, [])
                        if "마스터" not in st.session_state["allowed_subjects"]:
                            pool = [x for x in pool if x in st.session_state["allowed_subjects"]]
                        s_opts = ["과목을 선택하세요."] + pool
                    else: s_opts = ["과목을 선택하세요."]
                        
                    final_sub = st.selectbox("세부 교과 선택", s_opts)
                    sel_gr = st.selectbox("대상 학년", ["학년을 선택하세요.", "1학년", "2학년", "3학년"])
                    sel_se = st.selectbox("대상 학기", ["학기를 선택하세요.", "2026학년도 1학기", "2026학년도 2학기"])

            is_valid = (sel_g != "교과군을 선택하세요." and final_sub != "과목을 선택하세요." and sel_gr != "학년을 선택하세요." and sel_se != "학기를 선택하세요.")

            with r_layout:
                if is_valid:
                    # 💡 선택 조건에 맞춰서 고유 키를 조합해 실시간 DB 연동
                    subject_key = f"{final_sub}_{sel_gr}_{sel_se}".replace(" ", "_")
                    cfg_df = load_db_df(config_table)
                    match = cfg_df[cfg_df["subject_key"] == subject_key] if not cfg_df.empty else pd.DataFrame()
                    
                    # 💡 만약 예전에 세팅해 둔 기록이 있다면 '초기화'되지 않고 그대로 값을 불러옴 (다중 과목 전환 대응 핵심)
                    if not match.empty:
                        row = match.iloc[0]
                        init_cnt = int(row.get("item_count", 3))
                        init_titles = [row.get(f"item{i}_name", f"수행평가{i}") for i in range(1, 6)]
                    else:
                        init_cnt = 3
                        init_titles = ["수행평가1", "수행평가2", "수행평가3", "수행평가4", "수행평가5"]
                        
                    with st.container(border=True):
                        st.markdown("<h5 style='font-weight:800; color:#0f172a;'>🎯 2단계: 수행평가 세부 반영 항목 명칭 구성</h5>", unsafe_allow_html=True)
                        st.caption("선택하신 교과의 수행평가 항목 개수를 고르면 입력창이 동적으로 열립니다.")
                        
                        item_cnt = st.selectbox("평가 반영 항목 총 개수", [1,2,3,4,5], index=(init_cnt-1))
                        item_titles = []
                        
                        for i in range(item_cnt):
                            val = init_titles[i] if i < len(init_titles) else f"수행평가{i+1}"
                            txt = st.text_input(f"항목 {i+1} 실제 명칭 (예: 듣기/말하기 등)", value=val, key=f"title_assign_{i}")
                            item_titles.append(txt.strip())
                            
                        st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
                        if st.button("💾 이 과목 세팅 세이브 및 확정", type="primary", use_container_width=True):
                            record = {
                                "subject_key": subject_key, "item_count": item_cnt,
                                "item1_name": item_titles[0] if item_cnt >= 1 else "-",
                                "item2_name": item_titles[1] if item_cnt >= 2 else "-",
                                "item3_name": item_titles[2] if item_count >= 3 else "-",
                                "item4_name": item_titles[3] if item_cnt >= 4 else "-",
                                "item5_name": item_titles[4] if item_cnt >= 5 else "-"
                            }
                            supabase.table(config_table).upsert(record).execute()
                            st.success("🎉 과목 구성 기준이 클라우드에 성공적으로 기록되었습니다!"); time.sleep(0.4)
                            st.session_state["current_menu"] = "수행 평가 성적 입력"; st.rerun()
                else:
                    st.markdown("<div style='border: 2px dashed #cbd5e1; border-radius: 8px; padding: 70px 20px; text-align: center; color: #94a3b8; margin-top: 15px;'>⬅️ 왼쪽에서 세부 과목, 학년, 학기 조건을 모두 정확히 지정하셔야<br>해당 과목의 기존 수행평가 세팅 내역을 DB에서 불러와 수정할 수 있습니다.</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 5. 교사 계정 관리 대장 (최고관리자 전용)
    # ---------------------------------------------------------------------
    elif st.session_state["current_menu"] == "👑 교사 계정 관리 대장" and st.session_state["logged_teacher_id"] == "admin":
        with st.container(border=True):
            st.markdown('<div class="menu-title-container"><h4 class="menu-title-text">👑 전교 교사 권한 관리 관제 기구</h4></div>', unsafe_allow_html=True)
            df_tc = load_db_df(teacher_table)
            edited_tc = st.data_editor(df_tc, use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns([8, 2])
            with c1:
                if st.button("👨‍🏫 신규 교사 권한 계정 추가"): show_add_teacher_dialog()
            with c2:
                if st.button("💾 교사 진도 권한 원격 저장", type="primary", use_container_width=True):
                    if not df_tc.empty:
                        for _, r in df_tc.iterrows(): supabase.table(teacher_table).delete().eq("교사_ID", str(r["교사_ID"])).execute()
                    for r in edited_tc.to_dict(orient="records"):
                        if r.get("교사_ID"): supabase.table(teacher_table).upsert(r).execute()
                    st.success("🎉 전국 교사 권한 세이브 완료!"); time.sleep(0.3); st.rerun()
