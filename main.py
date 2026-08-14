import streamlit as st
import base64
from pathlib import Path


# =========================================================
# Page Config
# =========================================================
st.set_page_config(
    page_title="AIDDES 問卷填寫",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# Image → Base64
# =========================================================
def get_base64_image(image_path):

    path = Path(image_path)

    if not path.exists():
        return ""

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# =========================================================
# 首頁
# =========================================================
def home():

    # =====================================================
    # 圖片路徑
    #
    # GitHub 專案請確認：
    #
    # image/
    # ├── ccmq.jpg
    # └── osdi.jpg
    #
    # =====================================================
    left_image_path = "image/CCMQ.png"
    right_image_path = "image/OSDI.png"

    left_bg = get_base64_image(left_image_path)
    right_bg = get_base64_image(right_image_path)


    # =====================================================
    # 背景
    # =====================================================

    if left_bg:

        left_background = (
            "linear-gradient("
            "rgba(70, 60, 52, 0.20), "
            "rgba(70, 60, 52, 0.20)"
            "), "
            f'url("data:image/jpeg;base64,{left_bg}")'
        )

    else:

        left_background = "#B9AFA5"


    if right_bg:

        right_background = (
            "linear-gradient("
            "rgba(70, 60, 52, 0.20), "
            "rgba(70, 60, 52, 0.20)"
            "), "
            f'url("data:image/jpeg;base64,{right_bg}")'
        )

    else:

        right_background = "#AAA096"


    # =====================================================
    # CSS
    # =====================================================
    st.markdown(
        f"""
        <style>

        /* ============================================
           Streamlit 預設樣式清除
        ============================================ */

        html,
        body {{
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
        }}


        [data-testid="stAppViewContainer"] {{
            margin: 0 !important;
            padding: 0 !important;
        }}


        [data-testid="stMain"] {{
            margin: 0 !important;
            padding: 0 !important;
        }}


        [data-testid="stMainBlockContainer"] {{
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }}


        .block-container {{
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }}


        header {{
            display: none !important;
        }}


        footer {{
            display: none !important;
        }}


        #MainMenu {{
            display: none !important;
        }}


        /* ============================================
           首頁外層
        ============================================ */

        .aid-home {{
            position: relative;

            width: 100vw;
            height: 100vh;

            display: flex;

            margin: 0;
            padding: 0;

            overflow: hidden;

            background-color: #EEEAE6;
        }}


        /* ============================================
           中央標題
        ============================================ */

        .aid-main-title {{

            position: absolute;

            top: 6%;
            left: 50%;

            transform: translateX(-50%);

            z-index: 100;

            background-color: rgba(177, 160, 147, 0.94);

            color: white;

            font-size: 30px;
            font-weight: 600;

            letter-spacing: 4px;

            padding: 15px 42px;

            border-radius: 18px;

            white-space: nowrap;

            box-shadow:
                0 5px 18px rgba(0, 0, 0, 0.13);
        }}


        /* ============================================
           左右選擇區
        ============================================ */

        .survey-choice {{

            position: relative;

            width: 50%;
            height: 100vh;

            display: flex;

            justify-content: center;
            align-items: center;

            margin: 0;
            padding: 0;

            overflow: hidden;

            text-decoration: none !important;

            cursor: pointer;

            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;

            transition:
                filter 0.35s ease,
                transform 0.35s ease;
        }}


        /* ============================================
           左邊
        ============================================ */

        .left-choice {{

            background: {left_background};

            border-right:
                1px solid rgba(255, 255, 255, 0.35);
        }}


        /* ============================================
           右邊
        ============================================ */

        .right-choice {{
            background: {right_background};
        }}


        /* ============================================
           Hover
        ============================================ */

        .survey-choice:hover {{
            filter: brightness(1.08);
        }}


        .survey-choice:hover .survey-content {{
            transform: translateY(-5px);
        }}


        /* ============================================
           中央文字區
        ============================================ */

        .survey-content {{

            position: relative;

            z-index: 10;

            text-align: center;

            color: white;

            transition: transform 0.35s ease;
        }}


        .survey-title {{

            font-size: 36px;

            font-weight: 600;

            letter-spacing: 4px;

            color: white;

            text-shadow:
                0px 3px 14px rgba(0, 0, 0, 0.50);
        }}


        .survey-subtitle {{

            margin-top: 14px;

            font-size: 16px;

            font-weight: 400;

            letter-spacing: 2px;

            color: rgba(255, 255, 255, 0.95);

            text-shadow:
                0px 2px 8px rgba(0, 0, 0, 0.40);
        }}


        /* ============================================
           中間淡色遮罩
           讓文字更好看
        ============================================ */

        .survey-choice::after {{

            content: "";

            position: absolute;

            top: 0;
            left: 0;

            width: 100%;
            height: 100%;

            background:
                linear-gradient(
                    to bottom,
                    rgba(0,0,0,0.03),
                    rgba(0,0,0,0.05)
                );

            pointer-events: none;
        }}


        /* ============================================
           手機版
        ============================================ */

        @media (max-width: 768px) {{

            html,
            body {{
                overflow-y: auto !important;
            }}


            .aid-home {{

                flex-direction: column;

                width: 100vw;
                height: 100vh;
            }}


            .survey-choice {{

                width: 100%;

                height: 50vh;
            }}


            .left-choice {{

                border-right: none;

                border-bottom:
                    1px solid rgba(255,255,255,0.35);
            }}


            .aid-main-title {{

                top: 3%;

                font-size: 21px;

                padding: 11px 24px;

                letter-spacing: 3px;

                border-radius: 14px;
            }}


            .survey-title {{
                font-size: 27px;
            }}


            .survey-subtitle {{
                font-size: 14px;
            }}

        }}

        </style>
        """,
        unsafe_allow_html=True
    )


    # =====================================================
    # HTML
    #
    # 整個左右區塊都是 <a>
    # 所以任何地方都可以點
    # =====================================================

    st.markdown(
        """
        <div class="aid-home">

            <!-- ================================
                 中央標題
            ================================= -->

            <div class="aid-main-title">
                AIDDES 問卷填寫
            </div>


            <!-- ================================
                 左邊：中醫體質量表
            ================================= -->

            <a
                href="/CCMQ"
                target="_self"
                class="survey-choice left-choice"
            >

                <div class="survey-content">

                    <div class="survey-title">
                        中醫體質量表
                    </div>

                    <div class="survey-subtitle">
                        點擊進入填寫
                    </div>

                </div>

            </a>


            <!-- ================================
                 右邊：眼睛疾病量表
            ================================= -->

            <a
                href="/OSDI"
                target="_self"
                class="survey-choice right-choice"
            >

                <div class="survey-content">

                    <div class="survey-title">
                        眼睛疾病量表
                    </div>

                    <div class="survey-subtitle">
                        點擊進入填寫
                    </div>

                </div>

            </a>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 建立 Page
# =========================================================

home_page = st.Page(
    home,
    title="AIDDES 問卷",
    icon="🏠",
    default=True,
    url_path=""
)


ccmq_page = st.Page(
    "CCMQ.py",
    title="中醫體質量表",
    url_path="CCMQ"
)


osdi_page = st.Page(
    "OSDI.py",
    title="眼睛疾病量表",
    url_path="OSDI"
)


# =========================================================
# Navigation
# =========================================================

navigation = st.navigation(
    [
        home_page,
        ccmq_page,
        osdi_page
    ],
    position="hidden"
)


navigation.run()
