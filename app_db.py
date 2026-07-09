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
# 🎨 [디자인 관통 패치] 브라우저 스크롤 바 차단 및 한 화면 고정 스케일 CSS
# =========================================================================
st.markdown("""
    <style>
        /* 브라우저 전체 우측 스크롤바 원천 차단 및 한 화면 고정 */
        html, body, [data-testid="stAppViewContainer"], .main {
            overflow: hidden !important;
            height: 100vh !important;
        }
        
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        [data-testid="stAppViewContainer"] { margin-left: 0px !important; }
        .stSidebar, section[data-testid="stSidebar"] { min-width: 280px !important; max-width: 280px !important; background-color: #1e293b !important; box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; }
        [data-testid="stSidebar"] .stRadio label p, [data-testid="stSidebar"] .stRadio label span, [data-testid="stSidebar"] .stRadio label div, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[role="radiogroup"] * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; opacity: 1 !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 15px !important; font-weight: 700 !important; line-height: 2.0 !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover * { color: #60a5fa !important; -webkit-text-fill-color: #60a5fa !important; }
        .sidebar-title { font-size: 24px !important; font-weight: 800 !important; margin-bottom: 5px !important; display: block; }
        .user-info { color: #38bdf8 !important; -webkit-text-fill-color: #38bdf8 !important; font-size: 14px !important; font-weight: 600 !important; margin-bottom: 25px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 12px 0 !important; width: 100% !important; display: block !important; margin-bottom: 8px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] *, [data-testid="stSidebar"] button[kind="secondary"] p { color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; font-size: 15px !important; font-weight: 700 !important; }
        
        /* 메인 화면 primary 푸른색 계열 버튼 규격화 */
        div.stButton > button[kind="primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; padding: 8px 16px !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #2563eb !important; }
        div.stButton > button[kind="secondary"] { background-color: #ffffff !important; color: #0f172a !important; font-weight: 700 !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
        
        /* 로그인 화면 수동 왼쪽 여백 제어 */
        div[data-testid="stForm"] div[data-testid="stRadio"] { padding-left: 95px !important; margin-bottom: 25px !important; width: 100% !important; }
        div[data-testid="stForm"] div[role="radiogroup"] { display: flex !important; gap: 35px !important; align-items: center !important; }
        
        div[data-testid="InputInstructions"] { display: none !important; }
        div[data-testid="stSelectbox"] label p, div[data-testid="stTextInput"] label p { font-weight: 800 !important; color: #1e293b !important; font-size: 15px !important; }
        div[data-testid="stTextInput"] > div, div[data-testid="stSelectbox"] > div { background-color: #ffffff !important; border: 1px solid #94a3b8 !important; border-radius: 6px !important; }
        div[data-testid="stTextInput"] input { background-color: #ffffff !important; color: #0f172a !important; padding: 8px 12px !important; }
        div[data-testid="stTextInput"] > div:focus-within, div[data-testid="stSelectbox"] > div:focus-within { border: 2px solid #3b82f6 !important; outline: none !important; }
        
        /* 로그인 박스 외곽 폼 */
        div[data-testid="stForm"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; padding: 45px 40px !important; border-radius: 24px !important; box-shadow: 0 15px 40px rgba(0,0,0,0.06) !important; max-width: 440px !important; margin: 70px auto 0 auto !important; }
        div[data-testid="stForm"] h2 { font-size: 26px !important; text-align: center !important; font-weight: 800 !important; color: #0f172a !important; }
        
        /* 담백한 타이틀 영역 설계 */
        .header-title-main { font-size: 32px !important; font-weight: 800 !important; color: #1e293b !important; letter-spacing: -0.5px !important; margin-bottom: 5px !important; }
        .header-nav-sub { font-size: 15px !important; font-weight: 600 !important; color: #475569 !important; margin-bottom: 25px !important; }

        /* 각 메뉴 제목 밑 구분 라인 디자인 */
        .menu-title-container { border-bottom: 2px solid #cbd5e1 !important; padding-bottom: 12px !important; margin-bottom: 25px !important; }
        .menu-title-text { font-size: 24px !important; font-weight: 800 !important; color: #0f172a !important; margin: 0 !important; }

        .sync-giant-title { font-size: 24px !important; font-weight: 800 !important; color: #0f172a !important; margin-bottom: 10px !important; }

        .stButton button { white-space: nowrap !important; word-break: keep-all !important; }
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
config_table = "subject_configs"

def load_db_df(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

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
# ➕ [다이얼로그 팝업창 모듈]
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
                    st.success("🎉 교사 계정이 활성화되었습니다!")
                    st.rerun()
                except: st.error("❌ 등록 실패")

@st.dialog("➕ 전학생 / 개별 학생 추가")
def show_add_student_dialog():
    st.markdown("새로 명단에 추가할 학생의 기본 정보를 입력해 주세요.")
    with st.form("add_student_form", border=False):
        c1, c2, c3 = st.columns(3)
        with c1: new_ban = st.text_input("반", placeholder="예: 1")
        with c2: new_num = st.text_input("번호", placeholder="예: 15")
        with c3: new_name = st.text_input("이름", placeholder="예: 홍길동")
        
        c4, c5 = st.columns(2)
        with c4: new_email = st.text_input("학교 이메일", placeholder="예: student@school.kr")
        with c5: new_pw = st.text_input("초기 비밀번호", placeholder="예: 1234")
        
        submit_btn = st.form_submit_button("💾 이 학생 명단에 추가하기", use_container_width=True)
        if submit_btn:
            if not new_ban.strip() or not new_num.strip() or not new_name.strip() or not new_email.strip() or not new_pw.strip(): 
                st.error("❌ 모든 항목을 빠짐없이 입력해 주세요.")
            else:
                try:
                    clean_ban = new_ban.strip()
                    clean_num = new_num.strip()
                    clean_name = new_name.strip()
                    clean_email = new_email.strip()
                    clean_pw = new_pw.strip()
                    
                    supabase.table(student_table).upsert({
                        "반": int(clean_ban), 
                        "번호": int(clean_num), 
                        "이름": clean_name, 
                        "학교 이메일": clean_email, 
                        "비밀번호": int(clean_pw), 
                        "수행평가1": 0, "수행평가2": 0, "수행평가3": 0, 
                        "성적조회 횟수": 0, "최종 확인일시": "-"
                    }).execute()
                    st.rerun()
                except ValueError:
                    st.error("❌ '반'과 '번호', '초기 비밀번호'란에는 숫자만 입력할 수 있습니다.")
                except Exception as e:
                    st.error(f"❌ 데이터베이스 통신 실패: {e}")

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_data):
    st.markdown(f"<div><b>{student_data['이름']}</b> 학생의 실시간 성적 내역입니다.</div>", unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("📝 수행평가 1차", f"{int(student_data.get('수행평가1', 0))} 점")
    sc2.metric("📝 수행평가 2차", f"{int(student_data.get('수행평가2', 0))} 점")
    sc3.metric("📝 수행평가 3차", f"{int(student_data.get('수행평가3', 0))} 점")
    if "has_counted" not in st.session_state:
        new_count = int(student_data.get("성적조회 횟수", 0)) + 1
        supabase.table(student_table).upsert({"반": int(student_data["반"]), "번호": int(student_data["번호"]), "성적조회 횟수": new_count, "최종 확인일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).execute()
        st.session_state["has_counted"] = True
    if st.button("닫기", type="secondary", use_container_width=True):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.session_state.clear()
        st.rerun()

# 💡 [내 정보 수정 - Rerun 셧다운 완벽 해결 및 원본 조건부 이식 결정판]
@st.dialog("👤 내 정보 수정")
def show_profile_popup_dialog():
    st.markdown(f"<div>👤 <b>{st.session_state['teacher_name']}</b> 선생님의 계정 정보를 관리합니다.</div><br>", unsafe_allow_html=True)
    edit_mode = st.radio("관리할 항목 선택", ["🔐 비밀번호 변경", "📚 담당과목 변경"], horizontal=True)
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    if "pw_step_unlocked" not in st.session_state: st.session_state["pw_step_unlocked"] = False
    if "pw_save_status" not in st.session_state: st.session_state["pw_save_status"] = "none"
    if "pw_version_key" not in st.session_state: st.session_state["pw_version_key"] = 500

    is_unlocked = st.session_state["pw_step_unlocked"]
    v_key = str(st.session_state["pw_version_key"])

    if edit_mode == "🔐 비밀번호 변경":
        # 현재 비밀번호 입력 필드 (잠금 풀리기 전 검증)
        curr_pw = st.text_input("현재 비밀번호", type="password", placeholder="현재 사용 중인 비밀번호 입력", key="cur_pw_v_" + v_key, disabled=is_unlocked)
        
        if not is_unlocked and curr_pw:
            actual_pw = st.session_state.get("logged_teacher_pw", "").strip()
            if curr_pw.strip() != actual_pw:
                st.markdown("<p style='color: #ef4444; font-size: 14px; font-weight: bold; margin-top: 5px;'>❌ 현재 비밀번호가 일치하지 않습니다.</p>", unsafe_allow_html=True)
            else:
                # 🛠️ [핵심 조치] 여기서 st.rerun()을 때리면 다이얼로그가 파괴되므로, Rerun 없이 상태 메모리만 Unlocked 처리합니다.
                st.session_state["pw_step_unlocked"] = True
                is_unlocked = True

        # 💡 [구조 일체화 복구] 비밀번호가 맞았을 때만 하단에 새 인풋 필드 세트가 닫힘 현상 없이 스르륵 연장 노출됩니다.
        if is_unlocked:
            st.markdown("<p style='color: #10b981; font-size: 14px; font-weight: bold;'>✅ 현재 비밀번호가 확인되었습니다.</p>", unsafe_allow_html=True)
            new_pw = st.text_input("새 비밀번호 입력", type="password", placeholder="새로운 비밀번호 설정", key="new_pw_v_" + v_key)
            new_pw_confirm = st.text_input("새 비밀번호 확인", type="password", placeholder="새로운 비밀번호 다시 입력", key="confirm_pw_v_" + v_key)
            
            # 현재 비밀번호 치고 엔터 눌렀을 때 새 비밀번호 입력창으로 포커스 가이드
            components.html("""
                <script>
                    setTimeout(function() {
                        const parentDoc = window.parent.document;
                        const inputs = parentDoc.querySelectorAll('input[type="password"]');
                        if(inputs.length >= 3 && parentDoc.activeElement === inputs[0]) {
                            inputs[1].focus();
                        }
                    }, 150);
                </script>
            """, height=0, width=0)

            # 알림 메시지 위치 지정 매칭 표출
            if st.session_state["pw_save_status"] == "success":
                st.markdown("<p style='color: #10b981; font-size: 14px; font-weight: bold; margin-top: 5px;'>✓ 비밀번호를 변경하였습니다.</p>", unsafe_allow_html=True)
            elif st.session_state["pw_save_status"] == "fail_mismatch":
                st.markdown("<p style='color: #ef4444; font-size: 14px; font-weight: bold; margin-top: 5px;'>❌ 새 비밀번호가 서로 일치하지 않습니다. 다시 확인해 주세요.</p>", unsafe_allow_html=True)
            elif st.session_state["pw_save_status"] == "fail_empty":
                st.markdown("<p style='color: #ef4444; font-size: 14px; font-weight: bold; margin-top: 5px;'>❌ 새 비밀번호는 공백일 수 없습니다.</p>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1: save_btn = st.button("💾 비밀번호 저장", type="primary", use_container_width=True)
            with col2: close_btn = st.button("닫기", use_container_width=True)
                
            # 💡 [불일치 리런 무단 닫힘 완벽 해결] 틀려도 창 안닫히고 오직 '닫기' 버튼 클릭시에만 세션 청소 후 안전 퇴장
            if close_btn:
                st.session_state["pw_step_unlocked"] = False
                st.session_state["pw_save_status"] = "none"
                st.session_state["pw_version_key"] += 1
                st.rerun()
                
            if save_btn:
                clean_new_pw = new_pw.strip()
                clean_confirm_pw = new_pw_confirm.strip()
                
                if not clean_new_pw:
                    st.session_state["pw_save_status"] = "fail_empty"
                    st.rerun() # 틀렸을 때는 내부 상태값만 업데이트하고 루프를 돌려 팝업창 완전 고정 보장!
                elif clean_new_pw != clean_confirm_pw:
                    st.session_state["pw_save_status"] = "fail_mismatch"
                    st.rerun()
                else:
                    try:
                        teacher_id = st.session_state.get("logged_teacher_id", "")
                        if teacher_id:
                            supabase.table(teacher_table).update({"비밀번호": clean_new_pw}).eq("교사_ID", teacher_id).execute()
                            st.session_state["logged_teacher_pw"] = clean_new_pw
                            st.session_state["pw_save_status"] = "success"
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ 데이터베이스 반영 중 오류가 발생했습니다: {e}")
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("닫기", key="close_pw_outer", use_container_width=True):
                st.session_state["pw_step_unlocked"] = False
                st.session_state["pw_save_status"] = "none"
                st.session_state["pw_version_key"] += 1
                st.rerun()

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
                msg_box_sub.markdown("<p style='color: #10b981; font-size: 13px; font-weight: bold;'>🎉 담당 과목 권한이 임시 조정되었습니다.</p>", unsafe_allow_html=True)

# 세션 제어 상태 초기화
if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "student_logged_in" not in st.session_state: st.session_state["student_logged_in"] = False
if "logged_student_id" not in st.session_state: st.session_state["logged_student_id"] = ""
if "logged_student_pw" not in st.session_state: st.session_state["logged_student_pw"] = ""
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = False
if "logged_teacher_pw" not in st.session_state: st.session_state["logged_teacher_pw"] = ""
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = ""
if "allowed_subjects" not in st.session_state: st.session_state["allowed_subjects"] = []

df = load_db_df(student_table)

# =========================================================================
# 🔓 [1단계] 로그인 시스템
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
        st.markdown(f'<div class="user-info">👤 {st.session_state["teacher_name"]} 선생님 접속 중</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        menus = ["학생 조회 현황 모니터링", "개인별 성적 입력", "학생 정보 관리", "평가 대상 과목 구성", "성적 전체 일괄 업로드(CSV / Excel)"]
        if st.session_state["logged_teacher_id"] == "admin": 
            menus.append("👑 교사 계정 관리 대장")
            
        menu_selection = st.radio("메뉴 선택", menus, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("👤 내 정보 수정", type="secondary", use_container_width=True):
            show_profile_popup_dialog()
        if st.sidebar.button("🚪 로그아웃", type="secondary", use_container_width=True): st.session_state.clear(); st.rerun()

    if not df.empty and "반" in df.columns and "번호" in df.columns: df = df.sort_values(by=["반", "번호"])

    st.markdown(f"""
        <div class="header-title-main">수행평가 점수 확인 시스템</div>
        <div class="header-nav-sub">현재 위치: 교사 모드 > 📁 {menu_selection}</div>
    """, unsafe_allow_html=True)

    # 1번 메뉴: 학생 조회 현황 모니터링
    if menu_selection == "학생 조회 현황 모니터링":
        with st.container(border=True):
            st.markdown('<div class="menu-title-container"><h4 class="menu-title-text">📊 학생별 조회 이력 및 성적 현황 모니터링</h4></div>', unsafe_allow_html=True)
            
            layout_left, layout_right = st.columns([3.5, 6.5])
            
            with layout_left:
                st.markdown("**📂 대상 교과 선택**")
                selected_db_str = st.selectbox("교과 선택", options=["정보 (2학년 / 2026학년도 1학기)"], label_visibility="collapsed", key="mon_sub")
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**🎯 필터링할 학급 선택**")
                class_options = ["전체 학급 보기"]
                if not df.empty and "반" in df.columns: class_options = ["전체 학급 보기"] + [f"{x}반" for x in sorted(df['반'].unique())]
                selected_class = st.selectbox("학급 선택", options=class_options, label_visibility="collapsed", key="mon_class")
                
            with layout_right:
                subject_key = "정보_2학년_2026학년도_1학기"
                item_count, item_titles = get_subject_item_names(subject_key)

                if df.empty: st.info("📢 현재 데이터베이스가 비어있습니다.")
                else:
                    r_df = df.copy()
                    if selected_class != "전체 학급 보기": r_df = r_df[r_df['반'].astype(int) == int(selected_class.replace("반",""))]
                    
                    display_cols = ["반", "번호", "이름", "학교 이메일"]
                    rename_map = {}
                    
                    align_config = {
                        "반": st.column_config.TextColumn(alignment="center"),
                        "번호": st.column_config.TextColumn(alignment="center"),
                        "이름": st.column_config.TextColumn(alignment="center"),
                        "학교 이메일": st.column_config.TextColumn(alignment="center")
                    }
                    
                    for idx in range(item_count):
                        db_col = f"수행평가{idx+1}"
                        view_title = item_titles[idx]
                        if db_col in r_df.columns:
                            display_cols.append(db_col)
                            rename_map[db_col] = view_title
                            align_config[view_title] = st.column_config.NumberColumn(alignment="center")
                            
                    display_cols += ["성적조회 횟수", "최종 확인일시"]
                    align_config["성적조회 횟수"] = st.column_config.NumberColumn(alignment="center")
                    align_config["최종 확인일시"] = st.column_config.TextColumn(alignment="center")
                    
                    final_view_df = r_df[display_cols].rename(columns=rename_map)
                    st.dataframe(final_view_df.fillna("-"), use_container_width=True, hide_index=True, column_config=align_config, height=500)

    # 2번 메뉴: 개인별 성적 데이터 입력
    elif menu_selection == "개인별 성적 입력":
        with st.container(border=True):
            st.markdown('<div class="menu-title-container"><h4 class="menu-title-text">📝 개인별 성적 데이터 입력</h4></div>', unsafe_allow_html=True)
            
            layout_left, layout_right = st.columns([3.5, 6.5])
            
            with layout_left:
                st.markdown("**📂 관리할 교과 선택**")
                selected_db_str = st.selectbox("교과 선택", options=["정보 (2학년 / 2026학년도 1학기)"], label_visibility="collapsed", key="edt_sub")
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**🎯 필터링할 학급 선택**")
                
                class_options_ed = ["전체 학급 보기"]
                if not df.empty and "반" in df.columns: 
                    class_options_ed = ["전체 학급 보기"] + [f"{x}반" for x in sorted(df['반'].unique())]
                selected_class_ed = st.selectbox("학급 선택", options=class_options_ed, label_visibility="collapsed", key="edt_class")
                
                for _ in range(15):
                    st.write("")
                
                score_right_col1, score_right_col2 = st.columns(2)
                with score_right_col2:
                    save_trigger = st.button("💾 성적 저장하기", type="primary", use_container_width=True, key="side_save_score_btn")
                
            with layout_right:
                subject_key = "정보_2학년_2026학년도_1학기"
                item_count, item_titles = get_subject_item_names(subject_key)

                if df.empty: st.info("등록된 학생 데이터가 없습니다.")
                else:
                    f_idx = df[df["반"].astype(int) == int(selected_class_ed.replace("반", ""))].index if selected_class_ed != "전체 학급 보기" else df.index
                    
                    target_cols = ["반", "번호", "이름", "학교 이메일"]
                    rename_map = {}
                    db_cols_ordered = []
                    
                    align_config = {
                        "반": st.column_config.TextColumn(alignment="center"),
                        "번호": st.column_config.TextColumn(alignment="center"),
                        "이름": st.column_config.TextColumn(alignment="center"),
                        "학교 이메일": st.column_config.TextColumn(alignment="center")
                    }
                    
                    for idx in range(item_count):
                        db_col = f"수행평가{idx+1}"
                        db_cols_ordered.append(db_col)
                        target_cols.append(db_col)
                        rename_map[db_col] = item_titles[idx]
                        align_config[item_titles[idx]] = st.column_config.NumberColumn(alignment="center")
                        
                    target_cols += ["성적조회 횟수", "최종 확인일시"]
                    align_config["성적조회 횟수"] = st.column_config.NumberColumn(alignment="center")
                    align_config["최종 확인일시"] = st.column_config.TextColumn(alignment="center")
                    
                    sub_df = df.loc[f_idx, target_cols].rename(columns=rename_map)
                    disabled_cols = ["반", "번호", "이름", "학교 이메일", "성적조회 횟수", "최종 확인일시"]
                    
                    edited_df = st.data_editor(sub_df, use_container_width=True, disabled=disabled_cols, hide_index=True, key="grid_ed_sc", column_config=align_config, height=500)
                    
                    if save_trigger:
                        for _pos, r_idx in enumerate(f_idx):
                            for idx_c, db_col in enumerate(db_cols_ordered):
                                view_title = item_titles[idx_c]
                                df.loc[r_idx, db_col] = edited_df.iloc[_pos][view_title]
                            supabase.table(student_table).upsert(df.loc[r_idx].to_dict()).execute()
                        st.success("🎉 수행 점수가 원격 클라우드 DB에 동기화 완료되었습니다!"); st.rerun()

    # 3번 메뉴: 학생 정보 관리
    elif menu_selection == "학생 정보 관리":
        with st.container(border=True):
            st.markdown('<div class="menu-title-container"><h4 class="menu-title-text">📇 학생 기본 정보 관리</h4></div>', unsafe_allow_html=True)
            
            layout_left, layout_right = st.columns([3.5, 6.5])
            
            with layout_left:
                st.markdown("**📂 관리할 교과 선택**")
                st.selectbox("교과 선택", options=["INFO_2_2026_1"], label_visibility="collapsed", key="inf_sub")
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**👥 학반 필터링**")
                class_opts = ["전체"]
                if not df.empty and "반" in df.columns: class_opts = ["전체"] + [f"{x}반" for x in sorted(df['반'].unique())]
                sel_c = st.selectbox("학반 필터링", options=class_opts, label_visibility="collapsed", key="inf_class")

                for _ in range(15):
                    st.write("")

                info_grid_col1, info_grid_col2 = st.columns(2)
                with info_grid_col1:
                    add_std_trigger = st.button("➕ 학생 개별 추가", use_container_width=True, key="side_add_student_btn")
                with info_grid_col2:
                    save_info_trigger = st.button("💾 학생 정보 저장", type="primary", use_container_width=True, key="side_save_info_btn")

            with layout_right:
                if df.empty:
                    st.info("현재 등록된 학생이 없습니다.")
                    if st.button("➕ 첫 학생 개별 추가", type="primary"): show_add_student_dialog()
                else:
                    f_idx = df[df["반"].astype(int) == int(sel_c.replace("반", ""))].index if sel_c != "전체" else df.index
                    info_cols = ["반", "번호", "이름", "학교 이메일", "비밀번호"]
                    
                    align_config = {
                        "반": st.column_config.NumberColumn(alignment="center", format="%d"),
                        "번호": st.column_config.NumberColumn(alignment="center", format="%d"),
                        "이름": st.column_config.TextColumn(alignment="center"),
                        "학교 이메일": st.column_config.TextColumn(alignment="center"),
                        "비밀번호": st.column_config.NumberColumn(alignment="center", format="%d")
                    }
                    
                    edited_df = st.data_editor(df.loc[f_idx, info_cols], use_container_width=True, hide_index=True, key="grid_ed_inf", column_config=align_config, height=500)
                    
                    if add_std_trigger:
                        show_add_student_dialog()
                    if save_info_trigger:
                        for _pos, r_idx in enumerate(f_idx):
                            for col in edited_df.columns: df.loc[r_idx, col] = edited_df.iloc[_pos][col]
                            supabase.table(student_table).upsert(df.loc[r_idx].to_dict()).execute()
                        st.success("🎉 학생 신상정보 저장 완료!"); st.rerun()

    # 4번 메뉴: 평가 대상 과목 구성
    elif menu_selection == "평가 대상 과목 구성":
        with st.container(border=True):
            st.markdown('<div class="menu-title-container"><h4 class="menu-title-text">🎯 평가 대상 과목 및 항목 관리</h4></div>', unsafe_allow_html=True)
            
            main_col1, main_col2 = st.columns(2)
            
            with main_col1:
                with st.container(border=True):
                    st.markdown('<div class="sync-giant-title">⚙️ 1. 평가 과목 설정</div>', unsafe_allow_html=True)
                    st.caption("과목 설정이 끝나면, 우측에서 수행평가 세부 항목을 구성하세요.")
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    group_map = {"국어": "인문·사회군", "수학": "수리·과학군", "정보": "수리·과학군", "영어": "인문·사회군"}
                    allowed_list = st.session_state.get("allowed_subjects", [])
                    default_sub = "정보"
                    if allowed_list and allowed_list[0] != "마스터":
                        default_sub = allowed_list[0]
                    
                    sub_options = ["국어", "정보", "수학", "영어"]
                    sub_idx = sub_options.index(default_sub) if default_sub in sub_options else 0
                    predicted_group = group_map.get(default_sub, "수리·과학군")
                    group_options = ["인문·사회군", "수리·과학군", "예체능군"]
                    group_idx = group_options.index(predicted_group) if predicted_group in group_options else 0
                    
                    grid_c1, grid_c2 = st.columns(2)
                    with grid_c1:
                        sel_g = st.selectbox("교과군 선택", options=group_options, index=group_idx)
                        final_sub = st.selectbox("세부 과목", options=sub_options, index=sub_idx)
                    with grid_c2:
                        sel_gr = st.selectbox("학년 지정", options=["1학년", "2학년", "3학년"], index=1)
                        sel_se = st.selectbox("학기 선택", options=["학기를 선택하세요.", "2026학년도 1학기", "2026학년도 2학기"], index=1)
                    
                    subject_key = f"{final_sub}_{sel_gr}_{sel_se}".replace(" ", "_")

            with main_col2:
                if sel_se != "학기를 선택하세요.":
                    cfg_df = load_db_df(config_table)
                    db_match = cfg_df[cfg_df["subject_key"] == subject_key] if not cfg_df.empty else pd.DataFrame()
                    
                    if not db_match.empty:
                        saved_info = db_match.iloc[0]
                        init_count = int(saved_info.get("item_count", 3))
                        init_titles = [
                            saved_info.get("item1_name", "수행평가1"), 
                            saved_info.get("item2_name", "수행평가2"), 
                            saved_info.get("item3_name", "수행평가3"),
                            saved_info.get("item4_name", "수행평가4"),
                            saved_info.get("item5_name", "수행평가5")
                        ]
                    else:
                        init_count = 3
                        init_titles = ["수행평가1", "수행평가2", "수행평가3", "수행평가4", "수행평가5"]

                    with st.container(border=True):
                        st.markdown('<div class="sync-giant-title">🎯 2. 수행평가 항목 구성</div>', unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        split_c1, split_c2 = st.columns([1.1, 1.9])
                        
                        with split_c1:
                            item_count = st.selectbox("평가 반영 항목 개수 선택", [1, 2, 3, 4, 5], index=(init_count - 1))
                            
                        with split_c2:
                            st.markdown("<div style='font-size:14px; font-weight:800; color:#1e293b; margin-bottom: 5px;'>📝 각 항목의 제목을 입력하세요.</div>", unsafe_allow_html=True)
                            item_titles = []
                            for i in range(item_count):
                                default_val = init_titles[i] if i < len(init_titles) else f"수행평가_{i+1}"
                                t_in = st.text_input(f"항목 {i+1} 제목", value=default_val, key=f"split_item_title_{i}")
                                item_titles.append(t_in.strip())
                        
                        st.markdown("<hr style='border: 1px dashed #cbd5e1; margin: 20px 0;'>", unsafe_allow_html=True)
                        
                        b_sc1, b_space2 = st.columns([3.8, 1.2])
                        with b_space2:
                            if st.button("💾 과목 설정 저장", type="primary", use_container_width=True):
                                config_record = {
                                    "subject_key": subject_key, "item_count": item_count,
                                    "item1_name": item_titles[0] if item_count >= 1 else "-",
                                    "item2_name": item_titles[1] if item_count >= 2 else "-",
                                    "item3_name": item_titles[2] if item_count >= 3 else "-",
                                    "item4_name": item_titles[3] if item_count >= 4 else "-",
                                    "item5_name": item_titles[4] if item_count >= 5 else "-"
                                }
                                supabase.table(config_table).upsert(config_record).execute()
                                st.success("🎉 수행평가 구조 셋업 세이브 완료!"); st.rerun()
                else:
                    st.markdown(
                        """
                        <div style='border: 2px dashed #cbd5e1; border-radius: 12px; padding: 60px 20px; text-align: center; color: #94a3b8; margin-top: 5px;'>
                            ⬅️ 왼쪽에서 <b>[교과 과목 및 학기]</b>를 선택하시면<br>
                            이 자리에 수행평가 항목을 설정하는 박스가 나타납니다.
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

    # 5번 메뉴: 성적 전체 일괄 업로드
    elif menu_selection == "성적 전체 일괄 업로드(CSV / Excel)":
        with st.container(border=True):
            st.markdown('<div class="menu-title-container"><h4 class="menu-title-text">📥 전체 일괄 성적 대장 CSV 업로드</h4></div>', unsafe_allow_html=True)
            
            upload_left, upload_right = st.columns([3.5, 6.5])
            
            with upload_left:
                st.markdown("**📂 성적 연동 과목 선택**")
                st.selectbox("과목 선택", options=["INFO_2_2026_1"], label_visibility="collapsed", key="csv_upl_sub")
                
                st.markdown("<br>💡 **양식을 다운로드하여 성적을 업로드하세요.**", unsafe_allow_html=True)
                template_df = pd.DataFrame({
                    "반": [1, 1, 2], "번호": [1, 2, 1], "이름": ["홍길동", "이영희", "강백호"],
                    "학교 이메일": ["hgd@school.kr", "lyh@school.kr", "kbh@school.kr"], "비밀번호": [1234, 1234, 1234],
                    "수행평가1": [20, 19, 15], "수행평가2": [18, 20, 15], "수행평가3": [25, 22, 20]
                })
                csv_buffer = template_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 일괄 업로드용 성적 양식(.CSV) 다운로드", data=csv_buffer, file_name="성적일괄업로드_양식.csv", mime="text/csv")
                
                st.markdown("<br>**성적 대장 마스터 CSV 파일 업로드**", unsafe_allow_html=True)
                up_f = st.file_uploader("성적 대장 마스터 CSV 파일 업로드", type=["csv", "xlsx"], label_visibility="collapsed", key="csv_file_box")
                
                for _ in range(3):
                    st.write("")
                
                apply_btn_col1, apply_btn_col2 = st.columns(2)
                with apply_btn_col2:
                    apply_trigger = st.button("🚀 일괄 반영", type="primary", use_container_width=True, key="master_csv_apply_btn")
                
            with upload_right:
                st.markdown("<div style='font-size:15px; font-weight:800; color:#0f172a; padding-bottom:10px;'>📊 업로드 데이터 미리보기</div>", unsafe_allow_html=True)
                if up_f:
                    df_up = pd.read_csv(up_f) if up_f.name.endswith(".csv") else pd.read_excel(up_f)
                    df_up.columns = [c.strip() for c in df_up.columns]
                    
                    preview_align = {}
                    for col_name in df_up.columns:
                        if col_name in ["반", "번호", "비밀번호"] or "수행평가" in col_name:
                            preview_align[col_name] = st.column_config.NumberColumn(alignment="center", format="%d")
                        else:
                            preview_align[col_name] = st.column_config.TextColumn(alignment="center")
                            
                    st.dataframe(df_up, use_container_width=True, hide_index=True, column_config=preview_align, height=450)
