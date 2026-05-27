import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import glob

# 파일 경로 정의
CONFIG_FILE_MAIN = "master_subjects.csv"

# --- 직접 입력된 커스텀 과목 로드/저장 함수 ---
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
        except:
            pass
    return default_structure

def save_new_subject_to_master(group, subject):
    if not group or not subject: return
    new_data = pd.DataFrame([{"교과군": group, "과목명": subject}])
    if os.path.exists(CONFIG_FILE_MAIN):
        try:
            df = pd.read_csv(CONFIG_FILE_MAIN)
            if not ((df['교과군'] == group) & (df['과목명'] == subject)).any():
                pd.concat([df, new_data], ignore_index=True).to_csv(CONFIG_FILE_MAIN, index=False)
        except:
            new_data.to_csv(CONFIG_FILE_MAIN, index=False)
    else:
        new_data.to_csv(CONFIG_FILE_MAIN, index=False)

# --- 동적 파일 경로 생성 함수 ---
def get_file_names(subject, grade):
    safe_subject = "".join([c for c in subject if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).strip()
    safe_subject = safe_subject.replace(" ", "_")
    config_file = f"config_{safe_subject}_{grade}grade.csv"
    student_file = f"students_{safe_subject}_{grade}grade.csv"
    return config_file, student_file

def load_config(config_file):
    if os.path.exists(config_file):
        try:
            return pd.read_csv(config_file).iloc[0].to_dict()
        except:
            return None
    return None

def load_students(student_file):
    if os.path.exists(student_file):
        return pd.read_csv(student_file)
    return pd.DataFrame()

def get_active_databases():
    active_list = []
    files = glob.glob("config_*_*grade.csv")
    for f in files:
        try:
            parts = f.replace("config_", "").replace("grade.csv", "").split("_")
            if len(parts) >= 2:
                grade = parts[-1]
                subject = "_".join(parts[:-1])
                subject_display = subject.replace("_", " ")
                active_list.append({
                    "subject": subject_display,
                    "grade": f"{grade}학년"
                })
        except:
            pass
    return active_list

def reset_all_data():
    for f in glob.glob("config_*_*grade.csv") + glob.glob("students_*_*grade.csv") + [CONFIG_FILE_MAIN]:
        try: os.remove(f)
        except: pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 앱 기본 설정 ---
st.set_page_config(page_title="교과용 성적 확인 도우미 v7", layout="wide")

# 💡 [디자인 업그레이드 핵심 CSS]
# 깃허브 로그인 박스 특유의 입체적인 사각형 테두리, 배경색, 그림자 라인을 완벽하게 모방해 적용했습니다.
st.markdown("""
    <style>
        div[data-testid="stHeader"] {height: 0px !important; min-height: 0px !important; padding: 0px !important;}
        div.block-container {padding-top: 2.5rem !important; padding-bottom: 0rem !important;}
        .stTable th, .stTable td, div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th {
            text-align: center !important; vertical-align: middle !important;
        }
        
        /* 깃허브 감성 플로팅 박스 스타일 커스텀 */
        .github-box {
            background-color: #f6f8fa;
            border: 1px solid #d0d7de;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

try:
    is_admin_mode = st.query_params.get("mode") == "admin"
except AttributeError:
    query_all = st.experimental_get_query_params()
    is_admin_mode = query_all.get("mode", [None])[0] == "admin"

# 마스터 데이터베이스 로드
SUBJECT_MAP = load_master_subjects()
GRADE_OPTIONS_ADMIN = ["학년을 선택하세요.", "1학년", "2학년", "3학년"]

# ==========================================
# A. 선생님 관리자 화면 (?mode=admin)
# ==========================================
if is_admin_mode:
    st.markdown('<html lang="ko"></html>', unsafe_allow_html=True)
    
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    # 💡 로그인 전 화면: 깃허브와 똑같은 정중앙 미니멀 상자 양식 디자인 구현
    if not st.session_state["admin_logged_in"]:
        col_space1, col_center, col_space2 = st.columns([1.2, 1.6, 1.2])
        
        with col_center:
            # 상단 전용 아이콘 및 타이틀
            st.markdown("<h3 style='text-align: center; margin-bottom: 5px;'>⚙️ Sign in to Admin</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #57606a; font-size: 14px; margin-top: 0px;'>선생님 전용 통합 관리자 페이지</p>", unsafe_allow_html=True)
            
            # 깃허브 상자 시작 HTML 정의
            st.markdown('<div class="github-box">', unsafe_allow_html=True)
            
            # 상자 내부에 정렬되는 패스워드 입력창
            admin_pw = st.text_input("관리자 인증 비밀번호를 입력하세요 (Password)", type="password")
            
            # 버튼을 누르거나 엔터를 치면 동작하도록 깔끔하게 흐름 제어
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            login_btn = st.button("Sign in", use_container_width=True, type="primary")
            
            # 깃허브 상자 마감 HTML 정의
            st.markdown('</div>', unsafe_allow_html=True)
            
            if login_btn or (admin_pw == "1234"):
                if admin_pw == "1234":
                    st.session_state["admin_logged_in"] = True
                    st.rerun()
                elif admin_pw:
                    st.error("❌ 비밀번호가 올바르지 않습니다.")

    # 로그인 성공 후
    else:
        st.title("⚙️ 교과·학년 통합 제어 센터")
        st.markdown("#### 🛠️ [단계 1] 획기적인 교과군별 과목 지정")
        
        if "sel_group_idx" not in st.session_state: st.session_state.sel_group_idx = 0
        if "sel_sub_idx" not in st.session_state: st.session_state.sel_sub_idx = 0
        if "sel_grade_idx" not in st.session_state: st.session_state.sel_grade_idx = 0

        col_group, col_sub, col_grade, col_btn = st.columns([1.2, 1.2, 1, 0.8])
        
        with col_group:
            group_options = ["교과군을 선택하세요.", "인문·사회군", "수리·과학군", "예체능군", "➕ [신규 과목 개설]"]
            selected_group = st.selectbox("📂 1단계: 교과군 분류", options=group_options, index=st.session_state.sel_group_idx)
            
        with col_sub:
            final_subject = ""
            if selected_group == "➕ [신규 과목 개설]":
                target_group_for_new = st.selectbox("어디에 추가할까요?", options=["인문·사회군", "수리·과학군", "예체능군"])
                custom_sub_name = st.text_input("✏️ 새 과목명 입력", placeholder="예) 정보과학").strip()
                final_subject = custom_sub_name
            elif selected_group != "교과군을 선택하세요.":
                specific_subs = ["과목을 선택하세요."] + SUBJECT_MAP[selected_group]
                if st.session_state.sel_sub_idx >= len(specific_subs):
                    st.session_state.sel_sub_idx = 0
                selected_sub_box = st.selectbox("📚 2단계: 세부 과목 선택", options=specific_subs, index=st.session_state.sel_sub_idx)
                if selected_sub_box != "과목을 선택하세요.": final_subject = selected_sub_box
            else:
                st.selectbox("📚 2단계: 세부 과목 선택", options=["교과군을 먼저 골라주세요."], disabled=True)

        with col_grade:
            sel_grade = st.selectbox("🎓 3단계: 관리 학년 선택", options=GRADE_OPTIONS_ADMIN, index=st.session_state.sel_grade_idx)
            final_grade = sel_grade.replace("학년", "") if sel_grade != "학년을 선택하세요." else ""

        with col_btn:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            activate_btn = st.button("🔄 영역 활성화 및 로드", use_container_width=True)
            
        if activate_btn:
            if not final_subject or not final_grade:
                st.error("⚠️ 과목과 학년을 모두 정확히 선택(입력)해 주세요.")
            else:
                if selected_group == "➕ [신규 과목 개설]":
                    save_new_subject_to_master(target_group_for_new, final_subject)
                st.session_state.active_subject = final_subject
                st.session_state.active_grade = final_grade
                st.session_state.sel_group_idx = group_options.index(selected_group)
                if selected_group != "➕ [신규 과목 개설]":
                    st.session_state.sel_sub_idx = specific_subs.index(final_subject)
                st.session_state.sel_grade_idx = GRADE_OPTIONS_ADMIN.index(sel_grade)
                st.toast(f"📂 [{final_subject} - {final_grade}학년] 공간이 활성화되었습니다.")
                st.rerun()

        if "active_subject" in st.session_state and "active_grade" in st.session_state:
            act_sub = st.session_state.active_subject
            act_grd = st.session_state.active_grade
            
            c_file, s_file = get_file_names(act_sub, act_grd)
            current_config = load_config(c_file)
            
            st.markdown(f"---")
            st.markdown(f"### 📍 현재 작업 중: <span style='color:#1E88E5;'>[{act_sub}] {act_grd}학년</span> 공간", unsafe_allow_html=True)
            
            st.markdown("#### 📌 [파트 1] 세부 학기 및 평가 항목 세팅")
            col_term, _ = st.columns([1.5, 1.5])
            with col_term:
                current_year = datetime.now().year
                year_term_options = ["학년도/학기를 선택하세요."]
                for y in range(current_year - 1, 2029):
                    year_term_options.append(f"{y}학년도 1학기")
                    year_term_options.append(f"{y}학년도 2학기")
                year_term_options.append("➕ [학기 직접 입력]")
                    
                saved_semester = current_config['학기통합명'] if current_config and '학기통합명' in current_config else "학년도/학기를 선택하세요."
                if saved_semester != "학년도/학기를 선택하세요." and saved_semester not in year_term_options:
                    term_default_index = year_term_options.index("➕ [학기 직접 입력]")
                    show_custom_term = True
                else:
                    term_default_index = year_term_options.index(saved_semester) if saved_semester in year_term_options else 0
                    show_custom_term = False
                    
                selected_semester_select = st.selectbox("대상 학기 선택", options=year_term_options, index=term_default_index, key="admin_term_select")
                if selected_semester_select == "➕ [학기 직접 입력]" or show_custom_term:
                    term_custom_val = saved_semester if (saved_semester not in year_term_options and saved_semester != "학년도/학기를 선택하세요.") else ""
                    selected_semester = st.text_input("✏️ 학년도/학기 직접 입력", value=term_custom_val, placeholder="예) 2029학년도 1학기", key="admin_term_custom")
                else: selected_semester = selected_semester_select

            st.markdown("**🏫 담당 학급(반) 설정**")
            saved_classes = []
            if current_config and '선택된반 목록' in current_config:
                saved_classes = [int(b.strip()) for b in str(current_config['선택된반 목록']).split(",") if b.strip()]
                
            selected_classes = []
            class_cols = st.columns(6) 
            for b in range(1, 13):
                col_idx = (b - 1) % 6
                with class_cols[col_idx]:
                    is_checked = b in saved_classes
                    if st.checkbox(f"{b}반", value=is_checked, key=f"class_check_{b}"): selected_classes.append(b)

            st.markdown("**✍️ 평가 종류 항목 입력**")
            default_count = int(current_config['항목개수']) if current_config and '항목개수' in current_config else 0
            item_count = st.number_input("평가 항목 총 개수 (0~10개)", min_value=0, max_value=10, value=default_count, key="admin_item_count")
            
            item_names = []
            if item_count > 0:
                cols = st.columns(3)
                for i in range(1, int(item_count) + 1):
                    col_idx = (i - 1) % 3
                    with cols[col_idx]:
                        default_item_name = current_config[f'항목{i}_이름'] if current_config and f'항목{i}_이름' in current_config else ""
                        name = st.text_input(f"{i}번 항목 이름", value=default_item_name, placeholder="예) 지필평가, 수행1 등", key=f"item_input_{i}")
                        item_names.append(name)

            st.markdown("#### 📂 [파트 2] 학생 입력 및 제어판")
            is_ready = True
            error_msg = ""
            if selected_semester == "학년도/학기를 선택하세요." or not selected_semester.strip():
                is_ready = False; error_msg = "대상 학기를 선택하거나 올바르게 입력해 주세요."
            elif not selected_classes:
                is_ready = False; error_msg = "담당 학급(반)을 최소 1개 이상 체크해 주세요."
            elif item_count == 0:
                is_ready = False; error_msg = "평가 항목 총 개수를 1개 이상으로 설정해 주세요."
            elif any(not n.strip() for n in item_names):
                is_ready = False; error_msg = "생성된 평가 항목의 이름을 모두 입력해 주세요."

            if is_ready:
                classes_str_join = ",".join(map(str, sorted(selected_classes)))
                config_data = {
                    "교과명": act_sub, "학년": int(act_grd), "학기통합명": selected_semester,
                    "선택된반 목록": classes_str_join, "항목개수": item_count
                }
                for i, name in enumerate(item_names): config_data[f"항목{i+1}_이름"] = name

                sample_cols = ["학년", "반", "번호", "이름", "비밀번호"] + item_names + ["확인여부", "확인시간"]
                sample_rows = []
                for b_num in sorted(selected_classes):
                    sample_rows.append([int(act_grd), b_num, 1, f"홍길동({b_num}반예시)", "090101"] + [0]*len(item_names) + ["미확인", "-"])
                
                sample_df = pd.DataFrame(sample_rows, columns=sample_cols)
                csv_buffer = io.BytesIO()
                sample_df.to_csv(csv_buffer, index=False, encoding='cp949')
                csv_bytes = csv_buffer.getvalue()

            ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.5, 1.5, 1])
            with ctrl_col1:
                if is_ready:
                    if st.button(f"💾 [{act_sub}] 설정 저장 및 다운로드", use_container_width=True):
                        pd.DataFrame([config_data]).to_csv(c_file, index=False)
                        st.success(f"🎉 저장이 완료되었습니다!")
                        st.download_button(
                            label="📥 맞춤형 엑셀 양식 파일 받기", data=csv_bytes,
                            file_name=f"[{act_sub}]_{selected_semester}_{act_grd}학년_양식.csv", mime="text/csv", use_container_width=True
                        )
                        st.stop()
                else: st.button(f"⚠️ 설정 미완료 ({error_msg})", disabled=True, use_container_width=True)
                    
            with ctrl_col2:
                if is_ready:
                    if st.button(f"➕ 저장 후 다른 과목/학년 추가 등록하기", use_container_width=True):
                        pd.DataFrame([config_data]).to_csv(c_file, index=False)
                        if "active_subject" in st.session_state: del st.session_state.active_subject
                        if "active_grade" in st.session_state: del st.session_state.active_grade
                        st.session_state.sel_group_idx = 0
                        st.session_state.sel_sub_idx = 0
                        st.session_state.sel_grade_idx = 0
                        st.rerun()
                else: st.button("➕ 다른 과목 추가하기 (현재 설정 미완료)", disabled=True, use_container_width=True)

            with ctrl_col3:
                if st.button(f"🗑️ 전체 시스템 포맷", use_container_width=True): reset_all_data()

            uploaded_file = st.file_uploader("📁 해당 과목 학생 성적 파일 업로드 (통합 CSV)", type=["csv"], key="admin_csv_uploader")
            if uploaded_file is not None:
                try:
                    try: student_df = pd.read_csv(uploaded_file, encoding='cp949')
                    except: student_df = pd.read_csv(uploaded_file, encoding='utf-8')
                    student_df.to_csv(s_file, index=False)
                    st.success(f"📂 [{act_sub} - {act_grd}학년] 성적 데이터 연동 완료!")
                except Exception as e: st.error(f"파일 오류: {e}")

            if os.path.exists(c_file):
                if st.checkbox("📊 현재 과목 학생 데이터 현황 보기"):
                    df_st = load_students(s_file)
                    if not df_st.empty: st.dataframe(df_st, use_container_width=True)
                    else: st.info("학생 성적 명렬 파일이 아직 업로드되지 않았습니다.")
        else: st.info("💡 상단에서 교과군과 과목을 지정하여 [영역 활성화]를 누르시면 기저장된 서식이 복원 및 표출됩니다.")

# ==========================================
# B. 학생 점수 확인 화면 (기본 접속 화면)
# ==========================================
else:
    st.markdown('<html lang="ko"></html>', unsafe_allow_html=True)
    col_title_left, col_title_right = st.columns([6, 1])
    with col_title_left: st.title("🎒 수행평가 성적 확인 시스템")
    with col_title_right:
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        if st.button("⚙️ 관리자 공간", use_container_width=True, type="secondary"):
            st.query_params.update(mode="admin")
            st.rerun()
            
    st.header("📝 개인별 수행평가 성적 조회")
    
    if "student_view_finished" in st.session_state and st.session_state.student_view_finished:
        st.balloons()
        st.success("🔒 성적 조회가 안전하게 완료되었습니다! 수고하셨습니다.")
        if st.button("🔄 처음 화면으로 돌아가기 (새로고침)", use_container_width=True):
            st.session_state.student_view_finished = False
            st.rerun()
        st.stop()

    st.markdown("#### 🔍 성적을 조회할 과목을 선택하세요")
    active_dbs = get_active_databases()
    
    if not active_dbs:
        st.warning("⚠️ 현재 시스템에 등록된 교과 수행평가 성적 데이터가 전혀 없습니다. 선생님의 기본 설정을 기다려 주세요.")
    else:
        student_combos = ["조회할 과목(학년)을 선택하세요."]
        for db in active_dbs: student_combos.append(f"📚 {db['subject']} ({db['grade']})")
            
        selected_combo = st.selectbox("📌 나의 교과 및 학년 선택", options=student_combos)
        
        if selected_combo != "조회할 과목(학년)을 선택하세요.":
            matched_db = active_dbs[student_combos.index(selected_combo) - 1]
            final_st_sub = matched_db['subject']
            final_st_grd = matched_db['grade'].replace("학년", "")
            
            c_file, s_file = get_file_names(final_st_sub, final_st_grd)
            config = load_config(c_file)
            
            st.markdown("---")
            st.info(f"🧬 **{config.get('교과명', '미정')}** | **{config.get('학기통합명', '')}** ({config.get('학년', 0)}학년 조회 서비스 정상 가동 중)")
            
            if "show_score" not in st.session_state: st.session_state.show_score = False

            with st.form("student_login_form"):
                available_classes = [f"{b.strip()}반" for b in str(config.get('선택된반 목록', '')).split(",") if b.strip()]
                col_b_sel, col_n_sel = st.columns(2)
                with col_b_sel: student_class_str = st.selectbox("자신의 반을 선택하세요", options=available_classes)
                with col_n_sel: num = st.number_input("번호를 입력하세요", min_value=1, step=1)
                    
                name = st.text_input("이름을 입력하세요")
                pw = st.text_input("비밀번호 (지정된 비밀번호 입력)", type="password")
                submit = st.form_submit_button("내 점수 확인하기")
                
            if submit:
                df_students = load_students(s_file)
                if df_students.empty: st.error("해당 학급의 상세 성적 명렬표 파일이 업로드되지 않았습니다.")
                else:
                    try:
                        class_int = int(student_class_str.replace("반", ""))
                        student = df_students[
                            (df_students['학년'] == int(config['학년'])) & (df_students['반'] == class_int) & 
                            (df_students['번호'] == num) & (df_students['이름'] == name) & (df_students['비밀번호'].astype(str) == str(pw))
                        ]
                        if not student.empty:
                            idx = student.index[0]
                            items_count = int(config['항목개수'])
                            score_details = {}
                            for i in range(1, items_count + 1):
                                col_name = config[f'항목{i}_이름']
                                score_details[col_name] = [df_students.loc[idx, col_name]]
                            
                            st.session_state.show_score = True
                            st.session_state.current_student_name = name
                            st.session_state.current_score_df = pd.DataFrame(score_details)
                            
                            if df_students.loc[idx, '확인여부'] != "확인 완료":
                                df_students.loc[idx, '확인여부'] = "확인 완료"
                                df_students.loc[idx, '확인시간'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                df_students.to_csv(s_file, index=False)
                                st.session_state.check_time_str = f"⏱️ 성적 확인 일시 기록됨: {df_students.loc[idx, '확인시간']}"
                            else:
                                st.session_state.check_time_str = f"⏱️ 최초 기록 일시: {df_students.loc[idx, '확인시간']}"
                        else:
                            st.session_state.show_score = False
                            st.error("❌ 입력하신 정보가 일치하지 않습니다.")
                    except: st.error("⚠️ 시스템 오류가 발생했습니다.")

            if st.session_state.show_score:
                st.markdown("---")
                st.success(f"🎉 {st.session_state.current_student_name} 학생의 성적 조회가 완료되었습니다.")
                st.table(st.session_state.current_score_df)
                st.caption(st.session_state.check_time_str)
                st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
                if st.button("✅ 확인 완료 및 화면 닫기", use_container_width=True, type="primary"):
                    st.session_state.show_score = False
                    st.session_state.student_view_finished = True
                    st.rerun()