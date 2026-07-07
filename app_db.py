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
# 🔄 [방탄 CSS] 드롭다운, 텍스트 박스, 로그인 버튼 디자인 및 이중 테두리 완벽 제거
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        [data-testid="stAppViewContainer"] { margin-left: 0px !important; }

        /* 🚨 사이드바 배경 및 폭 고정 */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] { 
            min-width: 280px !important; 
            max-width: 280px !important; 
            background-color: #1e293b !important; 
            box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; 
        }
        
        /* 🚨 [사이드바 메뉴 텍스트 순백색 관통] */
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

        /* [사이드바 버튼 예외 처리] */
        [data-testid="stSidebar"] button[kind="secondary"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 12px 0 !important; width: 100% !important; display: block !important; margin-bottom: 8px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] *, [data-testid="stSidebar"] button[kind="secondary"] p { color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; font-size: 15px !important; font-weight: 700 !important; }
        [data-testid="stSidebar"] button[kind="secondary"]:hover { background-color: #f8fafc !important; border-color: #3b82f6 !important; }

        /* 메인 화면 및 폼 일반 버튼 디자인 */
        div.stButton > button[kind="primary"], button[data-testid="baseButton-primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2) !important; }
        div.stButton > button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover { background-color: #2563eb !important; }
        div.stButton > button[kind="secondary"], button[data-testid="baseButton-secondary"] { background-color: #ffffff !important; color: #0f172a !important; font-weight: 700 !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
        div.stButton > button[kind="secondary"]:hover, button[data-testid="baseButton-secondary"]:hover { background-color: #f8fafc !important; border-color: #3b82f6 !important; color: #2563eb !important; }

        /* 로그인 폼 제출용 버튼 디자인 강제 지정 */
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

        /* 팝업 다이얼로그 전용 버튼 */
        [data-testid="stDialog"] button[kind="primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 800 !important; border: none !important; border-radius: 6px !important; padding: 12px 0 !important; font-size: 15px !important; width: 100% !important; }
        [data-testid="stDialog"] button[kind="secondary"] { background-color: #64748b !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; padding: 12px 0 !important; font-size: 15px !important; width: 100% !important; }

        div[data-testid="InputInstructions"] { display: none !important; }

        /* 라벨 제목 굵게 */
        div[data-testid="stSelectbox"] label p, div[data-testid="stTextInput"] label p { font-weight: 800 !important; color: #1e293b !important; font-size: 15px !important; }

        /* 드롭다운 & 텍스트 박스 기본 상태 */
        div[data-testid="stTextInput"] > div,
        div[data-testid="stTextInput"] [data-baseweb="input"],
        div[data-testid="stSelectbox"] > div[data-baseweb="select"],
        div[data-testid="stSelectbox"] > div { 
            background-color: #ffffff !important; 
            border: 1px solid #94a3b8 !important; 
            border-radius: 6px !important; 
            transition: all 0.2s ease-in-out !important; 
            box-shadow: none !important;
        }

        div[data-testid="stTextInput"] input { 
            background-color: #ffffff !important; 
            color: #0f172a !important;
            padding: 8px 12px !important;
            border-radius: 6px !important;
            box-shadow: none !important;
        }
        
        /* 이중 테두리 중첩 현상 제거 */
        div[data-testid="stTextInput"] > div:focus-within,
        div[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
        div[data-testid="stSelectbox"] > div:focus-within,
        div[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within,
        div[data-testid="stTextInput"] input:focus {
            border: 2px solid #3b82f6 !important;
            outline: none !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
            -webkit-box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
        }

        /* 로그인 박스 */
        div[data-testid="stForm"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; padding: 45px 40px 45px 40px !important; border-radius: 24px !important; box-shadow: 0 15px 40px rgba(0,0,0,0.06) !important; max-width: 440px !important; margin: 70px auto 0 auto !important; }
        div[data-testid="stForm"] h2 { font-size: 26px !important; white-space: nowrap !important; text-align: center !important; margin: 0 auto 20px auto !important; font-weight: 800 !important; color: #0f172a !important; }
        div[data-testid="stForm"] div[data-testid="stRadio"] { padding-left: 95px !important; margin-bottom: 25px !important; width: 100% !important; }
        div[data-testid="stForm"] div[role="radiogroup"] { display: flex !important; gap: 35px !important; align-items: center !important; }
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

# 고정으로 사용할 메인 성적 테이블 강제 지정
current_table = "st_info_2_2026_1"

# 데이터 로드 헬퍼 함수
def load_supabase_df():
    try:
        response = supabase.table(current_table).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        return pd.DataFrame()

# 데이터 저장 및 업서트 헬퍼 함수
def save_upsert_record(record):
    try:
        supabase.table(current_table).upsert(record).execute()
        return True
    except:
        return False

# =========================================================================
# 🗂️ [마스터 기본 교과 데이터 구조 설정]
# =========================================================================
def load_master_subjects():
    return {
        "인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"], 
        "수리·과학군": ["수학", "과학", "기술·가정", "정보"], 
        "예체능군": ["음악", "미술", "체육"]
    }

# =========================================================================
# 👤 [다이얼로그 팝업창] 교사 개인 정보 수정창
# =========================================================================
@st.dialog("👤 내 정보 수정")
def show_profile_popup_dialog():
    st.markdown(f"<div>👤 <b>{st.session_state['teacher_name']}</b> 선생님의 계정 정보를 관리합니다.</div><br>", unsafe_allow_html=True)
    edit_mode = st.radio("관리할 항목 선택", ["🔐 비밀번호 변경", "📚 담당과목 변경"], horizontal=True)
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    # 1. 교사용 연동 비밀번호 수정
    if edit_mode == "🔐 비밀번호 변경":
        if "pw_step_unlocked" not in st.session_state: st.session_state["pw_step_unlocked"] = False
        is_unlocked = st.session_state["pw_step_unlocked"]

        curr_pw = st.text_input("현재 비밀번호", type="password", placeholder="현재 사용 중인 비밀번호 입력", key="curr_pw_input_field", disabled=is_unlocked)
        
        if not is_unlocked and curr_pw:
            actual_pw = st.session_state.get("logged_teacher_pw", "")
            if curr_pw != actual_pw:
                st.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold; margin-top: -10px;'>❌ 현재 비밀번호가 일치하지 않습니다.</p>", unsafe_allow_html=True)
            else:
                st.session_state["pw_step_unlocked"] = True
                is_unlocked = True

        if is_unlocked:
            st.markdown("<p style='color: #10b981; font-size: 13px; font-weight: bold;'>✅ 현재 비밀번호가 확인되었습니다. 변경할 새 비밀번호를 입력하세요.</p>", unsafe_allow_html=True)
            new_pw = st.text_input("새 비밀번호 입력", type="password", placeholder="새로운 비밀번호")
            new_pw_confirm = st.text_input("새 비밀번호 확인", type="password", placeholder="새로운 비밀번호 다시 입력")
            
            components.html("""<script>setTimeout(function() { const inputs = window.parent.document.querySelectorAll('input[type="password"]:not([disabled])'); if (inputs.length > 0) { inputs[0].focus(); } }, 150);</script>""", height=0, width=0)

            msg_box = st.empty()
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1: save_btn = st.button("💾 비밀번호 저장", type="primary", use_container_width=True)
            with col2:
                if st.button("닫기", type="secondary", use_container_width=True):
                    st.session_state["pw_step_unlocked"] = False
                    st.rerun()
                    
            if save_btn:
                if not new_pw or new_pw != new_pw_confirm: msg_box.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold;'>❌ 새 비밀번호가 비어있거나 서로 일치하지 않습니다.</p>", unsafe_allow_html=True)
                elif new_pw == st.session_state.get("logged_teacher_pw", ""): msg_box.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold;'>❌ 현재 사용 중인 비밀번호와 동일합니다.</p>", unsafe_allow_html=True)
                else:
                    st.session_state["logged_teacher_pw"] = new_pw
                    msg_box.markdown("<p style='color: #10b981; font-size: 13px; font-weight: bold;'>🎉 메모리 내 세션 암호가 성공적으로 임시 업데이트되었습니다.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("닫기", type="secondary", use_container_width=True):
                st.session_state["pw_step_unlocked"] = False
                st.rerun()

    # 2. 교과 권한 가시성 수정
    elif edit_mode == "📚 담당과목 변경":
        curr_subs_str = ", ".join(st.session_state.get("allowed_subjects", []))
        new_subs_str = st.text_input("담당 과목 변경 (여러 과목은 콤마[,]로 분리)", value=curr_subs_str, placeholder="예: 정보, 수학")
        msg_box_sub = st.empty()
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1: save_sub_btn = st.button("💾 과목 저장하기", type="primary", use_container_width=True)
        with col2:
            if st.button("닫기", type="secondary", use_container_width=True): st.rerun()
                
        if save_sub_btn:
            if not new_subs_str.strip(): msg_box_sub.markdown("<p style='color: #ef4444; font-size: 13px; font-weight: bold;'>❌ 담당 과목을 최소 1개 이상 입력하세요.</p>", unsafe_allow_html=True)
            else:
                st.session_state["allowed_subjects"] = [s.strip() for s in new_subs_str.split(",") if s.strip()]
                msg_box_sub.markdown("<p style='color: #10b981; font-size: 13px; font-weight: bold;'>🎉 담당 교과 가시성 권한이 즉시 재지정되었습니다!</p>", unsafe_allow_html=True)

# =========================================================================
# ➕ [다이얼로그 팝업창] 전학생 추가 기능 (DB Upsert 연동)
# =========================================================================
@st.dialog("➕ 전학생 / 개별 학생 추가")
def show_add_student_dialog(current_df):
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
                    "반": int(new_ban),
                    "번호": int(new_num),
                    "이름": new_name.strip(),
                    "학교 이메일": new_email.strip(),
                    "비밀번호": int(new_pw),
                    "수행평가1": 0, "수행평가2": 0, "수행평가3": 0,
                    "성적조회 횟수": 0,
                    "최종 확인일시": "-"
                }
                if save_upsert_record(new_record):
                    st.success("🎉 새로운 학생 데이터가 Supabase DB에 실시간 주입되었습니다!")
                    st.rerun()
                else: st.error("❌ DB 데이터 이식에 실패했습니다.")

# =========================================================================
# 🎉 [다이얼로그 팝업창] 학생 1인 맞춤형 성적 정보 표출
# =========================================================================
@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_data, current_df):
    st.markdown(f"<div><b>{student_data['이름']}</b> 학생의 실시간 성적 내역입니다.</div>", unsafe_allow_html=True)
    
    # 예쁘게 가공된 카드 형태 스코어보드 표출
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("📝 수행평가 1차", f"{int(student_data['수행평가1'])} 점")
    sc2.metric("📝 수행평가 2차", f"{int(student_data['수행평가2'])} 점")
    sc3.metric("📝 수행평가 3차", f"{int(student_data['수행평가3'])} 점")
    
    if "has_counted" not in st.session_state:
        # 실시간 로그 및 트랙 수치 카운팅 누적
        new_count = int(student_data.get("성적조회 횟수", 0)) + 1
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        supabase.table(current_table).upsert({
            "반": int(student_data["반"]),
            "번호": int(student_data["번호"]),
            "성적조회 횟수": new_count,
            "최종 확인일시": now_str
        }).execute()
        st.session_state["has_counted"] = True
        
    if st.button("닫기", type="secondary", use_container_width=True):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.session_state.clear()
        st.rerun()

# =========================================================================
# ⚙️ [세션 제어 상태 초기화]
# =========================================================================
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "student_logged_in" not in st.session_state: st.session_state["student_logged_in"] = False
if "logged_student_id" not in st.session_state: st.session_state["logged_student_id"] = ""
if "logged_student_pw" not in st.session_state: st.session_state["logged_student_pw"] = ""
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = ""
if "logged_teacher_pw" not in st.session_state: st.session_state["logged_teacher_pw"] = ""
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = ""
if "allowed_subjects" not in st.session_state: st.session_state["allowed_subjects"] = []

SUBJECT_MAP = load_master_subjects()
df = load_supabase_df()

# =========================================================================
# 🔓 [1단계] 클린 통합 로그인 시스템 (기존 app.py 기능 완전 통합 계승)
# =========================================================================
if not st.session_state["admin_logged_in"] and not st.session_state["student_logged_in"]:
    with st.container():
        with st.form("master_unified_form"):
            st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
            
            login_mode = st.radio("접속 모드", ["학생", "교사"], horizontal=True, label_visibility="collapsed", key="pure_system_role_radio")
            user_id_input = st.text_input("ID", placeholder="ID를 입력하세요 (교사: admin / 학생: 학교 이메일)", label_visibility="collapsed", key="pure_user_id_field")
            user_pw_input = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요 (초기: 1234)", label_visibility="collapsed", key="pure_user_pw_field")
            
            b_col1, b_col2, b_col3 = st.columns([1.0, 1.8, 1.0])
            with b_col2: submit_active = st.form_submit_button("로그인", use_container_width=True)
            
            if submit_active:
                clean_id = str(user_id_input).strip()
                clean_pw = str(user_pw_input).strip()
                
                if login_mode == "학생":
                    if not clean_id or not clean_pw: st.error("❌ 학생 ID(이메일)와 비밀번호를 모두 입력하세요.")
                    elif df.empty: st.error("❌ 현재 백엔드 데이터베이스에 개설된 학생 성적 테이블이 존재하지 않습니다.")
                    else:
                        # 반, 번호 대신 학교 이메일을 기준으로 1인 인증 처리 진행
                        id_col = "학교 이메일" if "학교 이메일" in df.columns else ("school_email" if "school_email" in df.columns else None)
                        if not id_col or "비밀번호" not in df.columns: st.error("❌ DB의 열 이름 구성이 올바르지 않습니다.")
                        else:
                            id_match = df[df[id_col] == clean_id]
                            if id_match.empty: st.error("❌ 등록되지 않은 학생 정보(이메일)입니다.")
                            else:
                                pw_match = id_match[id_match["비밀번호"].astype(str) == clean_pw]
                                if pw_match.empty: st.error("❌ 비밀번호가 일치하지 않습니다.")
                                else:
                                    st.session_state["student_logged_in"] = True
                                    st.session_state["logged_student_id"] = clean_id
                                    st.session_state["logged_student_pw"] = clean_pw
                                    st.rerun()
                                            
                elif login_mode == "교사":
                    # 마스터 고정 관리자 권한
                    if clean_id == "admin" and clean_pw == "1234":
                        st.session_state["admin_logged_in"] = True
                        st.session_state["logged_teacher_id"] = "admin"
                        st.session_state["logged_teacher_pw"] = "1234"
                        st.session_state["teacher_name"] = "최고관리자"
                        st.session_state["allowed_subjects"] = ["정보", "수학"]
                        st.rerun()
                    else:
                        st.error("❌ 교사 로그인 정보가 틀렸습니다. (마스터 계정: admin / 1234)")

    st.markdown("<div class='footer-container'><div class='footer-text'>Designed & Developed by User & Supabase Backend Engine</div></div>", unsafe_allow_html=True)

# =========================================================================
# 🎓 [2단계-A] 학생 대시보드 화면부
# =========================================================================
elif st.session_state["student_logged_in"]:
    st.markdown(f"<h2>수행평가 점수 확인 시스템 <span style='font-size:16px; color:#3b82f6;'>(학생 모드)</span></h2>", unsafe_allow_html=True)
    if st.button("🚪 로그아웃", key="student_logout_btn"):
        st.session_state.clear()
        st.rerun()
    st.write(f"👤 접속 이메일: **{st.session_state['logged_student_id']}**")
    st.markdown("---")
    
    if df.empty: st.warning("현재 평가 데이터베이스에 활성화된 과목 파티션이 존재하지 않습니다.")
    else:
        st.info("💡 본인 인증이 완료되었습니다. 아래 버튼을 누르면 실시간 수행평가 상세 점수가 호출됩니다.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 나의 수행평가 성적 실시간 검증", type="primary", use_container_width=True, key="student_verify_score_btn"):
            st_id = st.session_state["logged_student_id"]
            st_pw = st.session_state["logged_student_pw"]
            id_col = "학교 이메일" if "학교 이메일" in df.columns else "school_email"
            
            res = df[(df[id_col] == st_id) & (df['비밀번호'].astype(str) == st_pw)]
            if not res.empty:
                show_result_dialog(res.iloc[0].to_dict(), df)
            else: st.error("❌ 일치하는 성적 데이터가 없습니다.")

# =========================================================================
# 🔒 [2단계-B] 교사 대시보드 화면부 (Supabase 통합 고속 제어 모듈)
# =========================================================================
elif st.session_state["admin_logged_in"]:
    with st.sidebar:
        st.markdown('<span class="sidebar-title">📋 교사 메뉴</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="user-info">👤 {st.session_state["teacher_name"]} 선생님 접속 중</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        menu_selection = st.radio("메뉴 선택", [
            "▶ 학생 조회 현황 모니터링", 
            "▶ 개인별 성적 입력", 
            "▶ 학생 정보 관리", 
            "▶ 평가 대상 과목 구성", 
            "▶ 성적 전체 일괄 업로드(CSV/Excel)"
        ], label_visibility="collapsed", key="teacher_sidebar_unique_menu_selector_2026")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.button("👤 내 정보 수정", type="secondary", use_container_width=True, key="open_profile_popup_btn"):
            st.session_state["pw_step_unlocked"] = False
            show_profile_popup_dialog()
            
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        
        if st.button("🚪 로그아웃", type="secondary", use_container_width=True, key="teacher_logout_btn_unique"):
            st.session_state.clear()
            st.rerun()

    st.markdown(f"<h2>수행평가 점수 확인 시스템 <span style='font-size:14px; color:#64748b;'>[정보 - 2학년 1학기]</span></h2>", unsafe_allow_html=True)
    st.write(f"현재 위치: 교사 모드 > **{menu_selection}**")
    st.markdown("<div style='text-align:center; height: 5px;'></div>", unsafe_allow_html=True)

    # 데이터 명단 정렬 자동화
    if not df.empty and "반" in df.columns and "번호" in df.columns:
        df = df.sort_values(by=["반", "번호"])

    # 1. 학생 조회 현황 모니터링
    if menu_selection == "▶ 학생 조회 현황 모니터링":
        with st.container(border=True):
            st.markdown("<h3>📊 학생별 조회 이력 및 성적 현황 모니터링</h3>", unsafe_allow_html=True)
            if df.empty: st.info("데이터베이스가 비어있습니다. 성적을 먼저 업로드해 주세요.")
            else:
                class_options = ["전체 학급 보기"] + [f"{x}반" for x in sorted(df['반'].unique())]
                selected_class = st.selectbox("🎯 필터링할 학급 선택", options=class_options, key="t_class_select_1_unique")
                
                render_df = df.copy()
                if selected_class != "전체 학급 보기":
                    render_df = render_df[render_df['반'].astype(int) == int(selected_class.replace("반",""))]
                
                display_cols = ["반", "번호", "이름", "학교 이메일", "수행평가1", "수행평가2", "수행평가3", "성적조회 횟수", "최종 확인일시"]
                st.dataframe(render_df[[c for c in display_cols if c in render_df.columns]].fillna("-"), use_container_width=True, hide_index=True)

    # 2. 개인별 성적 입력 (Supabase Upsert 연동)
    elif menu_selection == "▶ 개인별 성적 입력":
        with st.container(border=True):
            st.markdown("<h3>📝 개인별 성적 데이터 입력</h3>", unsafe_allow_html=True)
            if df.empty: st.info("등록된 학생이 없습니다.")
            else:
                class_options_ed = ["전체"] + [f"{x}반" for x in sorted(df['반'].unique())]
                selected_class_ed = st.selectbox("👥 학반 필터링", options=class_options_ed, key="t_class_select_2_unique")
                
                score_cols = ["반", "번호", "이름", "수행평가1", "수행평가2", "수행평가3"]
                
                if selected_class_ed != "전체":
                    filtered_idx = df[df["반"].astype(int) == int(selected_class_ed.replace("반", ""))].index
                    edit_target_df = df.loc[filtered_idx, score_cols]
                else:
                    filtered_idx = df.index
                    edit_target_df = df[score_cols]
                    
                edited_df = st.data_editor(edit_target_df, use_container_width=True, disabled=["반", "번호", "이름"], hide_index=True, key="t_score_editor_grid")
                st.markdown("<br>", unsafe_allow_html=True)
                
                bc1, bc2 = st.columns([4.2, 1.2])
                with bc2:
                    if st.button("💾 성적 저장하기", use_container_width=True, type="primary"):
                        with st.spinner("수파베이스 DB에 실시간 덮어쓰기 중..."):
                            for idx_pos, row_idx in enumerate(filtered_idx):
                                for col in edited_df.columns: df.loc[row_idx, col] = edited_df.iloc[idx_pos][col]
                                # 한 행씩 업서트 원격 반영
                                supabase.table(current_table).upsert(df.loc[row_idx].to_dict()).execute()
                        st.success("🎉 성적이 0.01초 만에 데이터베이스에 반영되었습니다!")
                        st.balloons()

    # 3. 학생 정보 관리 (전학생 및 비밀번호 제어부)
    elif menu_selection == "▶ 학생 정보 관리":
        with st.container(border=True):
            st.markdown("<h3>📇 학생 기본 정보 관리</h3>", unsafe_allow_html=True)
            if df.empty: st.info("등록된 학생이 없습니다.")
            else:
                class_options_info = ["전체"] + [f"{x}반" for x in sorted(df['반'].unique())]
                selected_class_info = st.selectbox("👥 학반 필터링", options=class_options_info, key="t_class_select_info_unique")
                
                info_cols = ["반", "번호", "이름", "학교 이메일", "비밀번호", "성적조회 횟수", "최종 확인일시"]
                
                if selected_class_info != "전체":
                    filtered_idx = df[df["반"].astype(int) == int(selected_class_info.replace("반", ""))].index
                    edit_target_df = df.loc[filtered_idx, info_cols]
                else:
                    filtered_idx = df.index
                    edit_target_df = df[info_cols]
                    
                edited_df = st.data_editor(edit_target_df, use_container_width=True, disabled=["성적조회 횟수", "최종 확인일시"], hide_index=True, key="t_info_editor_grid")
                st.markdown("<br>", unsafe_allow_html=True)
                
                bc1, bc2, bc3 = st.columns([3.6, 1.2, 1.2])
                with bc2:
                    if st.button("➕ 학생 개별 추가", use_container_width=True, type="secondary"):
                        show_add_student_dialog(df)
                with bc3:
                    if st.button("💾 학생 정보 저장", use_container_width=True, type="primary"):
                        with st.spinner("인적사항 동기화 중..."):
                            for idx_pos, row_idx in enumerate(filtered_idx):
                                for col in edited_df.columns: df.loc[row_idx, col] = edited_df.iloc[idx_pos][col]
                                supabase.table(current_table).upsert(df.loc[row_idx].to_dict()).execute()
                        st.success("🎉 학생 정보 수정사항이 정상 연동되었습니다!")
                        st.rerun()

    # 4. 평가 대상 과목 구성 (UI 구조 계승 및 안내 기능 고정)
    elif menu_selection == "▶ 평가 대상 과목 구성":
        st.markdown("<br>", unsafe_allow_html=True)
        main_col1, main_col2 = st.columns(2)
        
        with main_col1:
            with st.container(border=True):
                st.markdown("<h3>⚙️ 1. 평가 과목 설정</h3>", unsafe_allow_html=True)
                st.caption("현재 지정된 Supabase 연동 정보 파티션을 관리합니다.")
                
                sel_g = st.selectbox("교과군 선택", options=["수리·과학군", "인문·사회군", "예체능군"])
                final_sub = st.selectbox("세부 과목", options=SUBJECT_MAP.get(sel_g, ["정보"]))
                sel_gr = st.selectbox("학년 지정", options=["2학년", "1학년", "3학년"])
                sel_se = st.selectbox("학기 선택", options=["2026학년도 1학기", "2026학년도 2학기"])
                
        with main_col2:
            with st.container(border=True):
                st.markdown("<h3>🎯 2. 수행평가 항목 구성</h3>", unsafe_allow_html=True)
                st.write(f"현재 선택 교과명: **{final_sub} ({sel_gr} / {sel_se})**")
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.success(f"🟢 연결 성공: 현재 지정된 `{current_table}` 테이블 인프라에 다이렉트 통신 중입니다.")
                st.caption("※ Streamlit 고속 버전 아키텍처는 지정 테이블에 고정 연동되어 가동됩니다.")

    # 5. 성적 전체 일괄 업로드 (CSV/Excel 엑셀 이식 모듈 완전 통합)
    elif menu_selection == "▶ 성적 전체 일괄 업로드(CSV/Excel)":
        with st.container(border=True):
            st.markdown("<h3>📥 전체 일괄 성적 대장 파일 업로드 및 클라우드 이식</h3>", unsafe_allow_html=True)
            st.write("새 명단 파일(.csv / .xlsx)을 업로드하면 기존 DB 데이터를 싹 초기화하고 신규 데이터셋으로 초고속 마이그레이션을 실행합니다.")
            
            # 템플릿 양식 파일 가공 및 제공
            template_df = pd.DataFrame({
                "반": [1, 1, 2], "번호": [1, 2, 1], "이름": ["홍길동", "이영희", "강백호"],
                "학교 이메일": ["hgd@school.kr", "lyh@school.kr", "kbh@school.kr"], "비밀번호": [1234, 1234, 1234],
                "수행평가1": [20, 19, 15], "수행평가2": [18, 20, 15], "수행평가3": [25, 22, 20]
            })
            csv_buffer = template_df.to_csv(index=False).encode('utf-8-sig') 
            
            st.download_button(
                label="📥 일괄 업로드용 성적 샘플 양식(.CSV) 다운로드",
                data=csv_buffer, file_name="성적일괄업로드_양식.csv", mime="text/csv", type="secondary"
            )
            st.markdown("<hr style='border: 1px dashed #cbd5e1; margin: 20px 0;'>", unsafe_allow_html=True)
            
            up_f = st.file_uploader("성적 대장 마스터 CSV 또는 Excel 파일 업로드", type=["csv", "xlsx"])
            
            if up_f:
                # 확장자에 따른 유연한 판독 엔진 작동
                if up_f.name.endswith(".csv"):
                    try: df_up = pd.read_csv(up_f, encoding='utf-8-sig')
                    except: df_up = pd.read_csv(up_f, encoding='cp949')
                else:
                    df_up = pd.read_excel(up_f)
                    
                df_up.columns = [c.strip() for c in df_up.columns]
                st.markdown("#### 🔍 업로드 파일 구조 판독 미리보기")
                st.dataframe(df_up.head(3), use_container_width=True, hide_index=True)
                
                required_cols = ["반", "번호", "이름", "학교 이메일", "비밀번호"]
                missing = [c for c in required_cols if c not in df_up.columns]
                
                if missing:
                    st.error(f"❌ 서식 불일치: 필수 열이 누락되었습니다. 양식을 다시 확인해 주세요: {missing}")
                else:
                    if st.button("🚀 클라우드 DB 원격 초기화 및 새 명단 이식 실행", type="primary", use_container_width=True):
                        with st.spinner("기존 데이터 청소 및 신규 명단 이식 중..."):
                            # 1. 기존 DB 행 전체 삭제
                            if not df.empty:
                                for _, row in df.iterrows():
                                    supabase.table(current_table).delete().eq("반", int(row["반"])).eq("번호", int(row["번호"])).execute()
                            
                            # 2. 업로드 명단 기본 보정값 채우기 및 Insert 전송
                            for c in ["수행평가1", "수행평가2", "수행평가3", "성적조회 횟수"]:
                                if c not in df_up.columns: df_up[c] = 0
                            df_up["최종 확인일시"] = "-"
                            
                            upload_records = df_up.to_dict(orient="records")
                            for record in upload_records:
                                # NaN 결측치 결함 처리 방어 코드
                                for k, v in record.items():
                                    if pd.isna(v): record[k] = "-" if isinstance(v, str) else 0
                                supabase.table(current_table).insert(record).execute()
                                
                        st.success("🎯 Supabase 클라우드 DB 초기화 및 성적 마이그레이션이 완벽하게 완료되었습니다!")
                        st.balloons()
                        st.rerun()
