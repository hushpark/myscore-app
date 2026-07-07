import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import io
import re
from supabase import create_client, Client

# 🚨 [최상단 규칙 엄수] 와이드 레이아웃 설정
st.set_page_config(page_title="수행평가 점수 확인 시스템 (Supabase)", layout="wide")

# =========================================================================
# 🎨 [디자인 가시성 패치] 디자인 통합 및 접속 모드 라디오 버튼 수동 여백 복구
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        [data-testid="stAppViewContainer"] { margin-left: 0px !important; }
        [data-testid="stSidebar"], section[data-testid="stSidebar"] { min-width: 280px !important; max-width: 280px !important; background-color: #1e293b !important; box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; }
        [data-testid="stSidebar"] .stRadio label p, [data-testid="stSidebar"] .stRadio label span, [data-testid="stSidebar"] .stRadio label div, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[role="radiogroup"] * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; opacity: 1 !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 16px !important; font-weight: 700 !important; line-height: 2.2 !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover * { color: #60a5fa !important; -webkit-text-fill-color: #60a5fa !important; }
        .sidebar-title { font-size: 24px !important; font-weight: 800 !important; margin-bottom: 5px !important; display: block; }
        .user-info { color: #38bdf8 !important; -webkit-text-fill-color: #38bdf8 !important; font-size: 14px !important; font-weight: 600 !important; margin-bottom: 25px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 12px 0 !important; width: 100% !important; display: block !important; margin-bottom: 8px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] *, [data-testid="stSidebar"] button[kind="secondary"] p { color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; font-size: 15px !important; font-weight: 700 !important; }
        
        /* 일반 화면 primary 버튼 */
        div.stButton > button[kind="primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #2563eb !important; }
        
        /* 🔓 로그인 폼 제출용 버튼 디자인 */
        form[data-testid="stForm"] button {
            background-color: #ffffff !important;
            color: #0f172a !important;
            font-weight: 700 !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
            width: 100% !important;
            padding: 10px 0 !important;
            box-shadow: none !important;
        }
        form[data-testid="stForm"] button:hover {
            background-color: #f8fafc !important;
            border-color: #3b82f6 !important;
            color: #2563eb !important;
        }
        
        /* 📝 [수동 조절 칸] 왼쪽 밀기 여백 */
        div[data-testid="stForm"] div[data-testid="stRadio"] { 
            padding-left: 95px !important; 
            margin-bottom: 25px !important; 
            width: 100% !important; 
        }
        div[data-testid="stForm"] div[role="radiogroup"] { 
            display: flex !important; 
            gap: 35px !important; 
            align-items: center !important; 
        }
        
        div[data-testid="InputInstructions"] { display: none !important; }
        div[data-testid="stSelectbox"] label p, div[data-testid="stTextInput"] label p { font-weight: 800 !important; color: #1e293b !important; font-size: 15px !important; }
        div[data-testid="stTextInput"] > div, div[data-testid="stSelectbox"] > div { background-color: #ffffff !important; border: 1px solid #94a3b8 !important; border-radius: 6px !important; }
        div[data-testid="stTextInput"] input { background-color: #ffffff !important; color: #0f172a !important; padding: 8px 12px !important; }
        div[data-testid="stTextInput"] > div:focus-within, div[data-testid="stSelectbox"] > div:focus-within { border: 2px solid #3b82f6 !important; outline: none !important; }
        
        /* 로그인 박스 */
        div[data-testid="stForm"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; padding: 45px 40px 45px 40px !important; border-radius: 24px !important; box-shadow: 0 15px 40px rgba(0,0,0,0.06) !important; max-width: 440px !important; margin: 70px auto 0 auto !important; }
        div[data-testid="stForm"] h2 { font-size: 26px !important; white-space: nowrap !important; text-align: center !important; margin: 0 auto 20px auto !important; font-weight: 800 !important; color: #0f172a !important; }
        .footer-container { width: 100%; display: flex; justify-content: center; margin-top: 25px; }
        .footer-text { text-align: center; font-size: 12px; color: #94a3b8; font-weight: 500; }
        h3 { color: #1e293b !important; font-weight: 700 !important; font-size: 20px !important; margin-top: 0px !important; margin-bottom: 5px !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 🔑 [Supabase 원격 데이터베이스 연결 체계 주입]
# =========================================================================
SUPABASE_URL = "https://jwkvojfmhorndnnhscwl.supabase.co"
SUPABASE_KEY = "sb_publishable_6--SHGogHaHSEVO7g3rNjQ_FOHO-XlN"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

student_table = "st_info_2_2026_1"
teacher_table = "teacher_accounts"

# =========================================================================
# 🚀 원격 테이블 자동 생성 엔진
# =========================================================================
def create_table_if_not_exists(table_type):
    try:
        if table_type == "teacher":
            supabase.rpc("exec_sql", {"query": f"""
                CREATE TABLE IF NOT EXISTS public.{teacher_table} (
                    "교사_ID" text PRIMARY KEY,
                    "교사_성명" text,
                    "비밀번호" text,
                    "담당_과목" text
                );
                ALTER TABLE public.{teacher_table} DISABLE ROW LEVEL SECURITY;
            """}).execute()
        elif table_type == "student":
            supabase.rpc("exec_sql", {"query": f"""
                CREATE TABLE IF NOT EXISTS public.{student_table} (
                    "반" int8,
                    "번호" int8,
                    "이름" text,
                    "학교 이메일" text,
                    "비밀번호" int8,
                    "수행평가1" int8 DEFAULT 0,
                    "수행평가2" int8 DEFAULT 0,
                    "수행평가3" int8 DEFAULT 0,
                    "성적조회 횟수" int8 DEFAULT 0,
                    "최종 확인일시" text DEFAULT '-',
                    PRIMARY KEY ("반", "번호")
                );
                ALTER TABLE public.{student_table} DISABLE ROW LEVEL SECURITY;
            """}).execute()
    except Exception:
        pass

create_table_if_not_exists("teacher")
create_table_if_not_exists("student")

def load_db_df(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

# =========================================================================
# ➕ [다이얼로그 팝업창] 
# =========================================================================
@st.dialog("➕ 담당 교사 개별 추가")
def show_add_teacher_dialog():
    st.markdown("새로 임용/등록할 선생님의 권한 정보를 입력해 주세요.")
    with st.form("add_teacher_form", border=False):
        t_id = st.text_input("교사 전용 ID", placeholder="예: info_teacher")
        t_name = st.text_input("교사 성명", placeholder="예: 박디몬")
        t_pw = st.text_input("초기 임시 비밀번호", placeholder="예: 1234")
        t_subs = st.text_input("담당 과목 권한 지정 (쉼표 분리)", placeholder="예: 정보, 수학")
        submit_btn = st.form_submit_button("💾 이 교사 계정 활성화하기", use_container_width=True)
        if submit_btn:
            if not t_id or not t_name or not t_pw or not t_subs: st.error("❌ 모든 항목을 입력해야 합니다.")
            else:
                try:
                    supabase.table(teacher_table).upsert({"교사_ID": t_id.strip(), "교사_성명": t_name.strip(), "비밀번호": t_pw.strip(), "담당_과목": t_subs.strip()}).execute()
                    st.success("🎉 교사 데이터베이스 인프라에 새로운 교사 계정이 활성화되었습니다!")
                    st.rerun()
                except: st.error("❌ 등록 실패")

@st.dialog("➕ 전학생 / 개별 학생 추가")
def show_add_student_dialog():
    st.markdown("새로 명단에 추가할 학생의 기본 정보를 입력해 주세요.")
    with st.form("add_student_form", border=False):
        c1, c2, c3 = st.columns(3)
        with c1: new_ban = st.number_input("반", min_value=1, max_value=15, step=1)
        with c2: new_num = st.number_input("번호", min_value=1, max_value=50, step=1)
        with c3: new_name = st.text_input("이름")
        c4, c5 = st.columns(2)
        with c4: new_email = st.text_input("학교 이메일")
        with c5: new_pw = st.text_input("초기 비밀번호")
        submit_btn = st.form_submit_button("💾 이 학생 명단에 추가하기", use_container_width=True)
        if submit_btn:
            if not new_name or not new_email or not new_pw: st.error("❌ 모든 항목을 빠짐없이 입력해 주세요.")
            else:
                try:
                    supabase.table(student_table).upsert({"반": int(new_ban), "번호": int(new_num), "이름": new_name.strip(), "학교 이메일": new_email.strip(), "비밀번호": int(new_pw), "수행평가1": 0, "수행평가2": 0, "수행평가3": 0, "성적조회 횟수": 0, "최종 확인일시": "-"}).execute()
                    st.success("🎉 학생 데이터가 원격 DB에 주입되었습니다!")
                    st.rerun()
                except: st.error("❌ 학생 추가 실패")

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_data):
    st.markdown(f"<div><b>{student_data['이름']}</b> 학생의 실시간 성적 내역입니다.</div>", unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("📝 수행평가 1차", f"{int(student_data['수행평가1'])} 점")
    sc2.metric("📝 수행평가 2차", f"{int(student_data['수행평가2'])} 점")
    sc3.metric("📝 수행평가 3차", f"{int(student_data['수행평가3'])} 점")
    if "has_counted" not in st.session_state:
        new_count = int(student_data.get("성적조회 횟수", 0)) + 1
        supabase.table(student_table).upsert({"반": int(student_data["반"]), "번호": int(student_data["번호"]), "성적조회 횟수": new_count, "최종 확인일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).execute()
        st.session_state["has_counted"] = True
    if st.button("닫기", type="secondary", use_container_width=True):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.session_state.clear()
        st.rerun()

# ⚙️ [세션 제어 상태 초기화]
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "student_logged_in" not in st.session_state: st.session_state["student_logged_in"] = False
if "logged_student_id" not in st.session_state: st.session_state["logged_student_id"] = ""
if "logged_student_pw" not in st.session_state: st.session_state["logged_student_pw"] = ""
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = ""
if "logged_teacher_pw" not in st.session_state: st.session_state["logged_teacher_pw"] = ""
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = ""
if "allowed_subjects" not in st.session_state: st.session_state["allowed_subjects"] = []

df = load_db_df(student_table)

# =========================================================================
# 🔓 [1단계] 클린 통합 로그인 시스템
# =========================================================================
if not st.session_state["admin_logged_in"] and not st.session_state["student_logged_in"]:
    with st.container():
        with st.form("master_unified_form"):
            st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
            login_mode = st.radio("접속 모드", ["학생", "교사"], horizontal=True, label_visibility="collapsed")
            user_id_input = st.text_input("ID", placeholder="ID를 입력하세요", label_visibility="collapsed")
            user_pw_input = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed")
            
            b_col2 = st.columns([1.0, 1.8, 1.0])[1]
            submit_active = b_col2.form_submit_button("로그인", use_container_width=True)
            
            if submit_active:
                clean_id = str(user_id_input).strip()
                clean_pw = str(user_pw_input).strip()
                if login_mode == "학생":
                    if df.empty: st.error("❌ 등록된 성적 데이터셋이 백엔드에 존재하지 않습니다.")
                    else:
                        id_col = "학교 이메일" if "학교 이메일" in df.columns else "school_email"
                        id_match = df[df[id_col] == clean_id]
                        if id_match.empty: st.error("❌ 등록되지 않은 학생 정보입니다.")
                        else:
                            if str(id_match.iloc[0]["비밀번호"]) == clean_pw:
                                st.session_state["student_logged_in"] = True
                                st.session_state["logged_student_id"] = clean_id
                                st.session_state["logged_student_pw"] = clean_pw
                                st.rerun()
                            else: st.error("❌ 비밀번호 불일치")
                elif login_mode == "교사":
                    if clean_id == "admin" and clean_pw == "1234":
                        st.session_state["admin_logged_in"] = True
                        st.session_state["logged_teacher_id"] = "admin"
                        st.session_state["logged_teacher_pw"] = "1234"
                        st.session_state["teacher_name"] = "최고관리자"
                        st.session_state["allowed_subjects"] = ["마스터"]
                        st.rerun()
                    else:
                        df_tc = load_db_df(teacher_table)
                        if df_tc.empty: st.error("❌ 일반 교사 계정이 비어있습니다. 최고관리자 계정으로 먼저 등록하세요.")
                        else:
                            id_match = df_tc[df_tc['교사_ID'] == clean_id]
                            if not id_match.empty and str(id_match.iloc[0]['비밀번호']) == clean_pw:
                                row = id_match.iloc[0]
                                st.session_state["admin_logged_in"] = True
                                st.session_state["logged_teacher_id"] = clean_id
                                st.session_state["logged_teacher_pw"] = clean_pw
                                st.session_state["teacher_name"] = str(row['교사_성명']).strip()
                                st.session_state["allowed_subjects"] = [s.strip() for s in str(row['담당_과목']).split(",") if s.strip()]
                                st.rerun()
                            else: st.error("❌ 교사 로그인 실패")

    st.markdown("<div class='footer-container'><div class='footer-text'>Designed & Developed by User & Supabase Backend Engine</div></div>", unsafe_allow_html=True)

# =========================================================================
# 🎓 [2단계-A] 학생 화면
# =========================================================================
elif st.session_state["student_logged_in"]:
    st.markdown(f"<h2>수행평가 점수 확인 시스템 (학생 모드)</h2>", unsafe_allow_html=True)
    if st.button("🚪 로그아웃"): st.session_state.clear(); st.rerun()
    if st.button("🚀 나의 수행평가 성적 실시간 검증", type="primary", use_container_width=True):
        id_col = "학교 이메일" if "학교 이메일" in df.columns else "school_email"
        res = df[(df[id_col] == st.session_state["logged_student_id"]) & (df['비밀번호'].astype(str) == st.session_state["logged_student_pw"])]
        if not res.empty: show_result_dialog(res.iloc[0].to_dict())

# =========================================================================
# 🔒 [2단계-B] 교사 화면
# =========================================================================
elif st.session_state["admin_logged_in"]:
    with st.sidebar:
        st.markdown('<span class="sidebar-title">📋 교사 메뉴</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="user-info">👤 {st.session_state["teacher_name"]} 접속 중</div>', unsafe_allow_html=True)
        st.markdown("---")
        menus = ["▶ 학생 조회 현황 모니터링", "▶ 개인별 성적 입력", "▶ 학생 정보 관리", "▶ 성적 전체 일괄 업로드(CSV/Excel)"]
        if st.session_state["logged_teacher_id"] == "admin": menus.append("👑 교사 계정 관리 대장")
        menu_selection = st.radio("메뉴 선택", menus, label_visibility="collapsed")
        if st.sidebar.button("🚪 로그아웃", type="secondary", use_container_width=True): st.session_state.clear(); st.rerun()

    if not df.empty and "반" in df.columns and "번호" in df.columns: df = df.sort_values(by=["반", "번호"])

    if menu_selection == "▶ 학생 조회 현황 모니터링":
        with st.container(border=True):
            if df.empty: st.info("📢 현재 데이터베이스가 비어있습니다.")
            else:
                sel_c = st.selectbox("🎯 학급 선택", options=["전체 학급 보기"] + [f"{x}반" for x in sorted(df['반'].unique())])
                r_df = df.copy()
                if sel_c != "전체 학급 보기": r_df = r_df[r_df['반'].astype(int) == int(sel_c.replace("반",""))]
                st.dataframe(r_df[["반", "번호", "이름", "학교 이메일", "수행평가1", "수행평가2", "수행평가3", "성적조회 횟수", "최종 확인일시"]].fillna("-"), use_container_width=True, hide_index=True)

    elif menu_selection == "▶ 개인별 성적 입력":
        with st.container(border=True):
            if df.empty: st.info("등록된 학생 데이터가 없습니다.")
            else:
                sel_c = st.selectbox("👥 학반 필터링", options=["전체"] + [f"{x}반" for x in sorted(df['반'].unique())])
                f_idx = df[df["반"].astype(int) == int(sel_c.replace("반", ""))].index if sel_c != "전체" else df.index
                edited_df = st.data_editor(df.loc[f_idx, ["반", "번호", "이름", "수행평가1", "수행평가2", "수행평가3"]], use_container_width=True, disabled=["반", "번호", "이름"], hide_index=True)
                if st.button("💾 성적 저장하기", type="primary", use_container_width=True):
                    for idx_pos, r_idx in enumerate(f_idx):
                        for col in edited_df.columns: df.loc[r_idx, col] = edited_df.iloc[idx_pos][col]
                        supabase.table(student_table).upsert(df.loc[r_idx].to_dict()).execute()
                    st.success("🎉 변경된 수행 점수가 실시간 저장되었습니다!"); st.rerun()

    elif menu_selection == "▶ 학생 정보 관리":
        with st.container(border=True):
            if df.empty:
                st.info("현재 등록된 학생이 없습니다.")
                if st.button("➕ 첫 학생 개별 추가", type="primary"): show_add_student_dialog()
            else:
                sel_c = st.selectbox("👥 학반 필터링", options=["전체"] + [f"{x}반" for x in sorted(df['반'].unique())])
                f_idx = df[df["반"].astype(int) == int(sel_c.replace("반", ""))].index if sel_c != "전체" else df.index
                edited_df = st.data_editor(df.loc[f_idx, ["반", "번호", "이름", "학교 이메일", "비밀번호"]], use_container_width=True, hide_index=True)
                c1, c2 = st.columns([4.8, 1.2])
                with c1:
                    if st.button("➕ 학생 개별 추가"): show_add_student_dialog()
                with c2:
                    if st.button("💾 학생 정보 저장", type="primary", use_container_width=True):
                        for idx_pos, r_idx in enumerate(f_idx):
                            for col in edited_df.columns: df.loc[r_idx, col] = edited_df.iloc[idx_pos][col]
                            supabase.table(student_table).upsert(df.loc[r_idx].to_dict()).execute()
                        st.success("🎉 인적사항이 동기화되었습니다!"); st.rerun()

    elif menu_selection == "▶ 성적 전체 일괄 업로드(CSV/Excel)":
        with st.container(border=True):
            st.markdown("<h3>📥 성적 데이터 초기화 및 자동 인프라 맵핑</h3>")
            up_f = st.file_uploader("명단 파일 선택", type=["csv", "xlsx"])
            if up_f:
                df_up = pd.read_csv(up_f) if up_f.name.endswith(".csv") else pd.read_excel(up_f)
                df_up.columns = [c.strip() for c in df_up.columns]
                st.dataframe(df_up.head(3), use_container_width=True, hide_index=True)
                if st.button("🚀 클라우드 DB 원격 초기화 및 새 명단 이식 실행", type="primary", use_container_width=True):
                    create_table_if_not_exists("student")
                    if not df.empty:
                        for _, r in df.iterrows(): supabase.table(student_table).delete().eq("반", int(r["반"])).eq("번호", int(r["번호"])).execute()
                    for c in ["수행평가1", "수행평가2", "수행평가3", "성적조회 횟수"]:
                        if c not in df_up.columns: df_up[c] = 0
                    df_up["최종 확인일시"] = "-"
                    for record in df_up.to_dict(orient="records"): supabase.table(student_table).insert(record).execute()
                    st.success("🎯 대량 성적 이식 및 인프라 구축 성공!"); st.rerun()

    # 👑 교사 대장 레이아웃 완성 및 새로고침(st.rerun) 완전 결합부
    elif menu_selection == "👑 교사 계정 관리 대장" and st.session_state["logged_teacher_id"] == "admin":
        with st.container(border=True):
            st.markdown("<h3>👑 교사 계정 자동 관리 관제 센터</h3>", unsafe_allow_html=True)
            
            # 상단 실시간 교사 현황 데이터 그리드 호출
            df_tc = load_db_df(teacher_table)
            edited_tc_df = st.data_editor(df_tc, use_container_width=True, num_rows="fixed", hide_index=True, key="master_tc_editor")
            c1, c2 = st.columns([4.8, 1.2])
            with c1:
                if st.button("👨‍🏫 교사 개별 신규 추가"): show_add_teacher_dialog()
            with c2:
                if st.button("💾 교사 정보 원격 저장", type="primary", use_container_width=True):
                    create_table_if_not_exists("teacher")
                    if not df_tc.empty:
                        for _, row in df_tc.iterrows(): supabase.table(teacher_table).delete().eq("교사_ID", str(row["교사_ID"])).execute()
                    for record in edited_tc_df.to_dict(orient="records"):
                        if record.get("교사_ID"): supabase.table(teacher_table).upsert(record).execute()
                    st.success("🎉 교사 권한 정보 세이브 완료!"); st.rerun()
                    
            st.markdown("<hr style='border: 1px dashed #cbd5e1; margin: 30px 0;'>", unsafe_allow_html=True)
            
            st.markdown("#### 📥 선생님 명단 대량 일괄 등록 (CSV/Excel)")
            st.caption("인사이동 등으로 많은 선생님을 한 번에 등록해야 할 때, 아래 파일 업로더를 이용하세요.")
            
            tc_template = pd.DataFrame({
                "교사_ID": ["math_01", "eng_02"], "교사_성명": ["이수학", "김영어"],
                "비밀번호": ["1234", "1234"], "담당_과목": ["수학", "영어, 한문"]
            })
            tc_csv = tc_template.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 교사 일괄 등록용 서식 샘플(.CSV) 다운로드", data=tc_csv, file_name="교사일괄등록_양식.csv", mime="text/csv")
            
            tc_file = st.file_uploader("선생님 명단 파일 업로드", type=["csv", "xlsx"], key="teacher_file_uploader_master")
            
            if tc_file:
                df_tc_up = pd.read_csv(tc_file) if tc_file.name.endswith(".csv") else pd.read_excel(tc_file)
                df_tc_up.columns = [c.strip() for c in df_tc_up.columns]
                
                st.markdown("##### 🔍 업로드된 교사 명단 구조 파싱")
                st.dataframe(df_tc_up, use_container_width=True, hide_index=True)
                
                tc_req = ["교사_ID", "교사_성명", "비밀번호", "담당_과목"]
                tc_miss = [c for c in tc_req if c not in df_tc_up.columns]
                
                if tc_miss:
                    st.error(f"❌ 서식 오류: 필수 열이 누락되었습니다 -> {tc_miss}")
                else:
                    # ⭐ 폼 외부 분리를 유도하기 위해 컬럼을 쪼갠 뒤 버튼을 우측 정렬 형태로 강제 정돈 완료
                    btn_space1, btn_space2 = st.columns([3.8, 1.2])
                    with btn_space2:
                        if st.button("🚀 교사 일괄 이식 실행", type="primary", use_container_width=True, key="master_tc_upload_trigger_btn"):
                            with st.spinner("교사 원격 인프라 구조 밀어 넣는 중..."):
                                create_table_if_not_exists("teacher")
                                if not df_tc.empty:
                                    for _, r in df_tc.iterrows():
                                        supabase.table(teacher_table).delete().eq("교사_ID", str(r["교사_ID"])).execute()
                                for record in df_tc_up.to_dict(orient="records"):
                                    supabase.table(teacher_table).insert(record).execute()
                            
                            st.success("🎯 전 교사 인적사항 권한 계정이 클라우드 DB에 일괄 등록 완료되었습니다!")
                            st.balloons()
                            
                            # 🔄 [수정 완료] 저장 후 빈 화면으로 고정되지 않고 전역 세션을 강제로 완전히 새로고침 시킵니다.
                            st.rerun()
