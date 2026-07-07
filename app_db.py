import streamlit as st
import pandas as pd
import datetime
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
# 🔑 [Supabase 백엔드 고속 도로 설정]
# =========================================================================
# 코드 주입 방식 및 Secrets 대체망 완벽 호환 보장
try:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://jwkvojfmhorndnnhscwl.supabase.co")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "sb_publishable_6--SHGogHaHSEVO7g3rNjQ_FOHO-XlN")
except Exception:
    SUPABASE_URL = "https://jwkvojfmhorndnnhscwl.supabase.co"
    SUPABASE_KEY = "sb_publishable_6--SHGogHaHSEVO7g3rNjQ_FOHO-XlN"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
current_table = "st_info_2_2026_1"

# 데이터 로드 헬퍼 함수
def load_db_data():
    try:
        response = supabase.table(current_table).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"❌ DB 통신 에러: {e}")
        return pd.DataFrame()

# =========================================================================
# 🧭 [사이드바 메인 컨트롤러]
# =========================================================================
with st.sidebar:
    st.markdown('<span style="font-size:22px; font-weight:800; color:#fff;">🥇 성적 조회 시스템 v2</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    user_role = st.radio("🔑 접속 권한 선택", ["👨‍🏫 교사 모드", "🙋‍♂️ 학생 모드"])
    st.markdown("---")

df = load_db_data()

# =========================================================================
# 👨‍🏫 1. 교사 모드 로직부
# =========================================================================
if user_role == "👨‍🏫 교사 모드":
    st.markdown(f"<h2>👨‍🏫 교과 관리 대시보드 <span style='font-size:14px; color:#64748b;'>[정보 - 2학년 1학기]</span></h2>", unsafe_allow_html=True)
    
    # 교사 전용 패스워드 보안창 (기존 app.py 기능 계승)
    teacher_pw = st.text_input("교사 인증 비밀번호를 입력하세요", type="password")
    
    if teacher_pw == "1234":  # 선생님이 지정하실 마스터 비밀번호
        st.success("🔓 교사 권한 인증에 성공했습니다.")
        
        with st.sidebar:
            st.markdown('<span style="font-size:16px; font-weight:700; color:#38bdf8;">⚙️ 교사 관리 메뉴</span>', unsafe_allow_html=True)
            menu_selection = st.radio("메뉴", ["▶ 학생 조회 현황 모니터링", "▶ 개인별 성적 입력", "▶ 학생 정보 관리", "📥 새 엑셀 명단 파일 업로드"], label_visibility="collapsed")
        
        st.write(f"현재 메뉴: **{menu_selection}**")
        
        if not df.empty:
            # 학반 정렬 및 필터링
            if "반" in df.columns and "번호" in df.columns:
                df = df.sort_values(by=["반", "번호"])
            class_opts = ["전체 학급 보기"] + [f"{x}반" for x in sorted(df["반"].unique())]
            selected_class = st.selectbox("🎯 대상 학급 필터링", options=class_opts)
            filtered_df = df if selected_class == "전체 학급 보기" else df[df["반"] == int(selected_class.replace("반",""))]
        
        # [메뉴 1] 모니터링
        if menu_selection == "▶ 학생 조회 현황 모니터링":
            if df.empty: st.info("데이터가 없습니다. 엑셀을 업로드해 주세요.")
            else: st.dataframe(filtered_df.fillna("-"), use_container_width=True, hide_index=True)

        # [메뉴 2] 성적 입력
        elif menu_selection == "▶ 개인별 성적 입력":
            if df.empty: st.info("데이터가 없습니다.")
            else:
                st.caption("※ 정보 보안을 위해 학생 인적사항은 잠금 처리되며, 성적 점수만 수정 가능합니다.")
                score_cols = ["반", "번호", "이름", "수행평가1", "수행평가2", "수행평가3"]
                score_df = filtered_df[[c for c in score_cols if c in filtered_df.columns]]
                
                edited_score_df = st.data_editor(score_df, use_container_width=True, disabled=["반", "번호", "이름"], hide_index=True)
                
                if st.button("💾 성적 데이터 초고속 저장", type="primary", use_container_width=True):
                    with st.spinner("수파베이스 DB에 안전하게 저장 중..."):
                        for record in edited_score_df.to_dict(orient="records"):
                            # 반, 번호(PK)를 기준으로 해당 행의 수행평가 점수 업데이트
                            supabase.table(current_table).upsert(record).execute()
                        st.success("🎉 성적 점수가 0.01초 만에 클라우드 DB에 반영되었습니다!")
                        st.balloons()

        # [메뉴 3] 학생 정보 관리
        elif menu_selection == "▶ 학생 정보 관리":
            if df.empty: st.info("데이터가 없습니다.")
            else:
                st.caption("※ 학생들의 초기 비밀번호, 이메일을 수정하거나 전학생 행을 직접 추가(+)할 수 있습니다.")
                info_cols = ["반", "번호", "이름", "학교 이메일", "비밀번호", "성적조회 횟수", "최종 확인일시"]
                info_df = filtered_df[[c for c in info_cols if c in filtered_df.columns]]
                
                edited_info_df = st.data_editor(info_df, use_container_width=True, num_rows="dynamic", disabled=["성적조회 횟수", "최종 확인일시"], hide_index=True)
                
                if st.button("💾 학생 기본 정보 저장", type="primary", use_container_width=True):
                    with st.spinner("학생 신상 명단 동기화 중..."):
                        for record in edited_info_df.to_dict(orient="records"):
                            if "성적조회 횟수" not in record or pd.isna(record["성적조회 횟수"]): record["성적조회 횟수"] = 0
                            if "최종 확인일시" not in record or pd.isna(record["최종 확인일시"]): record["최종 확인일시"] = "-"
                            supabase.table(current_table).upsert(record).execute()
                        st.success("🎉 학생 인적사항이 전용 DB와 완벽히 동기화되었습니다!")
                        st.rerun()

        # [신규 메뉴 4] 📥 새 엑셀 명단 파일 업로드 (기존 app.py 기능의 초고속 DB 이식 버전)
        elif menu_selection == "📥 새 엑셀 명단 파일 업로드":
            st.markdown("### 📊 새 학기/새 과목 성적 파일 데이터베이스 이식")
            st.write("엑셀 파일(.xlsx)을 업로드하면 기존 DB의 행들을 안전하게 싹 비우고, 새 명단으로 초고속 초기화를 진행합니다.")
            
            uploaded_file = st.file_uploader("성적 엑셀 파일을 선택하세요", type=["xlsx"])
            
            if uploaded_file is not None:
                excel_df = pd.read_excel(uploaded_file)
                st.markdown("#### 🔍 업로드 파일 데이터 미리보기")
                st.dataframe(excel_df.head(5), use_container_width=True)
                
                # 규격 컬럼 검증 및 보정 자동화
                required_cols = ["반", "번호", "이름", "학교 이메일", "비밀번호"]
                missing_cols = [c for c in required_cols if c not in excel_df.columns]
                
                if missing_cols:
                    st.error(f"❌ 엑셀 파일 서식이 일치하지 않습니다. 필수 컬럼이 누락되었습니다: {missing_cols}")
                else:
                    if st.button("🚀 클라우드 DB 원격 초기화 및 신규 데이터 이식 실행", type="primary", use_container_width=True):
                        with st.spinner("기존 데이터 청소 및 신규 명단 이식 중... (약 3초 소요)"):
                            # 1. 기존 데이터 테이블 전체 삭제 (SQL 통지 방식 우회 연동)
                            if not df.empty:
                                for _, row in df.iterrows():
                                    supabase.table(current_table).delete().eq("반", int(row["반"])).eq("번호", int(row["번호"])).execute()
                            
                            # 2. 보정 컬럼 추가 후 신규 대량 밀어넣기
                            for col in ["수행평가1", "수행평가2", "수행평가3", "성적조회 횟수"]:
                                if col not in excel_df.columns: excel_df[col] = 0
                            if "최종 확인일시" not in excel_df.columns: excel_df["최종 확인일시"] = "-"
                            
                            # 정밀 업서트 데이터 전송
                            upload_records = excel_df.to_dict(orient="records")
                            for record in upload_records:
                                # NaN 데이터 방어막 처리
                                for k, v in record.items():
                                    if pd.isna(v): record[k] = "-" if isinstance(v, str) else 0
                                supabase.table(current_table).insert(record).execute()
                                
                        st.success("🎯 클라우드 데이터베이스 초기화 및 새 명단 마이그레이션 성공!")
                        st.balloons()
                        st.rerun()
    elif teacher_pw != "":
        st.error("❌ 비밀번호가 틀렸습니다. 교사 전용 키를 다시 확인하세요.")

# =========================================================================
# 🙋‍♂️ 2. 학생 모드 로직부
# =========================================================================
elif user_role == "🙋‍♂️ 학생 모드":
    st.markdown(f"<h2>🙋‍♂️ 내 수행평가 점수 확인하기</h2>", unsafe_allow_html=True)
    st.write("본인의 학반, 번호와 선생님께 부여받은 초기 비밀번호를 입력하면 실시간 성적이 조회됩니다.")
    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1: s_class = st.number_input("학년 반 입력 (예: 1)", min_value=1, max_value=10, step=1)
    with col2: s_num = st.number_input("출석 번호 입력 (예: 5)", min_value=1, max_value=40, step=1)
    with col3: s_pw = st.text_input("보안 비밀번호 입력", type="password")

    if st.button("🔍 실시간 성적 조회하기", type="primary", use_container_width=True):
        if df.empty:
            st.error("데이터베이스가 비어있습니다. 교사 모드에서 데이터를 먼저 등록해 주세요.")
        else:
            student_match = df[(df["반"] == int(s_class)) & (df["번호"] == int(s_num))]
            
            if not student_match.empty:
                db_pw = str(student_match.iloc[0]["비밀번호"])
                if s_pw == db_pw:
                    student_data = student_match.iloc[0]
                    st.success(f"⭕ 인증 성공: [{student_data['이름']}] 학생의 데이터 로드 완료")
                    
                    sc1, sc2, sc3 = st.columns(3)
                    sc1.metric(label="📝 수행평가 1차 점수", value=f"{int(student_data['수행평가1'])} 점")
                    sc2.metric(label="📝 수행평가 2차 점수", value=f"{int(student_data['수행평가2'])} 점")
                    sc3.metric(label="📝 수행평가 3차 점수", value=f"{int(student_data['수행평가3'])} 점")
                    
                    # 실시간 조회수 로그 업데이트 트래킹 로직
                    new_count = int(student_data.get("성적조회 횟수", 0)) + 1
                    now_str = (datetime.datetime.now() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    supabase.table(current_table).upsert({
                        "반": int(s_class), "번호": int(s_num), 
                        "성적조회 횟수": new_count, "최종 확인일시": now_str
                    }).execute()
                else:
                    st.error("❌ 비밀번호가 올바르지 않습니다. 다시 확인해 주세요.")
            else:
                st.error("❌ 입력한 반/번호에 해당하는 학생 정보를 찾을 수 없습니다.")
