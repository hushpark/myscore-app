import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import time
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
        
        /* 사이드바 구성 패치 */
        .stSidebar, section[data-testid="stSidebar"] { min-width: 280px !important; max-width: 280px !important; background-color: #1e293b !important; box-shadow: 4px 0 15px rgba(0,0,0,0.1) !important; }
        [data-testid="stSidebar"] .stRadio label p, [data-testid="stSidebar"] .stRadio label span, [data-testid="stSidebar"] .stRadio label div, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[role="radiogroup"] * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; opacity: 1 !important; }
        
        /* 메뉴 폰트 크기 큰 상태(17px) 유지 및 상단 정렬 복귀 */
        [data-testid="stSidebar"] div[role="radiogroup"] { margin-top: 0px !important; } 
        [data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 17px !important; font-weight: 700 !important; line-height: 2.3 !important; } 
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover * { color: #60a5fa !important; -webkit-text-fill-color: #60a5fa !important; }
        
        /* 메뉴들과 최하단 버튼 사이의 공백 밀기 장치 */
        .sidebar-spacer {
            height: 120px !important;
        }
        
        .sidebar-title { font-size: 24px !important; margin-bottom: 5px !important; display: block; }
        .user-info { color: #38bdf8 !important; -webkit-text-fill-color: #38bdf8 !important; font-size: 14px !important; font-weight: 600 !important; margin-bottom: 25px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 12px 0 !important; width: 100% !important; display: block !important; margin-bottom: 8px !important; }
        [data-testid="stSidebar"] button[kind="secondary"] *, [data-testid="stSidebar"] button[kind="secondary"] p { color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; font-size: 15px !important; font-weight: 700 !important; }
        
        /* 💾 [핵심 피드백 반영] 마스터 푸른색 계열 버튼 규격화 및 빨간색 필터링 원천 타파 */
        div.stButton > button[kind="primary"], 
        button[data-testid="stFormSubmitButton"],
        div.stForm [data-testid="stFormSubmitButton"] > button { 
            background-color: #3b82f6 !important; 
            color: #ffffff !important; 
            font-weight: 700 !important; 
            border: none !important; 
            border-radius: 6px !important; 
            padding: 8px 16px !important; 
        }
        div.stButton > button[kind="primary"]:hover, 
        button[data-testid="stFormSubmitButton"]:hover,
        div.stForm [data-testid="stFormSubmitButton"] > button:hover { 
            background-color: #2563eb !important; 
        }
        div.stButton > button[kind="secondary"] { background-color: #ffffff !important; color: #0f172a !important; font-weight: 700 !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
        
        /* 로그인 화면 전용 스타일 */
        div[data-testid="stForm"] div[data-testid="stRadio"] { padding-left: 95px !important; margin-bottom: 25px !important; width: 100% !important; }
        div[data-testid="stForm"] div[role="radiogroup"] { display: flex !important; gap: 35px !important; align-items: center !important; }
        div[data-testid="stForm"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; padding: 45px 40px !important; border-radius: 24px !important; max-width: 440px !important; margin: 70px auto 0 auto !important; box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important; }
        div[data-testid="stForm"] h2 { font-size: 26px !important; text-align: center !important; font-weight: 800 !important; color: #0f172a !important; }
        
        /* 📱 학생 스마트폰 사각형 가두리 독립 스타일 */
        .student-mobile-container {
            max-width: 440px !important;
            margin: 60px auto 0 auto !important;
            padding: 10px !important;
        }
        .student-mobile-card { 
            background-color: #ffffff !important; 
            border: 1px solid #cbd5e1 !important; 
            padding: 40px 35px !important; 
            border-radius: 24px !important; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important; 
            width: 100% !important;
            box-sizing: border-box !important;
        }
        .student-mobile-card h2 { 
            font-size: 24px !important; 
            text-align: center !important; 
            font-weight: 800 !important; 
            color: #0f172a !important; 
            margin-bottom: 25px !important; 
            letter-spacing: -0.5px !important;
        }
        
        div[data-testid="InputInstructions"] { display: none !important; }
        div[data-testid="stSelectbox"] label p, div[data-testid="stTextInput"] label p { font-weight: 800 !important; color: #1e293b !important; font-size: 15px !important; }
        div[data-testid="stTextInput"] > div, div[data-testid="stSelectbox"] > div { background-color: #ffffff !important; border: 1px solid #94a3b8 !important; border-radius: 6px !important; }
        div[data-testid="stTextInput"] input { background-color: #ffffff !important; color: #0f172a !important; padding: 8px 12px !important; }
        div[data-testid="stTextInput"] > div:focus-within, div[data-testid="stSelectbox"] > div:focus-within { border: 2px solid #3b82f6 !important; outline: none !important; }
        
        /* 타이틀 영역 구조 */
        .header-title-main { font-size: 32px !important; font-weight: 800 !important; color: #1e293b !important; letter-spacing: -0.5px !important; margin-bottom: 5px !important; }
        .header-nav-sub { font-size: 18px !important; font-weight: 700 !important; color: #1e293b !important; margin-bottom: 25px !important; }
        .menu-title-container { border-bottom: 2px solid #cbd5e1 !important; padding-bottom: 12px !important; margin-bottom: 25px !important; }
        
        /* 안내 가이드라인 박스 */
        .menu-guide-inline { font-size: 14px !important; font-weight: 600 !important; color: #475569 !important; background-color: #f8fafc !important; padding: 8px 16px !important; border-left: 4px solid #3b82f6 !important; border-radius: 4px !important; margin: 0 0 15px 0 !important; width: 100% !important; box-sizing: border-box !important; }

        .sync-giant-title { font-size: 24px !important; font-weight: 800 !important; color: #0f172a !important; margin-bottom: 10px !important; }
        .stButton button { white-space: nowrap !important; word-break: keep-all !important; }

        /* 모든 에러/성공/알림 메시지 폰트 일괄 통일 */
        div[data-testid="stAlert"] * {
            font-size: 14px !important;
            font-weight: 600 !important;
        }
        
        /* 🔒 30px 박스 붕괴 현상을 원천 방어하는 CSS 클래스 잠금 */
        .row1-fixed-status-box {
            min-height: 30px !important;
            max-height: 30px !important;
            height: 30px !important;
            display: block !important;
            margin: 5px 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 🔑 [Supabase 원격 데이터베이스 연결 체계 주입]
# =========================================================================
SUPABASE_URL = "https://jwkvojfmhorndnnhscwl.supabase.co"
SUPABASE_KEY = "sb_publishable_6--SHGogHaHSEVO7g3rNjQ_FOHO-XlN"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

master_student_table = "all_students"  
student_table = "student_scores"        
teacher_table = "teacher_accounts"
config_table = "subject_configs"

def load_db_df(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception:
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
            titles = [row.get("item1_name", "수행평가1"), row.get("item2_name", "수행평가2"), row.get("item3_name", "수행평가3"), row.get("item4_name", "수행평가4"), row.get("item5_name", "수행평가5")]
            return count, titles
    return 3, ["수행평가1", "수행평가2", "수행평가3", "수행평가4", "수행평가5"]

# =========================================================================
# ➕ [다이얼로그 팝업창 모듈]
# =========================================================================
@st.dialog("➕ 교사 개별 추가")
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
                    time.sleep(0.3); st.rerun()
                except Exception as e: st.error(f"❌ 등록 실패: {e}")

@st.dialog("➕ 학적 변동 학생 추가 (교과 맞춤형 독립 입력)")
def show_add_student_dialog(subject_key):
    st.markdown("전입/학적 변동 학생의 신상 정보 및 학교 이메일을 직접 등록합니다.")
    with st.form("add_student_form", border=False):
        c1, c2, c3 = st.columns(3)
        with c1: ban = st.text_input("반", placeholder="예: 1")
        with c2: num = st.text_input("번호", placeholder="예: 15")
        with c3: name = st.text_input("이름", placeholder="예: 홍길동")
        email = st.text_input("학교 이메일 계정 (ID)", placeholder="student@school.kr")
        
        submit_btn = st.form_submit_button("💾 해당 학생 이 과목에 배정하기", use_container_width=True)
        if submit_btn:
            if not ban.strip() or not num.strip() or not name.strip() or not email.strip(): 
                st.error("❌ 모든 항목을 빠짐없이 입력해 주세요.")
            else:
                try:
                    supabase.table(student_table).upsert({
                        "subject_key": subject_key, 
                        "반": int(ban.strip()), 
                        "번호": int(num.strip()), 
                        "이름": name.strip(), 
                        "school_email": email.strip(),
                        "password": "1234",
                        "수행평가1": 0, "수행평가2": 0, "수행평가3": 0, "수행평가4": 0, "수행평가5": 0,
                        "성적조회 횟수": 0, "최종 확인일시": "-"
                    }).execute()
                    st.success("🎉 과목 학적 명단에 성공적으로 안착되었습니다!")
                    time.sleep(0.5); st.rerun()
                except Exception as e: st.error(f"❌ 데이터베이스 연동 실패: {e}")

@st.dialog("➕ 학생 개별 추가")
def show_add_master_student_single_dialog():
    st.markdown("마스터 대장에 새로 개별 추가할 학생의 기본 학적 정보를 정확히 기입하세요.")
    with st.form("add_mst_student_form", border=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: grade = st.text_input("학년", placeholder="3")
        with c2: ban = st.text_input("반", placeholder="2")
        with c3: num = st.text_input("번호", placeholder="1")
        with c4: name = st.text_input("이름", placeholder="홍길동")
        email = st.text_input("학교 이메일 계정 (ID)", placeholder="student@school.kr")
        pw = st.text_input("초기 조회 비밀번호", value="1234")
        if st.form_submit_button("추가", use_container_width=True):
            if grade and ban and num and name and email and pw:
                try:
                    supabase.table(master_student_table).upsert({
                        "학년": int(grade.strip()), "반": int(ban.strip()), "번호": int(num.strip()),
                        "이름": name.strip(), "school_email": email.strip(), "password": pw.strip()
                    }).execute()
                    
                    st.session_state["mst_filter_grade"] = f"{grade.strip()}학년"
                    st.session_state["mst_filter_ban"] = f"{ban.strip()}반"
                    
                    if "cached_student_df" in st.session_state: del st.session_state["cached_student_df"]
                    st.success(f"🎉 {name.strip()} 학생 마스터 추가 완료!"); time.sleep(1.0); st.rerun()
                except Exception as e: st.error(f"❌ 추가 실패: {e}")
            else: st.error("❌ 공란이 있습니다.")

@st.dialog("🎉 성적 조회 결과")
def show_result_dialog(student_data):
    st.markdown(f"<div><b>{student_data['이름']}</b> 학생의 실시간 성적 내역입니다.</div><br>", unsafe_allow_html=True)
    
    # 테두리 격자 스타일 강제 주입
    st.markdown("""
        <style>
            .score-grid-container {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                overflow: hidden;
                text-align: center;
                background-color: #ffffff;
            }
            .score-header-box {
                background-color: #f8fafc;
                font-size: 13px;
                font-weight: 800;
                color: #475569;
                padding: 10px 0;
                border-bottom: 1px solid #cbd5e1;
            }
            .score-header-box:not(:last-child), .score-value-box:not(:last-child) {
                border-right: 1px solid #cbd5e1;
            }
            .score-value-box {
                font-size: 20px;
                font-weight: 800;
                color: #0f172a;
                padding: 15px 0;
            }
            .score-total-value {
                color: #3b82f6 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # 점수 파싱 및 합계 계산
    sc1 = int(student_data.get('수행평가1', 0))
    sc2 = int(student_data.get('수행평가2', 0))
    sc3 = int(student_data.get('수행평가3', 0))
    total_score = sc1 + sc2 + sc3
    
    # 4열 격자 표 렌더링
    st.markdown(f"""
        <div class="score-grid-container">
            <div class="score-header-box">수행평가 1차</div>
            <div class="score-header-box">수행평가 2차</div>
            <div class="score-header-box">수행평가 3차</div>
            <div class="score-header-box" style="background-color: #eff6ff; color: #1e40af;">합계</div>
            
            <div class="score-value-box">{sc1}점</div>
            <div class="score-value-box">{sc2}점</div>
            <div class="score-value-box">{sc3}점</div>
            <div class="score-value-box score-total-value" style="background-color: #f0f9ff;">{total_score}점</div>
        </div>
        <br>
    """, unsafe_allow_html=True)
    
    if "has_counted" not in st.session_state:
        new_count = int(student_data.get("성적조회 횟수", 0)) + 1
        supabase.table(student_table).update({
            "성적조회 횟수": new_count, 
            "최종 확인일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).eq("subject_key", student_data["subject_key"]).eq("school_email", student_data["school_email"]).execute()
        st.session_state["has_counted"] = True
    
    if st.button("닫기", type="secondary", use_container_width=True):
        if "has_counted" in st.session_state: del st.session_state["has_counted"]
        st.rerun()

@st.dialog("👤 내 정보 수정")
def show_profile_popup_dialog():
    st.markdown(f"<div>👤 <b>{st.session_state['teacher_name']}</b> 선생님의 계정 정보를 관리합니다.</div><br>", unsafe_allow_html=True)
    edit_mode = st.radio("관리할 항목 선택", ["🔐 비밀번호 변경", "📚 담당과목 변경"], horizontal=True)
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    if "pw_step_unlocked" not in st.session_state: st.session_state["pw_step_unlocked"] = False
    if "pw_save_status" not in st.session_state: st.session_state["pw_save_status"] = "none"
    if "pw_version_key" not in st.session_state: st.session_state["pw_version_key"] = 100

    v_key = str(st.session_state["pw_version_key"])

    if edit_mode == "🔐 비밀번호 변경":
        curr_pw_input = st.text_input("현재 비밀번호", type="password", placeholder="현재 사용 중인 비밀번호 입력", key="cur_pw_v_" + v_key)
        
        if not curr_pw_input:
            st.session_state["pw_save_status"] = "none"

        if curr_pw_input:
            if curr_pw_input.strip() != st.session_state.get("logged_teacher_pw", ""):
                st.markdown("<p style='color: #ef4444; font-size: 14px; font-weight: 600; margin-top: 5px;'>❌ 현재 비밀번호가 일치하지 않습니다.</p>", unsafe_allow_html=True)
                st.session_state["pw_save_status"] = "none"
            else:
                st.markdown("<p style='color: #10b981; font-size: 14px; font-weight: 600;'>✅ 현재 비밀번호가 확인되었습니다.</p>", unsafe_allow_html=True)
                
                new_pw = st.text_input("새 비밀번호 입력", type="password", placeholder="새로운 비밀번호 설정", key="new_pw_v_" + v_key, on_change=reset_pw_status)
                new_pw_confirm = st.text_input("새 비밀번호 확인", type="password", placeholder="새로운 비밀번호 다시 입력", key="confirm_pw_v_" + v_key, on_change=reset_pw_status)
                
                msg_placeholder = st.container()
                if st.session_state["pw_save_status"] == "success":
                    msg_placeholder.markdown("<p style='color: #10b981; font-size: 14px; font-weight: 600; margin-top: 5px;'>✓ 비밀번호를 변경하였습니다.</p>", unsafe_allow_html=True)
                elif st.session_state["pw_save_status"] == "fail_mismatch":
                    msg_placeholder.markdown("<p style='color: #ef4444; font-size: 14px; font-weight: 600; margin-top: 5px;'>❌ 새 비밀번호가 서로 일치하지 않습니다. 다시 확인해 주세요.</p>", unsafe_allow_html=True)
                elif st.session_state["pw_save_status"] == "fail_empty":
                    msg_placeholder.markdown("<p style='color: #ef4444; font-size: 14px; font-weight: 600; margin-top: 5px;'>❌ 새 비밀번호는 공백일 수 없습니다.</p>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                
                with col1: 
                    save_btn = st.button("💾 비밀번호 저장", type="primary", use_container_width=True)
                with col2: 
                    close_btn = st.button("닫기", key="close_pw_inner", use_container_width=True)

                if close_btn:
                    st.session_state["pw_save_status"] = "none"
                    st.session_state["pw_version_key"] += 1
                    st.rerun()
                    
                if save_btn:
                    clean_new_pw = new_pw.strip()
                    clean_confirm_pw = new_pw_confirm.strip()
                    
                    if not clean_new_pw:
                        st.session_state["pw_save_status"] = "fail_empty"
                        st.rerun()
                    elif clean_new_pw != clean_confirm_pw:
                        st.session_state["pw_save_status"] = "fail_mismatch"
                        st.rerun()
                    else:
                        is_ok = False
                        try:
                            teacher_id = st.session_state.get("logged_teacher_id", "")
                            if teacher_id:
                                supabase.table(teacher_table).update({"비밀번호": clean_new_pw}).eq("교사_ID", teacher_id).execute()
                                st.session_state["logged_teacher_pw"] = clean_new_pw
                                st.session_state["pw_save_status"] = "success"
                                st.session_state["pw_version_key"] += 1
                                is_ok = True
                        except Exception as e: st.error(f"❌ 데이터베이스 반영 중 오류가 발생했습니다: {e}")
                        if is_ok: st.rerun()
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("닫기", key="close_pw_outer", use_container_width=True): 
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
            if not new_subs_str.strip(): msg_box_sub.markdown("<p style='color: #ef4444; font-size: 14px; font-weight: 600;'>❌ 담당 과목을 최소 1개 이상 입력하세요.</p>", unsafe_allow_html=True)
            else:
                st.session_state["allowed_subjects"] = [s.strip() for s in new_subs_str.split(",") if s.strip()]
                msg_box_sub.markdown("<p style='color: #10b981; font-size: 14px; font-weight: 600;'>🎉 담당 과목 권한이 임시 조정되었습니다.</p>", unsafe_allow_html=True)

if "score_input_success_flag" not in st.session_state: st.session_state["score_input_success_flag"] = False
if "info_save_success_flag" not in st.session_state: st.session_state["info_save_success_flag"] = False
if "config_save_success_flag" not in st.session_state: st.session_state["config_save_success_flag"] = False

if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False
if "student_logged_in" not in st.session_state: st.session_state["student_logged_in"] = False
if "logged_student_id" not in st.session_state: st.session_state["logged_student_id"] = ""
if "logged_student_pw" not in st.session_state: st.session_state["logged_student_pw"] = ""
if "logged_teacher_id" not in st.session_state: st.session_state["logged_teacher_id"] = False
if "logged_teacher_pw" not in st.session_state: st.session_state["logged_teacher_pw"] = []

df = load_db_df(student_table)

# =========================================================================
# 🔓 [1단계] 로그인 화면 (안내문구 최적화 및 파란색 단추 바인딩 완료)
# =========================================================================
if not st.session_state["admin_logged_in"] and not st.session_state["student_logged_in"]:
    with st.container():
        with st.form("master_unified_form"):
            st.markdown("<h2 style='text-align:center;'>수행평가 점수 확인 시스템</h2>", unsafe_allow_html=True)
            login_mode = st.radio("접속 모드", ["학생", "교사"], horizontal=True, label_visibility="collapsed")
            
            user_id_input = st.text_input("ID / 이메일", placeholder="학생은 이메일, 교사는 ID를 입력하세요.", label_visibility="collapsed")
            user_pw_input = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요", label_visibility="collapsed")
            
            b_col2 = st.columns([1.0, 1.8, 1.0])[1]
            submit_active = b_col2.form_submit_button("로그인", type="primary", use_container_width=True)
            
            if submit_active:
                clean_id = str(user_id_input).strip()
                clean_pw = str(user_pw_input).strip()
                if login_mode == "학생":
                    res = supabase.table(master_student_table).select("*").eq("school_email", clean_id).eq("password", clean_pw).execute().data
                    if res:
                        st.session_state["student_logged_in"] = True
                        st.session_state["logged_student_id"] = clean_id
                        st.session_state["logged_student_pw"] = clean_pw
                        st.session_state["student_info"] = res[0]
                        st.rerun()
                    else: st.error("❌ 학생 로그인 정보가 올바르지 않습니다.")
                elif login_mode == "교사":
                    if clean_id == "admin" and clean_pw == "1234":
                        st.session_state["admin_logged_in"] = True
                        st.session_state["logged_teacher_id"] = "admin"
                        st.session_state["logged_teacher_pw"] = "1234"
                        st.session_state["teacher_name"] = "최고관리자"
                        st.session_state["allowed_subjects"] = ["마스터"]
                        st.session_state["current_menu"] = "학생 조회 현황 모니터링"
                        st.rerun()
                    else:
                        df_tc = load_db_df(teacher_table)
                        id_match = df_tc[df_tc['교사_ID'] == clean_id] if not df_tc.empty else pd.DataFrame()
                        if not id_match.empty and str(id_match.iloc[0]['비밀번호']) == clean_pw:
                            row = id_match.iloc[0]
                            st.session_state["admin_logged_in"] = True
                            st.session_state["logged_teacher_id"] = clean_id
                            st.session_state["logged_teacher_pw"] = clean_pw
                            st.session_state["teacher_name"] = str(row['교사_성명']).strip()
                            allowed = [s.strip() for s in str(row['담당_과목']).split(",") if s.strip()]
                            st.session_state["allowed_subjects"] = allowed
                            
                            active_dbs = get_active_databases()
                            if "마스터" not in allowed:
                                active_dbs = [d for d in active_dbs if d['subject'].strip() in allowed]
                            
                            if not active_dbs and "마스터" not in allowed:
                                st.session_state["current_menu"] = "평가 대상 과목 구성"
                            else:
                                st.session_state["current_menu"] = "학생 조회 현황 모니터링"
                            
                            st.rerun()
                        else: st.error("❌ 교사 로그인 실패")

# =========================================================================
# 🎓 [2단계-A] 학생 화면 (📱 스마트폰 사이즈 맞춤 및 st.form 하얀 사각형 가두리 완결)
# =========================================================================
elif st.session_state["student_logged_in"]:
    # 💡 모바일 가두리 컨테이너 벨트 시작
    st.markdown('<div class="student-mobile-container">', unsafe_allow_html=True)
    
    # 💡 [그림2 요구사항 최종 해결] 로그인 화면과 똑같이 st.form을 사용하여 하얀 사각형 안에 무조건 가둠!
    with st.form("student_mobile_form", border=True):
        st.markdown("<h2>수행평가 점수 확인</h2>", unsafe_allow_html=True)
        
        active_dbs = get_active_databases()
        if not active_dbs:
            st.markdown("<p style='color:#ef4444; font-weight:700;'>현재 평가 데이터베이스에 활성화된 과목이 없습니다.</p>", unsafe_allow_html=True)
            submit_active = False
        else:
            opts_s = ["과목을 선택하세요."] + [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in active_dbs]
            sel_s = st.selectbox("조회할 교과과정 선택", opts_s, label_visibility="visible")
            
            st.markdown("<br>", unsafe_allow_html=True)
            # 우리의 파란색 단추로 제출 버튼 바인딩
            submit_active = st.form_submit_button("🚀 나의 성적 실시간 검증", type="primary", use_container_width=True)

        # 폼 내부에서 제출 버튼이 눌렸을 때의 로직 처리
        if submit_active and sel_s != "과목을 선택하세요.":
            chosen_db = active_dbs[opts_s.index(sel_s)-1]
            subject_key = chosen_db['key']

            res = supabase.table(student_table).select("*").eq("subject_key", subject_key).eq("school_email", st.session_state["logged_student_id"]).execute()
            
            if len(res.data) > 0:
                show_result_dialog(res.data[0])
            else:
                st.error("❌ 해당 과목에 등록된 선생님의 성적 데이터가 아직 없습니다.")
                
    # 💡 로그아웃 단추는 하얀 상자 바로 밑에 모바일 너비에 맞춰 깔끔하게 배치
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 안전하게 로그아웃", type="secondary", use_container_width=True, key="std_logout_btn"): 
        st.session_state.clear()
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================================
# 🔒 [2단계-B] 교사 화면 (화강암 고정 구역 - 절대 변경 금지 지침 완벽 완수)
# =========================================================================
elif st.session_state["admin_logged_in"]:
    menus = ["학생 조회 현황 모니터링", "수행 평가 성적 입력", "학생 기본 정보 관리", "평가 대상 과목 구성"]
    
    allowed_trimmed = [str(x).strip() for x in st.session_state.get("allowed_subjects", []) if str(x).strip()]
    is_admin = (st.session_state.get("logged_teacher_id") == "admin" or "마스터" in allowed_trimmed)

    if is_admin: 
        menus.append("👑 학생 계정 관리")
        menus.append("👑 교사 계정 관리") 
        
    if "current_menu" not in st.session_state or st.session_state["current_menu"] not in menus:
        st.session_state["current_menu"] = menus[0]

    with st.sidebar:
        st.markdown('<span class="sidebar-title">📋 교사 메뉴</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="user-info">👤 {st.session_state["teacher_name"]} 선생님 접속 중</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        try:
            menu_idx = menus.index(st.session_state["current_menu"])
        except ValueError:
            menu_idx = 0

        menu_selection_radio = st.radio("메뉴 선택", menus, index=menu_idx, label_visibility="collapsed")
        
        if menu_selection_radio != st.session_state["current_menu"]:
            st.session_state["current_menu"] = menu_selection_radio
            st.rerun()
            
        menu_selection = st.session_state["current_menu"]
        
        st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
        
        if st.button("👤 내 정보 수정", type="secondary", use_container_width=True):
            show_profile_popup_dialog()
        if st.sidebar.button("🚪 로그아웃", type="secondary", use_container_width=True): st.session_state.clear(); st.rerun()

    st.markdown(f"""
        <div class="header-title-main">수행평가 점수 확인 시스템</div>
        <div class="header-nav-sub" style="border-bottom: 2px solid #cbd5e1; padding-bottom: 12px; margin-bottom: 25px;">
            📍 현재 위치: {"최고관리자 모드" if is_admin else "교사 모드"} > <span style="color: #3b82f6;">📂 {menu_selection}</span>
        </div>
    """, unsafe_allow_html=True)

    if not df.empty and "반" in df.columns and "번호" in df.columns: df = df.sort_values(by=["반", "번호"])

    layout_left, layout_right = st.columns([3.5, 6.5])

    # ---------------------------------------------------------------------
    # 1번 메뉴: 학생 조회 현황 모니터링
    # ---------------------------------------------------------------------
    if menu_selection == "학생 조회 현황 모니터링":
        registered_dbs = get_active_databases()
        if not is_admin:
            registered_dbs = [d for d in registered_dbs if d['subject'].strip() in allowed_trimmed]
        
        if not registered_dbs:
            with layout_left: st.info("📢 현재 개설되었거나 권한이 연결된 과목이 없습니다.")
        else:
            with layout_left:
                st.markdown("**📂 대상 교과 선택**")
                selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                selected_db_str = st.selectbox("교과 선택", options=selector_options, label_visibility="collapsed", key="mon_sub")
                chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                subject_key = chosen_db['key']
                df_data = supabase.table(student_table).select("*").eq("subject_key", subject_key).execute().data
                df = pd.DataFrame(df_data)
                if not df.empty: df = df.sort_values(by=["반", "번호"]).reset_index(drop=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**🎯 필터링할 학급 선택**")
                class_options = ["전체 학급 보기"]
                if not df.empty and "반" in df.columns: class_options += [f"{x}반" for x in sorted(df['반'].unique())]
                selected_class = st.selectbox("학급 선택", options=class_options, label_visibility="collapsed", key="mon_class")
                
            with layout_right:
                item_count, item_titles = get_subject_item_names(subject_key)
                if df.empty: st.info("📢 해당 교과에 등록된 데이터가 없습니다.")
                else:
                    r_df = df.copy()
                    if selected_class != "전체 학급 보기": r_df = r_df[r_df['반'].astype(int) == int(selected_class.replace("반",""))]
                    display_cols = ["반", "번호", "이름", "school_email"]
                    rename_map = {"school_email": "학교 이메일"}
                    align_config = {"반": st.column_config.TextColumn(alignment="center"), "번호": st.column_config.TextColumn(alignment="center"), "이름": st.column_config.TextColumn(alignment="center"), "학교 이메일": st.column_config.TextColumn(alignment="center")}
                    for idx in range(item_count):
                        db_col = f"수행평가{idx+1}"
                        if db_col in r_df.columns:
                            display_cols.append(db_col)
                            rename_map[db_col] = item_titles[idx]
                            align_config[item_titles[idx]] = st.column_config.NumberColumn(alignment="center")
                    display_cols += ["성적조회 횟수", "최종 확인일시"]
                    final_view_df = r_df[display_cols].rename(columns=rename_map)
                    st.dataframe(final_view_df.fillna("-"), use_container_width=True, hide_index=True, column_config=align_config, height=650)

    # ---------------------------------------------------------------------
    # 2번 메뉴: 수행 평가 성적 입력
    # ---------------------------------------------------------------------
    elif menu_selection == "수행 평가 성적 입력":
        registered_dbs = get_active_databases()
        if not is_admin:
            registered_dbs = [d for d in registered_dbs if d['subject'].strip() in allowed_trimmed]

        if not registered_dbs:
            with layout_left: st.info("📢 현재 개설되었거나 권한이 연결된 과목이 없습니다.")
        else:
            with layout_left:
                st.markdown("**📂 관리할 교과 선택**")
                selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                selected_db_str = st.selectbox("교과 선택", options=selector_options, label_visibility="collapsed", key="edt_sub")
                chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                subject_key = chosen_db['key']
                item_count, item_titles = get_subject_item_names(subject_key)

                df_data = supabase.table(student_table).select("*").eq("subject_key", subject_key).execute().data
                df_base = pd.DataFrame(df_data)
                if not df_base.empty: df_base = df_base.sort_values(by=["반", "번호"]).reset_index(drop=True)

                st.markdown("<br>**🎯 필터링할 학급 선택**", unsafe_allow_html=True)
                class_options_ed = ["전체 학급 보기"]
                if not df_base.empty and "반" in df_base.columns: class_options_ed += [f"{x}반" for x in sorted(df_base['반'].unique())]
                selected_class_ed = st.selectbox("학급 선택", options=class_options_ed, label_visibility="collapsed", key="edt_class")
                
                st.markdown("<hr style='margin: 15px 0; border: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)
                st.markdown("💡 **양식을 다운로드하여 성적을 일괄 업로드하세요.**")
                template_df = pd.DataFrame({"반": [1, 1], "번호": [1, 2], "이름": ["홍길동", "이영희"]})
                for col in item_titles[:item_count]: template_df[col] = [20, 18]
                    
                csv_buffer = template_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 일괄 업로드용 성적 양식 다운로드", data=csv_buffer, file_name="수행성적양식.csv", mime="text/csv", use_container_width=True)
                
                st.markdown("<br>📂 **엑셀/CSV 성적 일괄 가져오기 (덮어쓰기)**", unsafe_allow_html=True)
                up_f = st.file_uploader("엑셀 파일 올리기", type=["csv", "xlsx"], label_visibility="collapsed", key="integrated_file_uploader")
                
                excel_loaded_df = None
                file_just_loaded = False
                if up_f:
                    try:
                        df_up = pd.read_csv(up_f) if up_f.name.endswith(".csv") else pd.read_excel(up_f)
                        df_up.columns = [c.strip() for c in df_up.columns]
                        for idx_t, title in enumerate(item_titles[:item_count]):
                            if title in df_up.columns: df_up[f"수행평가{idx_t+1}"] = df_up[title]
                        excel_loaded_df = df_up
                        file_just_loaded = True
                    except Exception as e: st.error(f"❌ 파일 해석 실패: {e}")
                
                st.markdown('<div class="row1-fixed-status-box">', unsafe_allow_html=True)
                status_placeholder = st.empty()
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.session_state.get("score_input_success_flag", False):
                    status_placeholder.markdown("<p style='color:#3b82f6; font-weight:700; margin:0; padding:0; font-size:14px; line-height:30px;'>🎉 수행 평가 점수를 저장하였습니다.</p>", unsafe_allow_html=True)
                    st.session_state["score_input_success_flag"] = False
                elif file_just_loaded:
                    status_placeholder.markdown("<p style='color:#10b981; font-weight:700; margin:0; padding:0; font-size:14px; line-height:30px;'>✅ 파일 로드 성공! 오른쪽 테이블에 실시간 동기화되었습니다.</p>", unsafe_allow_html=True)
                else:
                    status_placeholder.markdown("<p style='margin:0; padding:0; line-height:30px;'>&nbsp;</p>", unsafe_allow_html=True)

                row2_cols = st.columns([5.0, 5.0])
                with row2_cols[0]:
                    st.write("") 
                with row2_cols[1]: 
                    save_trigger = st.button("💾 성적 저장하기", type="primary", use_container_width=True, key="original_left_save_btn")

                if save_trigger:
                    status_placeholder.markdown("<p style='color:#64748b; font-weight:700; margin:0; padding:0; font-size:14px; line-height:30px;'>⏳ 원격 데이터베이스에 동기화 중...</p>", unsafe_allow_html=True)
                    df_to_save = excel_loaded_df.copy() if excel_loaded_df is not None else df_base.copy()
                    if not df_to_save.empty:
                        try:
                            clean_score_records = []
                            f_idx_save = df_to_save[df_to_save["반"].astype(int) == int(selected_class_ed.replace("반", ""))].index if selected_class_ed != "전체 학급 보기" else df_to_save.index
                            
                            for _pos in f_idx_save:
                                view_row = df_to_save.loc[_pos].to_dict()
                                mst_lookup = supabase.table(master_student_table).select("school_email").eq("반", int(view_row["반"])).eq("번호", int(view_row["번호"])).eq("이름", str(view_row["이름"]).strip()).execute().data
                                if not mst_lookup:
                                    status_placeholder.empty()
                                    st.error(f"❌ '{view_row['반']}반 {view_row['번호']}번 {view_row['이름']}' 학생이 전교생 마스터 대장에 존재하지 않습니다. 최고관리자 메뉴에서 마스터 계정을 먼저 등록해 주세요.")
                                    st.stop()
                                    
                                email = mst_lookup[0]["school_email"]
                                record = {"subject_key": subject_key, "반": int(view_row["반"]), "번호": int(view_row["번호"]), "이름": str(view_row["이름"]).strip(), "school_email": email, "password": "1234", "수행평가1": 0, "수행평가2": 0, "수행평가3": 0, "수행평가4": 0, "수행평가5": 0, "성적조회 횟수": 0, "최종 확인일시": "-"}
                                for idx_c in range(item_count):
                                    db_col = f"수행평가{idx_c+1}"
                                    record[db_col] = int(view_row.get(item_titles[idx_c], view_row.get(db_col, 0)))
                                clean_score_records.append(record)
                            
                            supabase.table(student_table).delete().eq("subject_key", subject_key).execute()
                            if clean_score_records:
                                supabase.table(student_table).insert(clean_score_records).execute()
                                
                            st.session_state["score_input_success_flag"] = True
                            status_placeholder.empty()
                            st.rerun()
                        except Exception as e:
                            status_placeholder.empty()
                            st.error(f"❌ 데이터베이스 반영 중 오류가 발생했습니다: {e}")

            with layout_right:
                st.markdown('<p class="menu-guide-inline">💡 개인별 점수를 수정한 후, 왼쪽 패널 하단의 [💾 성적 저장하기] 버튼을 누르시면 반영됩니다.</p>', unsafe_allow_html=True)
                df = excel_loaded_df.copy() if excel_loaded_df is not None else df_base.copy()

                if df.empty: st.info("📢 현재 등록된 성적 대장이 없습니다. 학생 기본 정보 관리를 통해 이 과목에 학생 명단을 먼저 배정하세요.")
                else:
                    f_idx = df[df["반"].astype(int) == int(selected_class_ed.replace("반", ""))].index if selected_class_ed != "전체 학급 보기" else df.index
                    target_cols = ["반", "번호", "이름"]
                    rename_map = {}
                    align_config = {"반": st.column_config.TextColumn(alignment="center"), "번호": st.column_config.TextColumn(alignment="center"), "이름": st.column_config.TextColumn(alignment="center")}
                    
                    df["합계"] = 0
                    for idx in range(item_count):
                        db_col = f"수행평가{idx+1}"
                        target_cols.append(db_col)
                        rename_map[db_col] = item_titles[idx]
                        align_config[item_titles[idx]] = st.column_config.NumberColumn(alignment="center")
                        if db_col in df.columns:
                            df[db_col] = df[db_col].fillna(0).astype(int)
                            df["합계"] += df[db_col]
                    target_cols.append("합계")
                    align_config["합계"] = st.column_config.NumberColumn(alignment="center", format="%d 점")
                    
                    sub_df = df.loc[f_idx, target_cols].rename(columns=rename_map)
                    edited_df = st.data_editor(sub_df, use_container_width=True, disabled=["반", "번호", "이름", "합계"], hide_index=True, key="grid_ed_sc", column_config=align_config, height=600)

    # ---------------------------------------------------------------------
    # 3번 메뉴: 학생 기본 정보 관리
    # ---------------------------------------------------------------------
    elif menu_selection == "학생 기본 정보 관리":
        registered_dbs = get_active_databases()
        if not is_admin:
            registered_dbs = [d for d in registered_dbs if d['subject'].strip() in allowed_trimmed]

        if not registered_dbs:
            with layout_left: st.info("📢 현재 개설되었거나 권한이 연결된 과목이 없습니다.")
        else:
            with layout_left:
                st.markdown("**📂 관리할 교과 선택**")
                selector_options = [f"📚 {d['subject']} ({d['grade']} / {d['semester']})" for d in registered_dbs]
                selected_db_str = st.selectbox("교과 선택", options=selector_options, label_visibility="collapsed", key="inf_sub")
                chosen_db = registered_dbs[selector_options.index(selected_db_str)]
                subject_key = chosen_db['key']
                
                df = pd.DataFrame(supabase.table(student_table).select("*").eq("subject_key", subject_key).execute().data)
                if not df.empty: df = df.sort_values(by=["반", "번호"]).reset_index(drop=True)

                st.markdown("<br>", unsafe_allow_html=True)
                class_opts = ["전체"]
                if not df.empty and "반" in df.columns: class_opts += [f"{x}반" for x in sorted(df['반'].unique())]
                sel_c = st.selectbox("학반 필터링", options=class_opts, label_visibility="collapsed", key="inf_class")

                for _ in range(19): st.write("")
                
                st.markdown('<div class="row1-fixed-status-box">', unsafe_allow_html=True)
                status_placeholder = st.empty()
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.session_state.get("info_save_success_flag", False):
                    status_placeholder.markdown("<p style='color:#3b82f6; font-weight:700; margin:0; padding:0; font-size:14px; line-height:30px;'>🎉 학생 기본 정보를 저장하였습니다.</p>", unsafe_allow_html=True)
                    st.session_state["info_save_success_flag"] = False
                else:
                    status_placeholder.markdown("<p style='margin:0; padding:0; line-height:30px;'>&nbsp;</p>", unsafe_allow_html=True)
                
                row2_cols = st.columns([5.0, 5.0])
                with row2_cols[0]:
                    add_std_trigger = st.button("➕ 전입생 추가 배정", use_container_width=True)
                with row2_cols[1]:
                    save_info_trigger = st.button("💾 학생 기본 정보 저장", type="primary", use_container_width=True, key="fine_tuned_info_save_btn")

                if add_std_trigger: 
                    show_add_student_dialog(subject_key)

            with layout_right:
                st.markdown('<p class="menu-guide-inline">💡 개인별 인적사항을 수정한 후, 왼쪽 패널 하단의 [💾 학생 기본 정보 저장] 버튼을 누르시면 반영됩니다.</p>', unsafe_allow_html=True)
                if df.empty: st.info("📢 배정된 명단이 없습니다. 전입생 추가 기능이나 최고관리자의 마스터 연동 기능을 이용해 명단을 세팅하세요.")
                else:
                    f_idx = df[df["반"].astype(int) == int(sel_c.replace("반", ""))].index if sel_c != "전체" else df.index
                    edited_df = st.data_editor(df.loc[f_idx, ["반", "번호", "이름", "school_email"]], use_container_width=True, hide_index=True, key="grid_ed_inf", height=600, column_config={"school_email": st.column_config.TextColumn("학교 이메일")})
                    if save_info_trigger:
                        try:
                            for _pos in range(len(edited_df)):
                                vr = edited_df.iloc[_pos]
                                orig_r = df.loc[f_idx[_pos]].to_dict()
                                orig_r["반"], orig_r["번호"], orig_r["이름"], orig_r["school_email"] = int(vr["반"]), int(vr["번호"]), str(vr["이름"]).strip(), str(vr["school_email"]).strip()
                                supabase.table(student_table).upsert(orig_r).execute()
                            st.session_state["info_save_success_flag"] = True
                            time.sleep(0.2); st.rerun()
                        except Exception as e: st.error(f"❌ 명단 저장 실패: {e}")

    # ---------------------------------------------------------------------
    # 4번 메뉴: 평가 대상 과목 구성
    # ---------------------------------------------------------------------
    elif menu_selection == "평가 대상 과목 구성":
        main_col1, main_col2 = layout_left, layout_right
        with main_col1:
            with st.container(border=True):
                st.markdown('<div class="sync-giant-title">⚙️ 1. 평가 과목 설정</div>', unsafe_allow_html=True)
                st.caption("과목 설정이 끝나면, 우측에서 수행평가 세부 항목을 구성하세요.")
                st.markdown("<br>", unsafe_allow_html=True)
                
                if not is_admin and len(allowed_trimmed) == 1:
                    single_subject = allowed_trimmed[0]
                    st.text_input("세부 과목 (자동 지정 완료)", value=single_subject, disabled=True)
                    final_sub = single_subject
                    sel_se = st.selectbox("학기 선택", options=["학기를 선택하세요.", "2026학년도 1학기", "2026학년도 2학기"], index=0)
                    sel_gr = st.selectbox("학년 지정", options=["학년을 선택하세요.", "1학년", "2학년", "3학년"], index=0)
                else:
                    all_assigned_subjects = allowed_trimmed if not is_admin else ["국어", "영어", "수학", "사회", "과학", "역사", "도덕", "기술·가정", "정보", "음악", "미술", "체육", "한문", "중국어"]
                    final_sub = st.selectbox("세부 과목 지정", options=["과목을 선택하세요."] + all_assigned_subjects, index=0)
                    grid_c2 = st.container()
                    with grid_c2:
                        sel_se = st.selectbox("학기 선택", options=["학기를 선택하세요.", "2026학년도 1학기", "2026학년도 2학기"], index=0)
                        sel_gr = st.selectbox("학년 지정", options=["학년을 선택하세요.", "1학년", "2학년", "3학년"], index=0)

        if final_sub != "과목을 선택하세요." and sel_gr != "학년을 선택하세요." and sel_se != "학기를 선택하세요.":
            with main_col2:
                subject_key = f"{final_sub}_{sel_gr}_{sel_se}".replace(" ", "_")
                cfg_df = load_db_df(config_table)
                db_match = cfg_df[cfg_df["subject_key"] == subject_key] if not cfg_df.empty else pd.DataFrame()
                init_count = int(db_match.iloc[0]["item_count"]) if not db_match.empty else 3
                
                with st.container(border=True):
                    st.markdown('<div class="sync-giant-title">🎯 2. 수행평가 항목 구성</div>', unsafe_allow_html=True)
                    item_count = st.selectbox("평가 반영 항목 개수 선택", [1, 2, 3, 4, 5], index=init_count - 1)
                    item_titles = []
                    for i in range(item_count):
                        t_in = st.text_input(f"항목 {i+1} 제목", value=f"수행평가{i+1}", key=f"cfg_t_{i}")
                        item_titles.append(t_in.strip())
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.session_state.get("config_save_success_flag", False):
                        st.success("🎉 과목 구성 완료!")
                        st.session_state["config_save_success_flag"] = False
                    
                    btn_cols = st.columns(5)
                    with btn_cols[2]:
                        config_save_btn_trigger = st.button("💾 과목 설정 저장", type="primary", use_container_width=True)
                        
                    if config_save_btn_trigger:
                        rec = {"subject_key": subject_key, "item_count": item_count}
                        for idx_c in range(5): rec[f"item{idx_c+1}_name"] = item_titles[idx_c] if idx_c < len(item_titles) else "-"
                        supabase.table(config_table).upsert(rec).execute()
                        st.session_state["config_save_success_flag"] = True
                        time.sleep(0.2); st.rerun()

    # ---------------------------------------------------------------------
    # 5번 메뉴: 👑 학생 계정 관리
    # ---------------------------------------------------------------------
    elif menu_selection == "👑 학생 계정 관리" and is_admin:
        if "cached_student_df" not in st.session_state:
            db_df = load_db_df(master_student_table)
            if not db_df.empty: db_df = db_df.sort_values(by=["학년", "반", "번호"]).reset_index(drop=True)
            st.session_state["cached_student_df"] = db_df
            st.session_state["show_student_toast"] = False  
            st.session_state["student_save_success_flag"] = False 

        if "student_file_uploader_key" not in st.session_state: st.session_state["student_file_uploader_key"] = "st_uploader_init_100"
        if "mst_filter_grade" not in st.session_state: st.session_state["mst_filter_grade"] = "전체 학년"
        if "mst_filter_ban" not in st.session_state: st.session_state["mst_filter_ban"] = "전체 반"

        with layout_left:
            st.markdown('<p class="menu-guide-inline">💡 개인별 인적사항을 에디터 상에서 수정하거나 행을 추가한 후, 아래 [💾 학생 계정 저장] 버튼을 누르셔야 원격 클라우드 DB에 안전하게 일괄 저장 반영됩니다.</p>', unsafe_allow_html=True)
            st.markdown("**🔍 학년과 반별 필터링**")
            cached_data_src = st.session_state["cached_student_df"]
            
            g_opts = ["전체 학년"]
            b_opts = ["전체 반"]
            if not cached_data_src.empty:
                g_opts += [f"{x}학년" for x in sorted(cached_data_src["학년"].unique())]
                b_opts += [f"{x}반" for x in sorted(cached_data_src["반"].unique())]
                
            try: g_idx_sel = g_opts.index(st.session_state["mst_filter_grade"])
            except: g_idx_sel = 0
            try: b_idx_sel = b_opts.index(st.session_state["mst_filter_ban"])
            except: b_idx_sel = 0
                
            sel_mst_g = st.selectbox("학년 필터", options=g_opts, index=g_idx_sel, label_visibility="collapsed", key="mst_grade_sb")
            sel_mst_b = st.selectbox("반 필터", options=b_opts, index=b_idx_sel, label_visibility="collapsed", key="mst_ban_sb")
            
            st.session_state["mst_filter_grade"] = sel_g_track = sel_mst_g
            st.session_state["mst_filter_ban"] = sel_b_track = sel_mst_b
            st.markdown("<hr style='margin: 15px 0; border: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)
            st.markdown("📂 **학생 계정 일괄 업로드**")
            
            template_mst_df = pd.DataFrame({
                "학년": [3, 3], "반": [2, 2], "번호": [1, 2], "이름": ["홍길동", "이영희"],
                "school_email": ["hgd@school.kr", "lyh@school.kr"], "password": ["1234", "1234"]
            })
            mst_csv_buffer = template_mst_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 일괄 업로드용 마스터 양식 다운로드", data=mst_csv_buffer, file_name="전교생_마스터_일괄업로드_양식.csv", mime="text/csv", key="mst_down_btn", use_container_width=True)
            mst_f = st.file_uploader("전교생 마스터 엑셀 파일 업로드", type=["csv", "xlsx"], label_visibility="collapsed", key=st.session_state["student_file_uploader_key"])
            
            if mst_f:
                try:
                    df_mst = pd.read_csv(mst_f) if mst_f.name.endswith(".csv") else pd.read_excel(mst_f)
                    df_mst.columns = [c.strip() for c in df_mst.columns]
                    parsed_df = pd.DataFrame()
                    parsed_df["학년"] = df_mst["학년"].astype(int)
                    parsed_df["반"] = df_mst["반"].astype(int)
                    parsed_df["번호"] = df_mst["번호"].astype(int)
                    parsed_df["이름"] = df_mst["이름"].astype(str)
                    parsed_df["school_email"] = df_mst["school_email"].astype(str)
                    parsed_df["password"] = df_mst["password"].astype(str)
                    
                    if "last_loaded_file_name_student" not in st.session_state or st.session_state["last_loaded_file_name_student"] != mst_f.name:
                        st.session_state["cached_student_df"] = parsed_df.sort_values(by=["학년", "반", "번호"]).reset_index(drop=True)
                        st.session_state["show_student_toast"] = True  
                        st.session_state["last_loaded_file_name_student"] = mst_f.name
                except Exception as e: st.error(f"❌ 파일 해석 실패: {e}")

            if st.session_state.get("show_student_toast", False):
                st.toast("📥 엑셀 데이터가 오른쪽 표에 임시 로드되었습니다.")
                st.session_state["show_student_toast"] = False  
            
            st.markdown('<div class="row1-fixed-status-box">', unsafe_allow_html=True)
            mst_status_placeholder = st.empty()
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.session_state.get("student_save_success_flag", False):
                mst_status_placeholder.markdown("<p style='color:#3b82f6; font-weight:700; margin:0; padding:0; font-size:14px; line-height:30px;'>🎉 전교생 학생 계정 대장이 저장되었습니다.</p>", unsafe_allow_html=True)
                st.session_state["student_save_success_flag"] = False 
            else:
                mst_status_placeholder.markdown("<p style='margin:0; padding:0; line-height:30px;'>&nbsp;</p>", unsafe_allow_html=True)
            
            for _ in range(4): st.write("")
            
            student_grid_cols = st.columns([5.0, 5.0])
            with student_grid_cols[0]:
                add_mst_std_trigger = st.button("➕ 학생 개별 신규 추가", use_container_width=True, key="m_single_add_std_btn")
            with student_grid_cols[1]:
                save_all_std_trigger = st.button("💾 학생 계정 저장", type="primary", use_container_width=True, key="master_all_student_save_btn")
                
            if add_mst_std_trigger: show_add_master_student_single_dialog()
                
        with layout_right:
            target_render_df = st.session_state["cached_student_df"].copy()
            if target_render_df.empty: target_render_df = pd.DataFrame(columns=["학년", "반", "번호", "이름", "school_email", "password"])
            if sel_g_track != "전체 학급" and sel_g_track != "전체 학년": target_render_df = target_render_df[target_render_df["학년"] == int(sel_g_track.replace("학년",""))]
            if sel_b_track != "전체 반": target_render_df = target_render_df[target_render_df["반"] == int(sel_b_track.replace("반",""))]
            edited_all_std_df = st.data_editor(target_render_df, use_container_width=True, num_rows="dynamic", hide_index=True, key="master_all_student_editor", height=650)
            
            if save_all_std_trigger:
                with st.spinner("원격 데이터베이스에 마스터 인적사항 갱신 중..."):
                    try:
                        supabase.table(master_student_table).delete().neq("반", 0).execute()
                        clean_records = []
                        for record in edited_all_std_df.to_dict(orient="records"):
                            if record.get("school_email") and record.get("이름") and str(record.get("이름")).strip() != "None":
                                record["학년"] = int(record.get("학년", 1))
                                record["반"] = int(record.get("반", 1))
                                record["번호"] = int(record.get("번호", 1))
                                record["이름"] = str(record["이름"]).strip()
                                record["school_email"] = str(record["school_email"]).strip()
                                record["password"] = str(record.get("password", "1234")).strip()
                                if "id" in record: del record["id"]
                                clean_records.append(record)
                        if clean_records: supabase.table(master_student_table).insert(clean_records).execute()
                        st.session_state["student_file_uploader_key"] = f"st_uploader_init_{int(time.time())}"
                        st.session_state["cached_student_df"] = pd.DataFrame(clean_records)
                        st.session_state["show_student_toast"] = False
                        st.session_state["student_save_success_flag"] = True 
                        time.sleep(0.2); st.rerun()
                    except Exception as e: st.error(f"❌ 저장 실패: {e}")

    # ---------------------------------------------------------------------
    # 6번 메뉴: 👑 교사 계정 관리
    # ---------------------------------------------------------------------
    elif menu_selection == "👑 교사 계정 관리" and is_admin:
        if "cached_teacher_df" not in st.session_state:
            db_tc_df = load_db_df(teacher_table)
            if not db_tc_df.empty: db_tc_df = db_tc_df.sort_values(by=["교사_성명"]).reset_index(drop=True)
            st.session_state["cached_teacher_df"] = db_tc_df
            st.session_state["show_teacher_toast"] = False  
            st.session_state["teacher_save_success_flag"] = False

        if "teacher_file_uploader_key" not in st.session_state: st.session_state["teacher_file_uploader_key"] = "tc_uploader_init_100"

        with layout_left:
            st.markdown('<p class="menu-guide-inline">💡 교사들의 아이디 및 담당과목 권한을 에디터 상에서 수정한 후, 아래 [💾 교사 계정 저장] 버튼을 누르셔야 원격 데이터베이스에 일괄 적용 세이브 완료됩니다.</p>', unsafe_allow_html=True)
            st.markdown("**🔍 교사 계정 필터링**")
            cached_tc_src = st.session_state["cached_teacher_df"]
            tc_opts = ["전체 교직원 보기"]
            if not cached_tc_src.empty: tc_opts += sorted(list(cached_tc_src["교사_성명"].unique()))
            sel_tc_name = st.selectbox("교사 선택", options=tc_opts, index=0, label_visibility="collapsed", key="master_tc_filter_sb")
            st.markdown("<hr style='margin: 15px 0; border: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)
            st.markdown("📂 **교사 계정 일괄 업로드**")
            
            template_tc_df = pd.DataFrame({
                "교사_ID": ["math_master", "eng_queen"], "교사_성명": ["박수학", "이영어"],
                "비밀번호": ["1234", "1234"], "담당_과목": ["수학, 과학", "영어"]
            })
            tc_csv_buffer = template_tc_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 일괄 업로드용 교사 양식 다운로드", data=tc_csv_buffer, file_name="교사_권한대장_일괄업로드_양식.csv", mime="text/csv", use_container_width=True)
            tc_f = st.file_uploader("교사 마스터 엑셀 파일 업로드", type=["csv", "xlsx"], label_visibility="collapsed", key=st.session_state["teacher_file_uploader_key"])
            
            if tc_f:
                try:
                    df_tc_up = pd.read_csv(tc_f) if tc_f.name.endswith(".csv") else pd.read_excel(tc_f)
                    df_tc_up.columns = [c.strip() for c in df_tc_up.columns]
                    parsed_tc_df = pd.DataFrame()
                    parsed_tc_df["교사_ID"] = df_tc_up["교사_ID"].astype(str)
                    parsed_tc_df["교사_성명"] = df_tc_up["교사_성명"].astype(str)
                    parsed_tc_df["비밀번호"] = df_tc_up["비밀번호"].astype(str)
                    parsed_tc_df["담당_과목"] = df_tc_up["담당_과목"].astype(str)
                    
                    if "last_loaded_file_name_teacher" not in st.session_state or st.session_state["last_loaded_file_name_teacher"] != tc_f.name:
                        st.session_state["cached_teacher_df"] = parsed_tc_df.sort_values(by=["교사_성명"]).reset_index(drop=True)
                        st.session_state["show_teacher_toast"] = True
                        st.session_state["last_loaded_file_name_teacher"] = tc_f.name
                except Exception as e: st.error(f"❌ 파일 해석 실패: {e}")
            
            if st.session_state.get("show_teacher_toast", False):
                st.toast("📥 교사 데이터가 오른쪽 표에 임시 로드되었습니다.")
                st.session_state["show_teacher_toast"] = False
            
            st.markdown('<div class="row1-fixed-status-box">', unsafe_allow_html=True)
            tc_status_placeholder = st.empty()
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.session_state.get("teacher_save_success_flag", False):
                tc_status_placeholder.markdown("<p style='color:#3b82f6; font-weight:700; margin:0; padding:0; font-size:14px; line-height:30px;'>🎉 교사 전체 권한 대장이 저장되었습니다.</p>", unsafe_allow_html=True)
                st.session_state["teacher_save_success_flag"] = False
            else:
                tc_status_placeholder.markdown("<p style='margin:0; padding:0; line-height:30px;'>&nbsp;</p>", unsafe_allow_html=True)
            
            for _ in range(7): st.write("")
            
            teacher_grid_cols = st.columns([5.0, 5.0])
            with teacher_grid_cols[0]:
                add_tc_trigger = st.button("➕ 교사 개별 신규 추가", use_container_width=True, key="m_single_add_tc_btn")
            with teacher_grid_cols[1]:
                save_tc_trigger = st.button("💾 교사 계정 저장", type="primary", use_container_width=True, key="master_teacher_save_btn")
                
            if add_tc_trigger: show_add_teacher_dialog()
                
        with layout_right:
            target_tc_render_df = st.session_state["cached_teacher_df"].copy()
            if target_tc_render_df.empty: target_tc_render_df = pd.DataFrame(columns=["교사_ID", "교사_성명", "비밀번호", "담당_과목"])
            if sel_tc_name != "전체 교직원 보기": target_tc_render_df = target_tc_render_df[target_tc_render_df["교사_성명"] == sel_tc_name]
            edited_tc_df = st.data_editor(target_tc_render_df, use_container_width=True, num_rows="dynamic", hide_index=True, key="master_tc_editor", height=650)
            
            if save_tc_trigger:
                with st.spinner("원격 데이터베이스에 교사 권한사항 갱신 중..."):
                    try:
                        supabase.table(teacher_table).delete().neq("교사_ID", "admin").execute()
                        clean_teachers = []
                        for record in edited_tc_df.to_dict(orient="records"):
                            if record.get("교사_ID") and record.get("교사_성명") and str(record.get("교사_성명")).strip() != "None":
                                if str(record["교사_ID"]).strip() != "admin":
                                    record["교사_ID"] = str(record["교사_ID"]).strip()
                                    record["교사_성명"] = str(record["교사_성명"]).strip()
                                    record["비밀번호"] = str(record.get("비밀번호", "1234")).strip()
                                    record["담당_과목"] = str(record["담당_과목"]).strip()
                                    clean_teachers.append(record)
                        if clean_teachers: supabase.table(teacher_table).insert(clean_teachers).execute()
                        st.session_state["teacher_file_uploader_key"] = f"tc_uploader_init_{int(time.time())}"
                        st.session_state["cached_teacher_df"] = pd.DataFrame(clean_teachers)
                        st.session_state["show_teacher_toast"] = False
                        st.session_state["teacher_save_success_flag"] = True 
                        time.sleep(0.2); st.rerun()
                    except Exception as e: st.error(f"❌ 저장 실패: {e}")
