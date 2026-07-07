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
# 🔄 [방탄 CSS] 디자인 통합 및 이중 테두리 완벽 제거
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        [data-testid="stAppViewContainer"] { margin-left: 0px !important; }

        /* 사이드바 배경 및 폭 고정 */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] { 
            min-width: 280px !important; 
            max-width: 280px !important; 
            background-color: #1e293b !important; 
            box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; 
        }
        
        /* 사이드바 메뉴 텍스트 순백색 관통 */
        [data-testid="stSidebar"] .stRadio label p,
        [data-testid="stSidebar"] .stRadio label span,
        [data-testid="stSidebar"] .stRadio label div,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div[role="radiogroup"] *,
        [data-testid="stSidebar"] div[role="radiogroup"] label *,
        [data-testid="stSidebar"] div[role="radiogroup"] p,
        [data-testid="stSidebar"] div[role="radiogroup"] span {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 16px !important; font-weight: 700 !important; line-height: 2.2 !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover * { color: #60a5fa !important; -webkit-text-fill-color: #60a5fa !important; }
        
        .sidebar-title { font-size: 24px !important; font-weight: 800 !important; margin-bottom: 5px !important; display: block; }
        .user-info { color: #38bdf8 !important; -webkit-text-fill-color: #38bdf8 !important; font-size: 14px !important; font-weight: 600 !important; margin-bottom: 25px !important; }

        /* 사이드바 버튼 예외 처리 */
        [data-testid="stSidebar"] button[kind="secondary"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 12px 0 !important; width: 100% !important; display: block !important; margin-bottom: 8px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] *, [data-testid="stSidebar"] button[kind="secondary"] p { color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; font-size: 15px !important; font-weight: 700 !important; }
        [data-testid="stSidebar"] button[kind="secondary"]:hover { background-color: #f8fafc !important; border-color: #3b82f6 !important; }

        /* 일반 버튼 디자인 */
        div.stButton > button[kind="primary"], button[data-testid="baseButton-primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2) !important; }
        div.stButton > button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover { background-color: #2563eb !important; }
        div.stButton > button[kind="secondary"], button[data-testid="baseButton-secondary"] { background-color: #ffffff !important; color: #0f172a !important; font-weight: 700 !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
        div.stButton > button[kind="secondary"]:hover, button[data-testid="baseButton-secondary"]:hover { background-color: #f8fafc !important; border-color: #3b82f6 !important; color: #2563eb !important; }

        /* 로그인 폼 버튼 디자인 강제 지정 */
        form[data-testid="stForm"] button { background-color: #ffffff !important; color: #0f172a !important; font-weight: 700 !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; width: 100% !important; padding: 10px 0 !important; box-shadow: none !important; }
        form[data-testid="stForm"] button:hover { background-color: #f8fafc !important; border-color: #3b82f6 !important; color: #2563eb !important; }

        /* 팝업 다이얼로그 버튼 */
        [data-testid="stDialog"] button[kind="primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 800 !important; border: none !important; border-radius: 6px !important; padding: 12px 0 !important; font-size: 15px !important; width: 100% !important; }
        [data-testid="stDialog"] button[kind="secondary"] { background-color: #64748b !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; padding: 12px 0 !important; font-size: 15px !important; width: 100% !important; }

        div[data-testid="InputInstructions"] { display: none !important; }
        div[data-testid="stSelectbox"] label p, div[data-testid="stTextInput"] label p { font-weight: 800 !important; color: #1e293b !important; font-size: 15px !important; }

        /* 드롭다운 & 텍스트 박스 */
        div[data-testid="stTextInput"] > div, div[data-testid="stTextInput"] [data-baseweb="input"], div[data-testid="stSelectbox"] > div[data-baseweb="select"], div[data-testid="stSelectbox"] > div { background-color: #ffffff !important; border: 1px solid #94a3b8 !important; border-radius: 6px !important; transition: all 0.2s ease-in-out !important; box-shadow: none !important; }
        div[data-testid="stTextInput"] input { background-color: #ffffff !important; color: #0f172a !important; padding: 8px 12px !important; border-radius: 6px !important; box-shadow: none !important; }
        
        div[data-testid="stTextInput"] > div:focus-within, div[data-testid="stSelectbox"] > div:focus-within, div[data-testid="stTextInput"] input:focus { border: 2px solid #3b82f6 !important; outline: none !important; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important; }

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

# 테이블 지정
student_table = "st_info_2_2026_1"
teacher_table = "teacher_accounts"  # 신규 교사 계정 관리용 테이블 지정

# 데이터 로드 헬퍼 함수
def load_db_df(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

# =========================================================================
# 👤 [다이얼로그 팝업창] 교사 개별 등록 팝업창
# =========================================================================
@st.dialog("➕ 담당 교사 개별 추가")
def show_add_teacher_dialog():
    st.markdown("새로 임용/등록할 선생님의 권한 정보를 입력해 주세요.")
    with st.form("add_teacher_form", border=False):
        t_id = st.text_input("교사 전용 ID", placeholder="예: info_teacher")
        t_name = st.text_input("교사 성명", placeholder="예: 박디몬")
        t_pw = st.text_input("초기 임시 비밀번호", placeholder="예: 1234")
        t_subs = st.text_input("담당 과목 권한 지정 (쉼표 분리)", placeholder="예: 정보, 수학")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("💾 이 교사 계정 활성화하기", use_container_width=True)
        
        if submit_btn:
            if not t_id or not t_name or not t_pw or not t_subs: st.error("❌ 모든 항목을 입력해야 계정이 생성됩니다.")
            else:
                new_teacher = {
                    "교사_ID": t_id.strip(),
                    "교사_성명": t_name.strip(),
                    "비밀번호": t_pw.strip(),
                    "담당_과목": t_subs.strip()
                }
                try:
                    supabase.table(teacher_table).upsert(new_teacher).execute()
                    st.success("🎉 교사 데이터베이스 인프라에 새로운 교사 계정이 이식되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 데이터베이스 생성 실패 (테이블 구조 확인 필요): {e}")

# =========================================================================
# ➕ [다이얼로그 팝업창] 전학생 추가 기능
# =========================================================================
@st.dialog("➕ 전학생 / 개별 학생 추가")
def show_add_student_dialog():
    st.markdown("새로 명단에 추가할 학생의 기본 정보를 입력해 주세요.")
    with st.form("add_student_form", border=False):
        c1, c2, c3 = st.columns(3)
        with c1: new_ban = st.number_input("반 (숫자만)", min_value=1, max_value=15, step=1)
        with c2: new_num = st.number_input("번호 (숫자만)", min_value=1, max_value=50, step=1)
        with c3: new_name = st.text_input("이름", placeholder="예: 홍길동")
        
        c4, c5 = st.columns(2)
        with c4: new_email = st.text_input("학교 이메일", placeholder="예: student@school.kr")
        with c5: new_pw = st.text_input("초기 비밀번호", placeholder="예: 1234")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("💾 이 학생 명단에 추가하기", use_container_width=True)
        
        if submit_btn:
            if not new_name or not new_email or not new_pw: st.error("❌ 모든 항목을 빠짐없이 입력해 주세요.")
            else:
                new_record = {
                    "반": int(new_ban), "번호": int(new_num), "이름": new_name.strip(),
                    "학교 이메일": new_email.strip(), "비밀번호": int(new_pw),
                    "수행평가1": 0, "수행평가2": 0, "수행평가3": 0, "성적조회 횟수": 0, "최종 확인일시": "-"
                }
                try:
                    supabase.table(student_table).upsert(new_record).execute()
                    st.success("🎉 새로운 학생 데이터가 Supabase DB에 실시간 주입되었습니다!")
                    st.rerun()
                except: st.error("❌ 학생 추가 실패")

# =========================================================================
# 🎉 [다이얼로그 팝업창] 학생 1인 조회 팝업창
# =========================================================================
@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_data):
    st.markdown(f"<div><b>{student_data['이름']}</b> 학생의 실시간 성적 내역입니다.</div>", unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("📝 수행평가 1차", f"{int(student_data['수행평가1'])} 점")
    sc2.metric("📝 수행평가 2차", f"{int(student_data['수행평가2'])} 점")
    sc3.metric("📝 수행평가 3차", f"{int(student_data['수행평가3'])} 점")
    
    if "has_counted" not in st.session_state:
        new_count = int(student_data.get("성적조회 횟수", 0)) + 1
        supabase.table(student_table).upsert({
            "반": int(student_data["반"]), "번호": int(student_data["번호"]),
            "성적조회 횟수": new_count, "최종 확인일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).execute()
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
# 🔓 [1단계] 클린 통합 로그인 시스템 (교사 명단 DB 검증 엔진 탑재)
# =========================================================================
if not st.session_state["admin_logged_in"] and not st.session_state["student_logged_in"]:
    with st.container():
        with st.form("master_unified_form"):
            st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
            
            login_mode = st.radio("접속 모드", ["학생", "교사"], horizontal=True, label_visibility="collapsed", key="pure_system_role_radio")
            user_id_input = st.text_input("ID", placeholder="ID를 입력하세요", label_visibility="collapsed", key="pure_user_id_field")
            user_pw_input = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed", key="pure_user_pw_field")
            
            b_col1, b_col2, b_col3 = st.columns([1.0, 1.8, 1.0])
            with b_col2: submit_active = st.form_submit_button("로그인", use_container_width=True)
            
            if submit_active:
                clean_id = str(user_id_input).strip()
                clean_pw = str(user_pw_input).strip()
                
                if login_mode == "학생":
                    if not clean_id or not clean_pw: st.error("❌ 학생 ID(이메일)와 비밀번호를 모두 입력하세요.")
                    elif df.empty: st.error("❌ 현재 백엔드 데이터베이스가 비어있습니다.")
                    else:
                        id_col = "학교 이메일" if "학교 이메일" in df.columns else "school_email"
                        id_match = df[df[id_col] == clean_id]
                        if id_match.empty: st.error("❌ 등록되지 않은 학생 정보입니다.")
                        else:
                            pw_match = id_match[id_match["비밀번호"].astype(str) == clean_pw]
                            if pw_match.empty: st.error("❌ 비밀번호가 일치하지 않습니다.")
                            else:
                                st.session_state["student_logged_in"] = True
                                st.session_state["logged_student_id"] = clean_id
                                st.session_state["logged_student_pw"] = clean_pw
                                st.rerun()
                                            
                elif login_mode == "교사":
                    # 최고관리자 고정 통과 마스터키
                    if clean_id == "admin" and clean_pw == "1234":
                        st.session_state["admin_logged_in"] = True
                        st.session_state["logged_teacher_id"] = "admin"
                        st.session_state["logged_teacher_pw"] = "1234"
                        st.session_state["teacher_name"] = "최고관리자"
                        st.session_state["allowed_subjects"] = ["마스터"]
                        st.rerun()
                    else:
                        # 🔍 원격 Supabase 교사 계정 테이블 실시간 쿼리 검증 작동
                        df_tc = load_db_df(teacher_table)
                        if df_tc.empty: st.error("❌ 교사 계정 데이터베이스를 호출하지 못했습니다.")
                        else:
                            id_match = df_tc[df_tc['교사_ID'] == clean_id]
                            if id_match.empty: st.error("❌ 존재하지 않는 교사 권한 ID입니다.")
                            else:
                                pw_match = id_match[id_match['비밀번호'].astype(str) == clean_pw]
                                if pw_match.empty: st.error("❌ 비밀번호가 틀렸습니다.")
                                else:
                                    row = pw_match.iloc[0]
                                    st.session_state["admin_logged_in"] = True
                                    st.session_state["logged_teacher_id"] = clean_id
                                    st.session_state["logged_teacher_pw"] = clean_pw
                                    st.session_state["teacher_name"] = str(row['교사_성명']).strip()
                                    st.session_state["allowed_subjects"] = [s.strip() for s in str(row['담당_과목']).split(",") if s.strip()]
                                    st.rerun()

    st.markdown("<div class='footer-container'><div class='footer-text'>Designed & Developed by User & Supabase Backend Engine</div></div>", unsafe_allow_html=True)

# =========================================================================
# 🎓 [2단계-A] 학생 대시보드 화면부
# =========================================================================
elif st.session_state["student_logged_in"]:
    st.markdown(f"<h2>수행평가 점수 확인 시스템 <span style='font-size:16px; color:#3b82f6;'>(학생 모드)</span></h2>", unsafe_allow_html=True)
    if st.button("🚪 로그아웃"):
        st.session_state.clear()
        st.rerun()
    st.write(f"👤 접속 이메일: **{st.session_state['logged_student_id']}**")
    st.markdown("---")
    
    if df.empty: st.warning("현재 활성화된 성적 데이터가 존재하지 않습니다.")
    else:
        if st.button("🚀 나의 수행평가 성적 실시간 검증", type="primary", use_container_width=True):
            id_col = "학교 이메일" if "학교 이메일" in df.columns else "school_email"
            res = df[(df[id_col] == st.session_state["logged_student_id"]) & (df['비밀번호'].astype(str) == st.session_state["logged_student_pw"])]
            if not res.empty: show_result_dialog(res.iloc[0].to_dict())
            else: st.error("❌ 데이터를 로드하지 못했습니다.")

# =========================================================================
# 🔒 [2단계-B] 교사 대시보드 화면부 (최고관리자 전용 교사 제어 모듈 이식 완료)
# =========================================================================
elif st.session_state["admin_logged_in"]:
    with st.sidebar:
        st.markdown('<span class="sidebar-title">📋 교사 메뉴</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="user-info">👤 {st.session_state["teacher_name"]} 선생님 접속 중</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        # 기본 메뉴 리스트 구성
        base_menus = ["▶ 학생 조회 현황 모니터링", "▶ 개인별 성적 입력", "▶ 학생 정보 관리", "▶ 성적 전체 일괄 업로드(CSV/Excel)"]
        
        # ⭐ [치트키] 최고관리자(admin) 계정으로 로그인했을 때만 교사 관리 메뉴 노출
        if st.session_state["logged_teacher_id"] == "admin":
            base_menus.append("👑 교사 계정 관리 대장")
            
        menu_selection = st.radio("메뉴 선택", base_menus, label_visibility="collapsed")
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.sidebar.button("🚪 로그아웃", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.markdown(f"<h2>수행평가 점수 확인 시스템 <span style='font-size:14px; color:#64748b;'>[정보 - 교사 관리 관제센터]</span></h2>", unsafe_allow_html=True)
    st.write(f"현재 위치: 교사 모드 > **{menu_selection}**")
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

    # 1. 학생 조회 현황 모니터링
    if menu_selection == "▶ 학생 조회 현황 모니터링":
        with st.container(border=True):
            if df.empty: st.info("데이터베이스가 비어있습니다.")
            else:
                class_options = ["전체 학급 보기"] + [f"{x}반" for x in sorted(df['반'].unique())]
                selected_class = st.selectbox("🎯 필터링할 학급 선택", options=class_options)
                render_df = df.copy()
                if selected_class != "전체 학급 보기": render_df = render_df[render_df['반'].astype(int) == int(selected_class.replace("반",""))]
                st.dataframe(render_df[["반", "번호", "이름", "학교 이메일", "수행평가1", "수행평가2", "수행평가3", "성적조회 횟수", "최종 확인일시"]].fillna("-"), use_container_width=True, hide_index=True)

    # 2. 개인별 성적 입력
    elif menu_selection == "▶ 개인별 성적 입력":
        with st.container(border=True):
            if df.empty: st.info("등록된 학생이 없습니다.")
            else:
                class_opts = ["전체"] + [f"{x}반" for x in sorted(df['반'].unique())]
                sel_c = st.selectbox("👥 학반 필터링", options=class_opts)
                score_cols = ["반", "번호", "이름", "수행평가1", "수행평가2", "수행평가3"]
                filtered_idx = df[df["반"].astype(int) == int(sel_c.replace("반", ""))].index if sel_c != "전체" else df.index
                
                edited_df = st.data_editor(df.loc[filtered_idx, score_cols], use_container_width=True, disabled=["반", "번호", "이름"], hide_index=True)
                if st.button("💾 성적 저장하기", type="primary", use_container_width=True):
                    with st.spinner("저장 중..."):
                        for idx_pos, row_idx in enumerate(filtered_idx):
                            for col in edited_df.columns: df.loc[row_idx, col] = edited_df.iloc[idx_pos][col]
                            supabase.table(student_table).upsert(df.loc[row_idx].to_dict()).execute()
                    st.success("🎉 실시간 동기화 완료!"); st.balloons()

    # 3. 학생 정보 관리
    elif menu_selection == "▶ 학생 정보 관리":
        with st.container(border=True):
            if df.empty: st.info("등록된 학생이 없습니다.")
            else:
                class_opts = ["전체"] + [f"{x}반" for x in sorted(df['반'].unique())]
                sel_c = st.selectbox("👥 학반 필터링", options=class_opts)
                info_cols = ["반", "번호", "이름", "학교 이메일", "비밀번호", "성적조회 횟수", "최종 확인일시"]
                filtered_idx = df[df["반"].astype(int) == int(sel_c.replace("반", ""))].index if sel_c != "전체" else df.index
                
                edited_df = st.data_editor(df.loc[filtered_idx, info_cols], use_container_width=True, disabled=["성적조회 횟수", "최종 확인일시"], hide_index=True)
                b1, b2, b3 = st.columns([3.6, 1.2, 1.2])
                with b2:
                    if st.button("➕ 학생 개별 추가", use_container_width=True): show_add_student_dialog()
                with b3:
                    if st.button("💾 학생 정보 저장", type="primary", use_container_width=True):
                        for idx_pos, row_idx in enumerate(filtered_idx):
                            for col in edited_df.columns: df.loc[row_idx, col] = edited_df.iloc[idx_pos][col]
                            supabase.table(student_table).upsert(df.loc[row_idx].to_dict()).execute()
                        st.success("🎉 인적사항 동기화 성공!"); st.rerun()

    # 4. 성적 전체 일괄 업로드(CSV/Excel)
    elif menu_selection == "▶ 성적 전체 일괄 업로드(CSV/Excel)":
        with st.container(border=True):
            st.markdown("<h3>📥 성적 대장 일괄 마이그레이션</h3>")
            up_f = st.file_uploader("명단 파일 업로드 (.csv / .xlsx)", type=["csv", "xlsx"])
            if up_f:
                df_up = pd.read_csv(up_f) if up_f.name.endswith(".csv") else pd.read_excel(up_f)
                df_up.columns = [c.strip() for c in df_up.columns]
                st.dataframe(df_up.head(3), use_container_width=True, hide_index=True)
                
                if st.button("🚀 클라우드 DB 초기화 및 새 명단 이식 실행", type="primary", use_container_width=True):
                    with st.spinner("DB 마이그레이션 중..."):
                        if not df.empty:
                            for _, r in df.iterrows(): supabase.table(student_table).delete().eq("반", int(r["반"])).eq("번호", int(r["번호"])).execute()
                        for c in ["수행평가1", "수행평가2", "수행평가3", "성적조회 횟수"]:
                            if c not in df_up.columns: df_up[c] = 0
                        df_up["최종 확인일시"] = "-"
                        for record in df_up.to_dict(orient="records"): supabase.table(student_table).insert(record).execute()
                    st.success("🎯 이식 완벽 성공!"); st.balloons(); st.rerun()

    # 👑 5. [신규 이식 기능] 교사 계정 관리 대장 (일괄/개인별 등록 인터페이스 통합 완료)
    elif menu_selection == "👑 교사 계정 관리 대장":
        with st.container(border=True):
            st.markdown("<h3>👑 교사 계정 관리 및 권한 일괄 통제</h3>", unsafe_allow_html=True)
            st.write("각 과목 담당 선생님들의 로그인 계정과 교과 가시성 권한(담당_과목)을 일괄 혹은 개별 제어하는 마스터 관제 탭입니다.")
            st.markdown("<br>", unsafe_allow_html=True)
            
            df_tc = load_db_df(teacher_table)
            
            if df_tc.empty:
                st.info("현재 등록된 일반 교사 계정이 없습니다. 아래 메뉴를 통해 등록해 주세요.")
                # 테이블 구조 강제 가공용 베이스 세팅
                df_tc = pd.DataFrame(columns=["교사_ID", "교사_성명", "비밀번호", "담당_과목"])
            
            # 📝 [기능 1] 교사 명단 그리드 편집 시스템 (수정/삭제)
            st.markdown("#### 🛠️ 교사 권한 그리드 편집기")
            edited_tc_df = st.data_editor(
                df_tc, 
                use_container_width=True, 
                num_rows="dynamic",  # 행 삭제 및 행 추가 UI 자동 활성화
                hide_index=True, 
                key="master_teacher_grid_editor"
            )
            
            tc_col1, tc_col2, tc_col3 = st.columns([3.6, 1.2, 1.2])
            with tc_col2:
                if st.button("👨‍🏫 교사 개별 신규 추가", use_container_width=True, type="secondary"):
                    show_add_teacher_dialog()
            with tc_col3:
                if st.button("💾 교사 정보 원격 저장", use_container_width=True, type="primary"):
                    with st.spinner("클라우드 교사 원격 데이터베이스 덮어쓰기 중..."):
                        # 삭제된 행 추적을 위한 동기화 초기화 처리
                        for _, row in df_tc.iterrows():
                            supabase.table(teacher_table).delete().eq("교사_ID", str(row["교사_ID"])).execute()
                        # 편집된 데이터셋으로 새롭게 전송
                        for record in edited_tc_df.to_dict(orient="records"):
                            if record.get("교사_ID"):
                                supabase.table(teacher_table).upsert(record).execute()
                    st.success("🎉 교과 권한 명단이 Supabase 전용 보안 DB에 최종 세이브되었습니다!")
                    st.rerun()
                    
            st.markdown("<hr style='border: 1px dashed #cbd5e1; margin: 30px 0;'>", unsafe_allow_html=True)
            
            # 📥 [기능 2] 선생님 명단 대량 일괄 등록 (CSV/Excel)
            st.markdown("#### 📥 선생님 명단 대량 일괄 등록 (CSV/Excel)")
            st.caption("인사이동 등으로 많은 선생님들을 한 번에 등록해야 할 때, 아래 파일 업로더를 이용하세요.")
            
            # 템플릿 샘플 버퍼 제작
            tc_template = pd.DataFrame({
                "교사_ID": ["math_01", "eng_02"],
                "교사_성명": ["이수학", "김영어"],
                "비밀번호": ["1234", "1234"],
                "담당_과목": ["수학", "영어, 한문"]
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
                    if st.button("🚀 교사 데이터베이스 초기화 후 일괄 이식 실행", type="primary", use_container_width=True):
                        with st.spinner("교사 원격 인프라 구조 밀어 넣는 중..."):
                            # 기존 교사 데이터 완전 초기화
                            if not df_tc.empty:
                                for _, r in df_tc.iterrows():
                                    supabase.table(teacher_table).delete().eq("교사_ID", str(r["교사_ID"])).execute()
                            # 신규 대량 밀어넣기 연동
                            for record in df_tc_up.to_dict(orient="records"):
                                supabase.table(teacher_table).insert(record).execute()
                        st.success("🎯 전 교사 인적사항 권한 계정이 0.01초 만에 클라우드 DB에 일괄 등록 완료되었습니다!")
                        st.balloons()
                        st.rerun()
