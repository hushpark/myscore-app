# =========================================================================
# 🔄 [방탄 CSS] 드롭다운 & 텍스트 박스 완벽 테두리 동기화 및 시인성 개선
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

        /* 메인 화면 버튼 디자인 */
        div.stButton > button[kind="primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2) !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #2563eb !important; }
        div.stButton > button[kind="secondary"] { background-color: #ffffff !important; color: #0f172a !important; font-weight: 700 !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
        div.stButton > button[kind="secondary"]:hover { background-color: #f8fafc !important; border-color: #3b82f6 !important; color: #2563eb !important; }

        /* 팝업 다이얼로그 전용 버튼 */
        [data-testid="stDialog"] button[kind="primary"] { background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 800 !important; border: none !important; border-radius: 6px !important; padding: 12px 0 !important; font-size: 15px !important; width: 100% !important; }
        [data-testid="stDialog"] button[kind="secondary"] { background-color: #64748b !important; color: #ffffff !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; padding: 12px 0 !important; font-size: 15px !important; width: 100% !important; }

        div[data-testid="InputInstructions"] { display: none !important; }

        /* 🚨 [시인성 강화] 라벨 제목 굵게 */
        div[data-testid="stSelectbox"] label p, div[data-testid="stTextInput"] label p { font-weight: 800 !important; color: #1e293b !important; font-size: 15px !important; }

        /* 🚨 [드롭다운 & 텍스트 박스 테두리/배경 강제 동기화] */
        div[data-testid="stTextInput"] > div,
        div[data-testid="stTextInput"] [data-baseweb="input"],
        div[data-testid="stSelectbox"] > div[data-baseweb="select"],
        div[data-testid="stSelectbox"] > div { 
            background-color: #ffffff !important; 
            border: 1px solid #94a3b8 !important; /* 드롭다운과 동등한 수준의 선명한 외곽선 부여 */
            border-radius: 6px !important; 
            transition: all 0.2s ease-in-out !important; 
            box-shadow: none !important;
        }

        /* 텍스트 입력창 내부 패딩 및 배경 투명화 안정화 */
        div[data-testid="stTextInput"] input { 
            background-color: #ffffff !important; 
            color: #0f172a !important;
            padding: 8px 12px !important;
            border-radius: 6px !important;
        }
        
        /* 🎯 포커스(클릭) 시 드롭다운과 동일한 파란색 애니메이션 효과 적용 */
        div[data-testid="stTextInput"] > div:focus-within,
        div[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
        div[data-testid="stSelectbox"] > div:focus-within {
            border: 2px solid #3b82f6 !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
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