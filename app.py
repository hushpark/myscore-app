import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import glob
import re

# 파일 경로 정의
CONFIG_FILE_MAIN = "master_subjects.csv"
META_FILE = "admin_meta.csv"

# --- [보안] 암호 복잡도 검사 함수 ---
def is_strong_password(pw):
    if len(pw) < 12:
        return False, "❌ 최소 12자리 이상이어야 합니다."
    if not re.search("[a-zA-Z]", pw):
        return False, "❌ 영문자가 포함되어야 합니다."
    if not re.search("[0-9]", pw):
        return False, "❌ 숫자가 포함되어야 합니다."
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", pw):
        return False, "❌ 특수문자가 포함되어야 합니다."
    return True, "✅ 사용 가능한 안전한 암호 조건입니다."

# --- 데이터 로드/저장 함수 ---
def load_master_subjects():
    default_structure = {
        "인문·사회군": ["국어", "영어", "사회", "역사", "도덕", "한문", "중국어"],
        "수리·과학군": ["수학", "과학", "기술·가정", "정보"],
        "예체능군": ["음악", "미술", "체육"]
    }
    if os.path.exists(CONFIG_FILE_MAIN):
        try:
            df = pd.read_csv(CONFIG_FILE_MAIN)
            for _, row in df.iterrows():
                group = row['교과군']
                sub = row['과목명']
                if group in default_structure and sub not in default_structure[group]:
                    default_structure[group].append(sub)
        except: pass
    return default_structure

def save_new_subject_to_master(group, subject):
    new_data = pd.DataFrame([{"교과군": group, "과목명": subject}])
    if os.path.exists(CONFIG_FILE_MAIN):
        try:
            df = pd.read_csv(CONFIG_FILE_MAIN)
            if not ((df['교과군'] == group) & (df['과목명'] == subject)).any():
                pd.concat([df, new_data], ignore_index=True).to_csv(CONFIG_FILE_MAIN, index=False)
        except: new_data.to_csv(CONFIG_FILE_MAIN, index=False)
    else: new_data.to_csv(CONFIG_FILE_MAIN, index=False)

def load_admin_password():
    if os.path.exists(META_FILE):
        try:
            df = pd.read_csv(META_FILE)
            return str(df.iloc[0]['password']).strip()
        except: pass
    return "1234"

def save_admin_password(new_pw):
    pd.DataFrame([{"password": str(new_pw).strip()}]).to_csv(META_FILE, index=False)

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

def reset_all_data():
    for f in glob.glob("config_*") + glob.glob("students_*") + [CONFIG_FILE_MAIN, META_FILE]:
        try: os.remove(f)
        except: pass
    st.session_state.clear()
    st.rerun()

# --- 앱 설정 ---
st.set_page_config(page_title="교과용 성적 확인 도우미 v7", layout="wide")

# 💡 [디자인 완전 개조 CSS] 
# 기존의 불안정했던 지정을 버리고, 텍스트 입력과 버튼을 감싸는 Form 자체의 최대 너비를 340px로 강제 고정했습니다.
st.markdown("""
    <style>
        div[data-testid="stHeader"] {height: 0px !important; min-height: 0px !important; padding: 0px !important;}
        div.block-container {padding-top: 5rem !important; padding-bottom: 0rem !important;}
        .stTable th, .stTable td, div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th {
            text-align: center !important; vertical-align: middle !important;
        }
        
        /* 💡 로그인 폼 자체의 크기를 강제로 딱 절반(340px)으로 조절하고 가운데로 모으는 핵심 장치 */
        div[data-testid="stForm"] {
            max-width: 340px !important;
            margin: 0 auto !important;
            border: none !important; /* 지저분한 외곽 테두리선 삭제 */
            padding: 0px !important;  /* 여백 정돈 */
        }
        
        /* 타이틀 구역 정중앙 고정 */
        .admin-top-title { text-align: center !important; width: 100% !important; }
        .pw-guide { font-size: 12px; color: #57606a; line-height: 1.5; margin-top: 10px; }
        .pw-example { font-family: monospace; background: #eef1f4; padding: 1px 4px; border-radius: 3px; }
        
        label div p { font-size: 14px !important; font-weight: 500 !important; color: #24292f !important; }
        div[data-testid="stTextInput"] input { font-size: 14px !important; padding: 6px 10px !important; }
    </style>
""", unsafe_allow_html=True)

query_params = st.query_params
is_admin_mode = query_params.get("mode") == "admin"

SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS = ["학년을 선택하세요.", "1학년", "2학년", "3학년"]
CURRENT_ADMIN_PW = load_admin_password()

# ==========================================
# A. 선생님 관리자 화면 (?mode=admin)
# ==========================================
if is_admin_mode:
    st.markdown('<html lang="ko"></html>', unsafe_allow_html=True)
    
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if not st.session_state["admin_logged_in"]:
        col_space1, col_center, col_space2 = st.columns([1, 2, 1])
        with col_center:
            st.markdown("<div class='admin-top-title'><h3 style='margin-bottom:0px;'>⚙️ 선생님 전용 통합 관리자 페이지</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: gray; font-size: 14px; margin-top:5px;'>여러 교과와 학년별 성적 데이터베이스를 스위칭하며 관리하는 공간입니다.</p><br></div>", unsafe_allow_html=True)
            
            # 💡 [구조 변경] 입력창과 버튼을 하나의 st.form으로 묶어 CSS가 완벽하게 50% 크기로 지배하도록 설계했습니다.
            with st.form("admin_login_form_container"):
                admin_pw = st.text_input("관리자 인증 비밀번호를 입력하세요", type="password")
                st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
                login_submitted = st.form_submit_button("로그인", use_container_width=True, type="primary")
            
            if login_submitted or (admin_pw == CURRENT_ADMIN_PW):
                if admin_pw == CURRENT_ADMIN_PW:
                    st.session_state["admin_logged_in"] = True
                    st.rerun()
                elif admin_pw: 
                    st.error("❌ 비밀번호가 올바르지 않습니다.")

    else:
        # 로그인 완료 후 대시보드는 1번 사진처럼 100% 와이드 화면으로 시원하게 출력됩니다.
        st.title("⚙️ 교과·학년 통합 제어 센터")
        st.markdown("#### 🛠️ [단계 1] 획기적인 교과군별 과목 지정")
        
        if "sel_group_idx" not in st.session_state: st.session_state.sel_group_idx = 0
        if "sel_sub_idx" not in st.session_state: st.session_state.sel_sub_idx = 0
        if "sel_grade_idx" not in st.session_state: st.session_state.sel_grade_idx = 0

        c1, c2, c3, c4 = st.columns([1.2, 1.2, 1, 0.8])
        with c1:
            g_opts = ["교과군을 선택하세요.", "인문·사회군", "수리·과학군", "예체능군", "➕ [신규 과목 개설]"]
            sel_g = st.selectbox("📂 1단계: 교과군", options=g_opts, index=st.session_state.sel_group_idx)
        with c2:
            final_sub = ""
            if sel_g == "➕ [신규 과목 개설]":
                t_g = st.selectbox("추가 위치", ["인문·사회군", "수리·과학군", "예체능군"])
                f_sub = st.text_input("✏️ 새 과목명", placeholder="정보과학").strip()
                final_sub = f_sub
            elif sel_g != "교과군을 선택하세요.":
                s_opts = ["과목을 선택하세요."] + SUBJECT_MAP[sel_g]
                idx_s = st.session_state.sel_sub_idx if st.session_state.sel_sub_idx < len(s_opts) else 0
                sel_s = st.selectbox("📚 2단계: 세부 과목", options=s_opts, index=idx_s)
                if sel_s != "과목을 선택하세요.": final_sub = sel_s
            else: st.selectbox("📚 2단계: 세부 과목", ["교과군을 먼저 선택하세요."], disabled=True)
        with c3:
            sel_gr = st.selectbox("🎓 3단계: 관리 학년", options=GRADE_OPTIONS, index=st.session_state.sel_grade_idx)
            final_gr = sel_gr.replace("학년", "") if sel_gr != "학년을 선택하세요." else ""
        with c4:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 영역 활성화", use_container_width=True):
                if final_sub and final_gr:
                    if sel_g == "➕ [신규 과목 개설]": save_new_subject_to_master(t_g, final_sub)
                    st.session_state.active_subject, st.session_state.active_grade = final_sub, final_gr
                    st.session_state.sel_group_idx = g_opts.index(sel_g)
                    if sel_g != "➕ [신규 과목 개설]": st.session_state.sel_sub_idx = s_opts.index(final_sub)
                    st.session_state.sel_grade_idx = GRADE_OPTIONS.index(sel_gr)
                    st.rerun()
                else: st.error("과목/학년을 선택하세요.")

        if "active_subject" in st.session_state and st.session_state.active_subject:
            sub, grd = st.session_state.active_subject, st.session_state.active_grade
            cf, sf = get_file_names(sub, grd)
            conf = load_config(cf)
            
            st.markdown("---")
            st.markdown(f"### 📍 작업 중: <span style='color:#1E88E5;'>[{sub}] {grd}학년</span>", unsafe_allow_html=True)
            
            st.markdown("#### 📌 [파트 1] 학기 및 평가 세팅")
            col_t, _ = st.columns([1.5, 1.5])
            with col_t:
                y_opts = ["학년도/학기를 선택하세요."] + [f"{y}학년도 {t}학기" for y in range(2024, 2030) for t in [1, 2]] + ["➕ [직접 입력]"]
                saved_s = conf['학기통합명'] if conf else "학년도/학기를 선택하세요."
                idx_t = y_opts.index(saved_s) if saved_s in y_opts else y_opts.index("➕ [직접 입력]") if saved_s != "학년도/학기를 선택하세요." else 0
                sel_t = st.selectbox("대상 학기", y_opts, index=idx_t)
                final_t = st.text_input("✏️ 직접 입력", value=saved_s if idx_t == len(y_opts)-1 else "") if sel_t == "➕ [직접 입력]" else sel_t

            st.markdown("**🏫 담당 학급(반)**")
            saved_cl = [int(x) for x in str(conf['선택된반 목록']).split(",")] if conf else []
            sel_cl = []
            cols_cl = st.columns(6)
            for i in range(1, 13):
                with cols_cl[(i-1)%6]:
                    if st.checkbox(f"{i}반", value=i in saved_cl): sel_cl.append(i)

            st.markdown("**✍️ 평가 항목**")
            n_item = st.number_input("평가 항목 개수", 0, 10, int(conf['항목개수']) if conf else 0)
            item_names = []
            if n_item > 0:
                cols_i = st.columns(3)
                for i in range(1, n_item + 1):
                    with cols_i[(i-1)%3]:
                        item_names.append(st.text_input(f"{i}번 이름", value=conf.get(f'항목{i}_이름', "") if conf else ""))

            st.markdown("#### 📂 [파트 2] 데이터 제어")
            ready = final_t != "학년도/학기를 선택하세요." and sel_cl and n_item > 0 and all(item_names)
            
            c1, c2, c3 = st.columns([1.5, 1.5, 1])
            with c1:
                if ready:
                    if st.button(f"💾 [{sub}] 설정 저장"):
                        d = {"교과명":sub, "학년":grd, "학기통합명":final_t, "선택된반 목록":",".join(map(str, sorted(sel_cl))), "항목개수":n_item}
                        for i, name in enumerate(item_names): d[f"항목{i+1}_이름"] = name
                        pd.DataFrame([d]).to_csv(cf, index=False)
                        st.success("저장 완료!")
                else: st.button("⚠️ 설정 미완료", disabled=True)
            with c2:
                if st.button("➕ 다른 과목 추가하기"):
                    st.session_state.active_subject = None
                    st.session_state.sel_group_idx = 0
                    st.rerun()
            with c3:
                if st.button("🗑️ 전체 시스템 포맷"): reset_all_data()

            up_f = st.file_uploader("📁 성적 CSV 업로드", type="csv")
            if up_f:
                try:
                    df_up = pd.read_csv(up_f, encoding='cp949')
                    df_up.to_csv(sf, index=False)
                    st.success("성적 데이터 연동 완료!")
                except: st.error("파일 형식을 확인하세요 (CP949/UTF-8)")

        st.markdown("<br><br><br>---", unsafe_allow_html=True)
        st.markdown("### 🔐 관리자 인증 암호 변경 (2중 교차 검증)")
        
        col_pw1, col_pw2, col_pw_btn = st.columns([1.5, 1.5, 1.2])
        with col_pw1:
            new_pw = st.text_input("1. 새 암호 입력", type="password", key="new_pw_static")
        with col_pw2:
            confirm_pw = st.text_input("2. 새 암호 확인", type="password", key="confirm_pw_static")
            
        is_valid, msg = is_strong_password(new_pw)
        
        if new_pw:
            if new_pw == confirm_pw and is_valid:
                st.success("✅ 조건 통과! 두 암호가 일치합니다.")
            elif confirm_pw and new_pw != confirm_pw:
                st.error("❌ 암호 확인 칸이 일치하지 않습니다.")
            else:
                st.warning(msg)
                
        st.markdown("""<div class="pw-guide">
        <b>[설정 규칙]</b> 최소 12자 이상 필수 & 영문, 숫자, 특수기호 조합 필수<br>
        <b>[안전 암호 예시]</b> <span class="pw-example">teacher!@2026info</span> | <span class="pw-example">pass#$99grade!!</span> | <span class="pw-example">study**24safe##</span>
        </div>""", unsafe_allow_html=True)

        with col_pw_btn:
            can_submit = is_valid and (new_pw == confirm_pw)
            st.markdown("<div style='height:2px;'></div>", unsafe_allow_html=True)
            if st.button("🔒 새로운 암호로 즉시 변경", disabled=not can_submit, use_container_width=True, type="primary"):
                save_admin_password(new_pw)
                st.toast("🎉 관리자 암호가 성공적으로 변경되었습니다!")
                st.success("🎉 변경 성공! 새 비밀번호가 활성화되었습니다.")

# ==========================================
# B. 학생 화면 (기본)
# ==========================================
else:
    col_l, col_r = st.columns([6, 1])
    with col_l: st.title("🎒 수행평가 성적 확인 시스템")
    with col_r:
        if st.button("⚙️ 관리자"):
            st.query_params.update(mode="admin")
            st.rerun()
    
    st.header("📝 개인별 성적 조회")
    active_dbs = get_active_databases()
    
    if not active_dbs:
        st.warning("등록된 데이터가 없습니다.")
    else:
        opts_s = ["과목을 선택하세요."] + [f"📚 {d['subject']} ({d['grade']})" for d in active_dbs]
        sel_s = st.selectbox("조회할 과목 선택", opts_s)
        
        if sel_s != "과목을 선택하세요.":
            db = active_dbs[opts_s.index(sel_s)-1]
            cf, sf = get_file_names(db['subject'], db['grade'].replace("학년",""))
            config = load_config(cf)
            
            st.info(f"🧬 **{config['교과명']}** | **{config['학기통합명']}**")
            
            with st.form("login"):
                classes = [f"{x.strip()}반" for x in str(config['선택된반 목록']).split(",")]
                c1, c2 = st.columns(2)
                with c1: b_sel = st.selectbox("반", classes)
                with c2: n_sel = st.number_input("번호", 1, 50, 1)
                name_in = st.text_input("이름")
                pw_in = st.text_input("비밀번호", type="password")
                if st.form_submit_button("점수 확인"):
                    df_st = load_students(sf)
                    if df_st.empty: st.error("성적 파일이 없습니다.")
                    else:
                        res = df_st[(df_st['반']==int(b_sel.replace("반",""))) & (df_st['번호']==n_sel) & (df_st['이름']==name_in) & (df_st['비밀번호'].astype(str)==str(pw_in))]
                        if not res.empty:
                            idx = res.index[0]
                            scores = {config[f'항목{i+1}_이름']: [df_st.loc[idx, config[f'항목{i+1}_이름']]] for i in range(int(config['항목개수']))}
                            st.success(f"🎉 {name_in} 학생의 점수입니다.")
                            st.table(pd.DataFrame(scores))
                            if df_st.loc[idx, '확인여부'] != "확인 완료":
                                df_st.loc[idx, '확인여부'], df_st.loc[idx, '확인시간'] = "확인 완료", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                df_st.to_csv(sf, index=False)
                        else: st.error("정보가 일치하지 않습니다.")