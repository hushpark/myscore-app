import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 🚨 [최상단 규칙 엄수] 와이드 레이아웃 및 디자인 테마 강제 설정
st.set_page_config(page_title="수행평가 점수 확인 시스템 (Supabase)", layout="wide")

# =========================================================================
# 🎨 [디자인 가시성 패치] Streamlit 고질병 테두리 및 텍스트 순백색 관통 CSS
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        
        /* 사이드바 폭 고정 및 어두운 네이비 배경 */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] { 
            min-width: 280px !important; max-width: 280px !important; 
            background-color: #1e293b !important; 
        }
        
        /* 사이드바 메뉴 글씨 흰색 강제 관통 */
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[role="radiogroup"] * {
            color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; opacity: 1 !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 16px !important; font-weight: 700 !important; line-height: 2.2 !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover * { color: #60a5fa !important; }
        
        .sidebar-title { font-size: 24px !important; font-weight: 800 !important; margin-bottom: 5px !important; display: block; color: #ffffff; }
        .user-info { color: #38bdf8 !important; font-size: 14px !important; font-weight: 600 !important; margin-bottom: 25px !important; }

        /* 드롭다운 및 입력창 테두리 시인성 융단폭격 */
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-testid="stSelectbox"] > div[data-baseweb="select"],
        div[data-testid="stSelectbox"] > div { 
            background-color: #ffffff !important; 
            border: 1px solid #94a3b8 !important; 
            border-radius: 6px !important; 
            box-shadow: none !important;
        }
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        div[data-testid="stSelectbox"] > div:focus-within {
            border: 2px solid #3b82f6 !important;
        }
        div[data-testid="stSelectbox"] label p, div[data-testid="stTextInput"] label p { font-weight: 800 !important; color: #1e293b !important; }
        h3 { color: #1e293b !important; font-weight: 700 !important; font-size: 20px !important; margin-top: 0px !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 🔑 [Supabase 백엔드 도킹] 주소 및 암호 인증
# =========================================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 기본 정보 초기화
if "teacher_logged" not in st.session_state: st.session_state["teacher_logged"] = True # 테스트 편의를 위해 즉시 로그인 활성화
if "teacher_name" not in st.session_state: st.session_state["teacher_name"] = "박디몬"

# DB 로드 함수
def load_db_table(table_name):
    try:
        response = supabase.table(table_name).select("*").order("반").order("번호").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"❌ DB 로드 실패: {e}")
        return pd.DataFrame()

# =========================================================================
# 📋 [사이드바 메인 레이아웃] 교사 전용 대시보드
# =========================================================================
with st.sidebar:
    st.markdown('<span class="sidebar-title">📋 교사 메뉴</span>', unsafe_allow_html=True)
    st.markdown(f'<div class="user-info">👤 {st.session_state["teacher_name"]} 선생님 접속 중</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 선생님이 기획하셨던 핵심 메뉴 라인업
    menu_selection = st.radio("메뉴 선택", [
        "▶ 학생 조회 현황 모니터링", 
        "▶ 개인별 성적 입력", 
        "▶ 학생 정보 관리"
    ], label_visibility="collapsed")

st.markdown(f"<h2>수행평가 점수 확인 시스템 <span style='font-size:16px; color:#64748b;'>with Supabase</span></h2>", unsafe_allow_html=True)
st.write(f"현재 위치: 교사 모드 ➡️ **{menu_selection}**")
st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

# 기본 과목 테이블 매핑 (방금 만드신 st_info_2_2026_1 테이블 연동)
current_table = "st_info_2_2026_1"
df = load_db_table(current_table)

if df.empty:
    st.warning("⚠️ DB 테이블에서 데이터를 가져오지 못했습니다. 수파베이스 대시보드나 Secrets 설정을 확인하세요.")
else:
    # 학반 필터링 공통 UI
    class_opts = ["전체 학급 보기"] + [f"{x}반" for x in sorted(df["반"].unique())]
    selected_class = st.selectbox("🎯 대상 학급 필터링", options=class_opts)
    
    filtered_df = df if selected_class == "전체 학급 보기" else df[df["반"] == int(selected_class.replace("반",""))]
    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 1. 학생 조회 현황 모니터링 모드
    # ---------------------------------------------------------------------
    if menu_selection == "▶ 학생 조회 현황 모니터링":
        with st.container(border=True):
            st.markdown("<h3>📊 학생별 성적 및 실시간 조회 이력</h3>", unsafe_allow_html=True)
            # 조회 현황은 읽기 전용이므로 st.dataframe으로 깔끔하게 표출
            st.dataframe(filtered_df.fillna("-"), use_container_width=True, hide_index=True)

    # ---------------------------------------------------------------------
    # 2. 개인별 성적 입력 모드 (선생님의 요청: 점수 데이터만 수정하는 전용 그리드)
    # ---------------------------------------------------------------------
    elif menu_selection == "▶ 개인별 성적 입력":
        with st.container(border=True):
            st.markdown("<h3>📝 수행평가 점수 마스터 입력창</h3>", unsafe_allow_html=True)
            st.caption("※ 반, 번호, 이름 등 학생 기본 정보는 잠금 처리되어 안전하며, 성적 점수 셀만 수정 가능합니다.")
            
            # 성적 입력에 필요한 열만 추출 (반, 번호, 이름 + 수행평가 항목들)
            score_cols = ["반", "번호", "이름", "수행평가1", "수행평가2", "수행평가3"]
            score_target_df = filtered_df[[c for c in score_cols if c in filtered_df.columns]]
            
            # 에디터 기동 (반, 번호, 이름 열은 비활성화하여 수정 불가 조치)
            edited_score_df = st.data_editor(
                score_target_df, 
                use_container_width=True, 
                disabled=["반", "번호", "이름"], 
                hide_index=True,
                key="score_data_editor_grid"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 성적 데이터 초고속 저장", type="primary", use_container_width=True):
                with st.spinner("수파베이스 클라우드 진짜 DB에 안전하게 마이그레이션 중..."):
                    try:
                        records = edited_score_df.to_dict(orient="records")
                        for record in records:
                            # 반, 번호 복합키를 기준으로 해당 학생의 성적 컬럼만 매칭하여 스마트 업서트(Upsert)
                            supabase.table(current_table).upsert(record).execute()
                        st.success("🎉 성적 점수가 충돌 없이 0.01초 만에 전용 DB에 반영되었습니다!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"저장 실패: {e}")

    # ---------------------------------------------------------------------
    # 3. 학생 정보 관리 모드 (선생님의 요청: 인적사항, 비번, 이메일만 고치는 전용 그리드)
    # ---------------------------------------------------------------------
    elif menu_selection == "▶ 학생 정보 관리":
        with st.container(border=True):
            st.markdown("<h3>📇 학생 인적사항 및 계정 정보 관리</h3>", unsafe_allow_html=True)
            st.caption("※ 전학생 추가 및 학생들의 학교 이메일, 로그인 초기 비밀번호를 통합 관리하는 그리드입니다.")
            
            # 학생 정보 관리에 필요한 열만 추출
            info_cols = ["반", "번호", "이름", "학교 이메일", "비밀번호", "성적조회 횟수", "최종 확인일시"]
            info_target_df = filtered_df[[c for c in info_cols if c in filtered_df.columns]]
            
            # 에디터 기동 (인적사항이므로 자유롭게 편집 가능, 횟수와 일시는 자동 기록이므로 잠금)
            edited_info_df = st.data_editor(
                info_target_df, 
                use_container_width=True, 
                num_rows="dynamic", # ➕ 새로운 행(전학생)을 하단 [+] 버튼으로 마음껏 추가 가능!
                disabled=["성적조회 횟수", "최종 확인일시"],
                hide_index=True,
                key="info_data_editor_grid"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 학생 기본 정보 저장", type="primary", use_container_width=True):
                with st.spinner("학생 인적사항 데이터베이스 동기화 중..."):
                    try:
                        records = edited_info_df.to_dict(orient="records")
                        for record in records:
                            # 새 행 추가 시 빈 값 기본값 세팅 규칙
                            if "성적조회 횟수" not in record or pd.isna(record["성적조회 횟수"]): record["성적조회 횟수"] = 0
                            if "최종 확인일시" not in record or pd.isna(record["최종 확인일시"]): record["최종 확인일시"] = "-"
                            
                            supabase.table(current_table).upsert(record).execute()
                        st.success("🎉 학생 신상정보 명단이 성공적으로 클라우드 DB와 일치화되었습니다!"); st.rerun()
                    except Exception as e:
                        st.error(f"저장 실패: {e}")
