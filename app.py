import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import glob

# 파일 경로 정의
CONFIG_FILE_MAIN = "master_subjects.csv"

def get_file_names(subject, grade):
    safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")
    return f"config_{safe_subject}_{grade}grade.csv", f"students_{safe_subject}_{grade}grade.csv"

def load_config(file):
    if os.path.exists(file):
        try: return pd.read_csv(file).iloc[0].to_dict()
        except: return None
    return None

def load_students(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

def get_active_databases():
    active_list = []
    for f in glob.glob("config_*_*grade.csv"):
        try:
            parts = f.replace("config_", "").replace("grade.csv", "").split("_")
            if len(parts) >= 2:
                active_list.append({"subject": parts[0].replace("_", " "), "grade": f"{parts[-1]}학년"})
        except: pass
    return active_list

# --- 앱 설정 ---
st.set_page_config(page_title="수행평가 성적 확인 시스템", layout="wide")

st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        div[data-testid="stHeader"] {height: 0px !important; display:none;}
        
        /* 팝업창 잔상으로 상단에 생기던 빈 사각형 투명 버그 완벽 박멸 */
        div[data-testid="stDialog"] { display: none !important; opacity: 0 !important; }
        iframe { display: none !important; }
        
        /* 🎯 [선생님 요청 반영] 학생 화면 전체 컴포넌트를 가로 600px 중앙 집중형 카드로 구속 */
        .student-container {
            max-width: 600px !important;
            margin: 60px auto 0 auto !important;
            background-color: #ffffff !important;
            padding: 35px !important;
            border-radius: 14px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        }
        
        /* 내부 Form 기본 테두리 무효화 */
        .student-container div[data-testid="stForm"] {
            border: none !important;
            padding: 0px !important;
            box-shadow: none !important;
            max-width: 100% !important;
        }
        
        /* 💡 [선생님 요청 반영] 교사용 제어판 이동 단추 슬림화 및 화면 우측 가이드라인 라인 완전 밀착 */
        div.stButton > button[key="go_to_admin_btn"] {
            width: fit-content !important;
            min-width: auto !important;
            padding: 4px 14px !important;
            font-size: 15px !important; /* 조회할 과목 선택 글씨 스케일과 매칭 */
            float: right !important;
            border-radius: 6px !important;
            border: 1px solid #cbd5e1 !important;
            color: #475569 !important;
            background-color: #ffffff !important;
        }
        div.stButton > button[key="go_to_admin_btn"]:hover {
            background-color: #f1f5f9 !important;
            border-color: #94a3b8 !important;
        }
        
        /* 600px 박스 내부 수평 균형을 위한 상단 타이틀-버튼 묶음 Flex 정의 */
        .header-flex-wrapper {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            width: 100%;
        }
        
        h2 { color: #0f172a !important; font-weight: 800 !important; font-size: 23px !important; margin: 0 !important; padding: 0 !important; }
        h3 { font-size: 18px !important; font-weight: 700 !important; color: #1e293b !important; }
    </style>
""", unsafe_allow_html=True)

# 🎯 학생용 600px HTML 카드 박스 레이어 시작
st.markdown('<div class="student-container">', unsafe_allow_html=True)

# 🎯 [버그 해결] 600px 박스 안에서 타이틀과 단추가 절대로 깨지거나 밀리지 않는 Flex 구조 정렬
st.markdown('<div class="header-flex-wrapper"><h2>🎒 수행평가 성적 확인 시스템</h2>', unsafe_allow_html=True)

# 🎯 [부활 및 연동] 교사용 화면(app_teacher)으로 진입하는 버튼 코드 강제 장착 완료!
if st.button("🔓 교사용 제어판", key="go_to_admin_btn"):
    st.query_params.update(mode="admin")
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### 📝 개인별 성적 조회")

active_dbs = get_active_databases()
if not active_dbs:
    st.warning("현재 등록된 성적 데이터가 없습니다.")
else:
    opts_s = ["과목을 선택하세요."] + [f"📚 {d['subject']} ({d['grade']})" for d in active_dbs]
    sel_s = st.selectbox("조회할 과목 선택", opts_s, label_visibility="collapsed", key="student_select_sub")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    if sel_s != "과목을 선택하세요.":
        db = active_dbs[opts_s.index(sel_s)-1]
        cf, sf = get_file_names(db['subject'], db['grade'].replace("학년",""))
        config = load_config(cf)
        
        if config:
            st.success(f"🧬 **{config['교과명']}** | **{config['학기통합명']}**")
            
            with st.form("login_form"):
                classes = [f"{x.strip()}반" for x in str(config['선택된반 목록']).split(",")] if '선택된반 목록' in config else ["1반"]
                
                c1, c2, c3 = st.columns(3)
                with c1: b_in = st.selectbox("반", classes)
                with c2: n_in = st.number_input("번호", 1, 50, 1)
                with c3: name_in = st.text_input("이름", placeholder="홍길동")
                
                pw_in = st.text_input("비밀번호", type="password", placeholder="비밀번호")
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                
                if st.form_submit_button("🔍 내 점수 확인하기", use_container_width=True):
                    df_st = load_students(sf)
                    if df_st.empty: 
                        st.error("성적 데이터가 아직 연동되지 않은 교과입니다.")
                    else:
                        res = df_st[(df_st['반']==int(b_in.replace("반",""))) & (df_st['번호']==n_in) & (df_st['이름']==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                        if not res.empty:
                            idx = res.index[0]
                            scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_is_strong_password' if f'항목{i+1}_이름' not in df_st.columns else f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                            
                            # 순정 명렬 데이터 바인딩
                            scores = {}
                            for i in range(int(config['항목개수'])):
                                h_name = config.get(f'항목{i+1}_이름', f'항목{i+1}')
                                if h_name in df_st.columns:
                                    scores[h_name] = [df_st.loc[idx, h_name]]
                                    
                            st.success(f"🎉 {name_in} 학생의 조회 결과입니다.")
                            st.table(pd.DataFrame(scores))
                            
                            if df_st.loc[idx, '확인여부'] != "확인 완료":
                                df_st.loc[idx, '확인여부'], df_st.loc[idx, '확인시간'] = "확인 완료", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                df_st.to_csv(sf, index=False)
                        else: 
                            st.error("입력한 학생 정보 또는 비밀번호가 일치하지 않습니다.")

st.markdown('</div>', unsafe_allow_html=True) # HTML 카드 닫기