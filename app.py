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
        
        /* 팝업창 잔상 버그 무조건 차단 */
        div[data-testid="stDialog"] { display: none !important; }
        iframe { display: none !important; }
        
        /* 🎯 학생 화면 전체를 500px 정중앙 전용 박스로 강력 구속 */
        .student-container {
            max-width: 500px !important;
            margin: 60px auto 0 auto !important;
            background-color: #ffffff !important;
            padding: 30px !important;
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
        
        h2 { color: #0f172a !important; font-weight: 800 !important; font-size: 22px !important; margin: 0; text-align: center; }
        h3 { font-size: 17px !important; font-weight: 700 !important; color: #1e293b !important; }
    </style>
""", unsafe_allow_html=True)

# 🎯 학생용 500px HTML 카드 박스 레이어 시작
st.markdown('<div class="student-container">', unsafe_allow_html=True)

st.markdown("<h2>🎒 수행평가 성적 확인 시스템</h2>", unsafe_allow_html=True)
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# --- 교사용 제어판 이동 버튼 추가 ---
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🔓 교사용 제어판", use_container_width=True):
        st.query_params.update(mode="admin")
        st.rerun()

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
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
                            scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                            st.success(f"🎉 {name_in} 학생의 조회 결과입니다.")
                            st.table(pd.DataFrame(scores))
                            
                            if df_st.loc[idx, '확인여부'] != "확인 완료":
                                df_st.loc[idx, '확인여부'], df_st.loc[idx, '확인시간'] = "확인 완료", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                df_st.to_csv(sf, index=False)
                        else: 
                            st.error("입력한 학생 정보 또는 비밀번호가 일치하지 않습니다.")

st.markdown('</div>', unsafe_allow_html=True) # HTML 카드 닫기