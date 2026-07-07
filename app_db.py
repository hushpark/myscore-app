import streamlit as st
import pandas as pd
from supabase import create_client, Client

# [최상단 규칙] 와이드 레이아웃 설정
st.set_page_config(page_title="수행평가 점수 확인 시스템 (Supabase)", layout="wide")

# =========================================================================
# 🎨 [디자인 가시성 패치] 네이비 & 화이트 관통 CSS
# =========================================================================
st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #f1f5f9 !important; }
        div[data-testid="stHeader"] { display: none !important; }
        
        /* 사이드바 스타일 */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] { 
            min-width: 280px !important; max-width: 280px !important; 
            background-color: #1e293b !important; 
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[role="radiogroup"] * {
            color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; opacity: 1 !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 16px !important; font-weight: 700 !important; line-height: 2.2 !important; }
        
        /* 테두리 시인성 강화 */
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-testid="stSelectbox"] > div[data-baseweb="select"] { 
            background-color: #ffffff !important; border: 1px solid #94a3b8 !important; border-radius: 6px !important; 
        }
        div[data-testid="stTextInput"] label p, div[data-testid="stSelectbox"] label p { font-weight: 800 !important; color: #1e293b !important; }
        h3 { color: #1e293b !important; font-weight: 700 !important; font-size: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 🔑 [Supabase 백엔드 도킹]
# =========================================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 과목 명 및 테이블 강제 지정
current_table = "st_info_2_2026_1"

# 데이터 로드 함수
def load_db_table():
    try:
        response = supabase.table(current_table).select("*").order("반").order("번호").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        return pd.DataFrame()

# =========================================================================
# 🧭 [시스템 메인 제어부] 교사/학생 모드 대전환 스위치
# =========================================================================
with st.sidebar:
    st.markdown('<span style="font-size:22px; font-weight:800; color:#fff;">🥇 성적 조회 시스템</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 시스템 접속 모드 선택
    user_role = st.radio("🔑 접속 권한 선택", ["👨‍🏫 교사 모드", "🙋‍♂️ 학생 모드"])
    st.markdown("---")

df = load_db_table()

if df.empty:
    st.warning("⚠️ DB 테이블에서 데이터를 로드하지 못했습니다. 수파베이스 대시보드 설정을 확인하세요.")
else:
    # ---------------------------------------------------------------------
    # 👨‍🏫 1. 교사 모드 진입
    # ---------------------------------------------------------------------
    if user_role == "👨‍🏫 교사 모드":
        with st.sidebar:
            st.markdown('<span style="font-size:16px; font-weight:700; color:#38bdf8;">⚙️ 교사 관리 메뉴</span>', unsafe_allow_html=True)
            menu_selection = st.radio("메뉴", ["▶ 학생 조회 현황 모니터링", "▶ 개인별 성적 입력", "▶ 학생 정보 관리"], label_visibility="collapsed")

        st.markdown(f"<h2>교과 관리 대시보드 <span style='font-size:14px; color:#64748b;'>[정보 - 2학년 1학기]</span></h2>", unsafe_allow_html=True)
        st.write(f"현재 메뉴: **{menu_selection}**")
        
        # 학반 필터링
        class_opts = ["전체 학급 보기"] + [f"{x}반" for x in sorted(df["반"].unique())]
        selected_class = st.selectbox("🎯 대상 학급 필터링", options=class_opts)
        filtered_df = df if selected_class == "전체 학급 보기" else df[df["반"] == int(selected_class.replace("반",""))]

        # [메뉴 1] 모니터링
        if menu_selection == "▶ 학생 조회 현황 모니터링":
            st.dataframe(filtered_df.fillna("-"), use_container_width=True, hide_index=True)

        # [메뉴 2] 성적 입력 (성적 컬럼만 열어두기)
        elif menu_selection == "▶ 개인별 성적 입력":
            st.caption("※ 정보 보안을 위해 학생 인적사항은 잠금 처리되며, 성적 점수만 수정 가능합니다.")
            score_cols = ["반", "번호", "이름", "수행평가1", "수행평가2", "수행평가3"]
            score_df = filtered_df[[c for c in score_cols if c in filtered_df.columns]]
            
            edited_score_df = st.data_editor(score_df, use_container_width=True, disabled=["반", "번호", "이름"], hide_index=True)
            
            if st.button("💾 성적 데이터 초고속 저장", type="primary", use_container_width=True):
                with st.spinner("수파베이스 DB에 안전하게 저장 중..."):
                    for record in edited_score_df.to_dict(orient="records"):
                        supabase.table(current_table).upsert(record).execute()
                    st.success("🎉 성적 점수가 0.01초 만에 전용 DB에 반영되었습니다!")
                    st.balloons()

        # [메뉴 3] 학생 정보 관리 (전학생 추가 및 신상 정보 제어)
        elif menu_selection == "▶ 학생 정보 관리":
            st.caption("※ 전학생 추가(+) 및 학생들의 초기 비밀번호, 이메일을 일괄 관리하는 칸입니다.")
            info_cols = ["반", "번호", "이름", "학교 이메일", "비밀번호", "성적조회 횟수", "최종 확인일시"]
            info_df = filtered_df[[c for c in info_cols if c in filtered_df.columns]]
            
            edited_info_df = st.data_editor(info_df, use_container_width=True, num_rows="dynamic", disabled=["성적조회 횟수", "최종 확인일시"], hide_index=True)
            
            if st.button("💾 학생 기본 정보 저장", type="primary", use_container_width=True):
                with st.spinner("학생 인적사항 동기화 중..."):
                    for record in edited_info_df.to_dict(orient="records"):
                        if "성적조회 횟수" not in record or pd.isna(record["성적조회 횟수"]): record["성적조회 횟수"] = 0
                        if "최종 확인일시" not in record or pd.isna(record["최종 확인일시"]): record["최종 확인일시"] = "-"
                        supabase.table(current_table).upsert(record).execute()
                    st.success("🎉 학생 신상 명단이 클라우드 DB와 일치화되었습니다!")
                    st.rerun()

    # ---------------------------------------------------------------------
    # 🙋‍♂️ 2. 학생 모드 진입 (개인 성적 조회 기능)
    # ---------------------------------------------------------------------
    elif user_role == "🙋‍♂️ 학생 모드":
        st.markdown(f"<h2>🙋‍♂️ 내 수행평가 점수 확인하기</h2>", unsafe_allow_html=True)
        st.write("본인의 학반, 번호와 지정된 초기 비밀번호를 입력하면 실시간 점수가 조회됩니다.")
        st.markdown("<hr>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1: s_class = st.number_input("학년 반 입력 (예: 1)", min_value=1, max_value=10, step=1)
        with col2: s_num = st.number_input("출석 번호 입력 (예: 5)", min_value=1, max_value=40, step=1)
        with col3: s_pw = st.text_input("보안 비밀번호 입력", type="password")

        if st.button("🔍 실시간 성적 조회하기", type="primary", use_container_width=True):
            # DB에서 해당 학생이 일치하는지 조회 행 검색
            student_match = df[(df["반"] == int(s_class)) & (df["번호"] == int(s_num))]
            
            if not student_match.empty:
                db_pw = str(student_match.iloc[0]["비밀번호"])
                if s_pw == db_pw:
                    student_data = student_match.iloc[0]
                    st.success(f"⭕ 인증 성공: [{student_data['이름']}] 학생의 성적 데이터 로드 완료")
                    
                    # 📊 성적 대시보드 카드 디자인 표출
                    sc1, sc2, sc3 = st.columns(3)
                    sc1.metric(label="📝 수행평가 1차 점수", value=f"{student_data['수행평가1']} 점")
                    sc2.metric(label="📝 수행평가 2차 점수", value=f"{student_data['수행평가2']} 점")
                    sc3.metric(label="📝 수행평가 3차 점수", value=f"{student_data['수행평가3']} 점")
                    
                    # 📈 조회수 카운트 실시간 DB 증가 및 로그 업데이트 마법
                    new_count = int(student_data["성적조회 횟수"]) + 1
                    import datetime
                    now_str = (datetime.datetime.now() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 수파베이스에 학생 조회 로그 즉시 업데이트 (렉 제로)
                    supabase.table(current_table).upsert({
                        "반": int(s_class), "번호": int(s_num), 
                        "성적조회 횟수": new_count, "최종 확인일시": now_str
                    }).execute()
                else:
                    st.error("❌ 비밀번호가 올바르지 않습니다. 다시 확인해 주세요.")
            else:
                st.error("❌ 입력한 반/번호에 해당하는 학생 정보를 찾을 수 없습니다.")
