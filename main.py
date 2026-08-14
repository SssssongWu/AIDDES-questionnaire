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
# 之後把圖片放進專案，例如：
# images/ccmq.jpg
# images/osdi.jpg
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

    # -----------------------------------------------------
    # 之後只要修改這兩個圖片路徑
    # -----------------------------------------------------
    left_image_path = "image/CCMQ.jpg"
    right_image_path = "image/OSDI.jpg"

    left_bg = get_base64_image(left_image_path)
    right_bg = get_base64_image(right_image_path)

    # 如果圖片還沒放，先給純色背景
    if left_bg:
        left_background = f"""
        linear-gradient(
            rgba(75, 65, 58, 0.25),
            rgba(75, 65, 58, 0.25)
        ),
        url("data:image/jpeg;base64,{left_bg}")
        """
    else:
        left_background = "#b5aa9d"

    if right_bg:
        right_background = f"""
        linear-gradient(
            rgba(75, 65, 58, 0.25),
            rgba(75, 65, 58, 0.25)
        ),
        url("data:image/jpeg;base64,{right_bg}")
        """
    else:
        right_background = "#a89d91"

    # -----------------------------------------------------
    # CSS
    # -----------------------------------------------------
    st.markdown(
        f"""
        <style>

        /* 移除 Streamlit 預設空白 */
        .block-container {{
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            max-width: 100% !important;
        }}

        header {{
            visibility: hidden;
        }}

        footer {{
            visibility: hidden;
        }}

        #MainMenu {{
            visibility: hidden;
        }}

        /* 整個首頁 */
        .aid-home {{
            position: relative;
            width: 100%;
            height: 100vh;
            overflow: hidden;
        }}

        /* 中央標題 */
        .aid-title {{
            position: absolute;
            top: 7%;
            left: 50%;
            transform: translateX(-50%);

            background-color: #75665B;

            color: white;
            font-size: 30px;
            font-weight: 600;

            padding: 14px 38px;

            border-radius: 16px;

            z-index: 10;

            letter-spacing: 3px;

            box-shadow:
                0px 5px 18px rgba(0, 0, 0, 0.15);

            white-space: nowrap;
        }}

        /* 左右容器 */
        .choice-container {{
            display: flex;
            width: 100%;
            height: 100vh;
        }}

        /* 共用左右區塊 */
        .choice {{
            position: relative;

            width: 50%;
            height: 100%;

            display: flex;
            justify-content: center;
            align-items: center;

            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;

            overflow: hidden;

            transition:
                transform 0.35s ease,
                filter 0.35s ease;
        }}

        /* 左背景 */
        .choice-left {{
            background: {left_background};
            background-size: cover;
            background-position: center;
        }}

        /* 右背景 */
        .choice-right {{
            background: {right_background};
            background-size: cover;
            background-position: center;
        }}

        /* hover */
        .choice:hover {{
            filter: brightness(1.07);
        }}

        /* 問卷名稱 */
        .choice-text {{
            color: white;

            font-size: 34px;
            font-weight: 600;

            text-shadow:
                0px 2px 10px rgba(0,0,0,0.45);

            letter-spacing: 3px;

            text-align: center;

            z-index: 2;
        }}

        /* 小螢幕 */
        @media (max-width: 768px) {{

            .choice-container {{
                flex-direction: column;
            }}

            .choice {{
                width: 100%;
                height: 50vh;
            }}

            .aid-title {{
                top: 3%;
                font-size: 21px;
                padding: 10px 24px;
            }}

            .choice-text {{
                font-size: 25px;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True
    )

    # =====================================================
    # 標題
    # =====================================================
    st.markdown(
        """
        <div class="aid-title">
            AIDDES問卷填寫
        </div>
        """,
        unsafe_allow_html=True
    )

    # =====================================================
    # 因為 Streamlit button 才能執行 switch_page
    # 使用兩欄做實際點擊區
    # =====================================================

    col_left, col_right = st.columns(2, gap=None)

    with col_left:

        st.markdown(
            f"""
            <div style="
                height: 78vh;
                margin-top: 11vh;

                background: {left_background};
                background-size: cover;
                background-position: center;

                border-radius: 0px;

                display: flex;
                align-items: center;
                justify-content: center;

                text-align: center;
            ">

                <div style="
                    color: white;
                    font-size: 34px;
                    font-weight: 600;
                    letter-spacing: 3px;
                    text-shadow: 0px 2px 10px rgba(0,0,0,0.45);
                ">
                    中醫量質量表填寫
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "進入中醫量質量表",
            use_container_width=True,
            key="ccmq_button"
        ):
            st.switch_page(ccmq_page)

    with col_right:

        st.markdown(
            f"""
            <div style="
                height: 78vh;
                margin-top: 11vh;

                background: {right_background};
                background-size: cover;
                background-position: center;

                border-radius: 0px;

                display: flex;
                align-items: center;
                justify-content: center;

                text-align: center;
            ">

                <div style="
                    color: white;
                    font-size: 34px;
                    font-weight: 600;
                    letter-spacing: 3px;
                    text-shadow: 0px 2px 10px rgba(0,0,0,0.45);
                ">
                    眼睛疾病量表填寫
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "進入眼睛疾病量表",
            use_container_width=True,
            key="osdi_button"
        ):
            st.switch_page(osdi_page)


# =========================================================
# 建立三個 Page
# =========================================================

home_page = st.Page(
    home,
    title="AIDDES 問卷",
    icon="🏠",
    default=True
)

ccmq_page = st.Page(
    "CCMQ.py",
    title="中醫量質量表"
)

osdi_page = st.Page(
    "OSDI.py",
    title="眼睛疾病量表"
)


# =========================================================
# Navigation
# position="hidden" = 不顯示左側導航
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
