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
# 圖片 → Base64
# =========================================================
def get_image_data_uri(image_path):

    path = Path(image_path)

    if not path.exists():
        print(f"❌ 找不到圖片：{path.resolve()}")
        return ""

    suffix = path.suffix.lower()

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp"
    }

    mime_type = mime_types.get(suffix, "image/png")

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    print(f"✅ 圖片成功載入：{path.resolve()}")

    return f"data:{mime_type};base64,{encoded}"


# =========================================================
# 首頁
# =========================================================
def home():

    # =====================================================
    # 圖片路徑
    # =====================================================

    left_image_path = "image/CCMQ.png"
    right_image_path = "image/OSDI.png"

    left_image = get_image_data_uri(left_image_path)
    right_image = get_image_data_uri(right_image_path)


    # =====================================================
    # 背景
    # =====================================================

    if left_image:
        left_background = (
            "linear-gradient("
            "rgba(75, 65, 58, 0.16), "
            "rgba(75, 65, 58, 0.16)"
            "), "
            f'url("{left_image}")'
        )
    else:
        left_background = "#C8BBB0"


    if right_image:
        right_background = (
            "linear-gradient("
            "rgba(75, 65, 58, 0.16), "
            "rgba(75, 65, 58, 0.16)"
            "), "
            f'url("{right_image}")'
        )
    else:
        right_background = "#C3B6AC"


    # =====================================================
    # HTML + CSS
    # 使用 st.html，不再使用 st.markdown
    # =====================================================

    page_html = f"""
<style>

html,
body {{
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}


/* Streamlit 主畫面 */

[data-testid="stAppViewContainer"] {{
    margin: 0 !important;
    padding: 0 !important;
}}

[data-testid="stMain"] {{
    margin: 0 !important;
    padding: 0 !important;
}}

[data-testid="stMainBlockContainer"] {{
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100% !important;
}}

.block-container {{
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100% !important;
}}


/* 隱藏 Streamlit UI */

header {{
    display: none !important;
}}

footer {{
    display: none !important;
}}

#MainMenu {{
    display: none !important;
}}


/* =====================================================
   整個首頁
===================================================== */

.aiddes-home {{
    position: relative;

    width: 100vw;
    height: 100vh;

    margin: 0;
    padding: 0;

    display: flex;

    overflow: hidden;

    background: #EEEAE6;
}}


/* =====================================================
   上方中央標題
===================================================== */

.aiddes-main-title {{
    position: absolute;

    top: 6%;
    left: 50%;

    transform: translateX(-50%);

    z-index: 100;

    background: rgba(196, 181, 169, 0.93);

    color: white;

    font-size: 30px;
    font-weight: 600;

    letter-spacing: 5px;

    padding: 15px 42px;

    border-radius: 18px;

    white-space: nowrap;

    box-shadow:
        0 6px 20px rgba(70, 60, 55, 0.16);
}}


/* =====================================================
   左右大區塊
===================================================== */

.survey-choice {{

    position: relative;

    width: 50%;
    height: 100vh;

    display: flex;

    align-items: center;
    justify-content: center;

    margin: 0;
    padding: 0;

    overflow: hidden;

    cursor: pointer;

    text-decoration: none !important;

    background-size: cover !important;
    background-position: center center !important;
    background-repeat: no-repeat !important;

    transition:
        filter 0.35s ease;
}}


/* =====================================================
   左圖
===================================================== */

.left-choice {{
    background-image: {left_background};

    border-right:
        1px solid rgba(255,255,255,0.40);
}}


/* =====================================================
   右圖
===================================================== */

.right-choice {{
    background-image: {right_background};
}}


/* =====================================================
   hover
===================================================== */

.survey-choice:hover {{
    filter: brightness(1.07);
}}


.survey-choice:hover .survey-content {{
    transform: translateY(-6px);
}}


/* =====================================================
   圖片淡遮罩
===================================================== */

.survey-choice::before {{

    content: "";

    position: absolute;

    inset: 0;

    background:
        linear-gradient(
            to bottom,
            rgba(60,50,45,0.01),
            rgba(60,50,45,0.08)
        );

    z-index: 1;

    pointer-events: none;
}}


/* =====================================================
   中央文字
===================================================== */

.survey-content {{

    position: relative;

    z-index: 5;

    text-align: center;

    transition:
        transform 0.35s ease;
}}


.survey-title {{

    color: white;

    font-size: 36px;
    font-weight: 600;

    letter-spacing: 4px;

    text-shadow:
        0 3px 14px rgba(0,0,0,0.48);
}}


.survey-subtitle {{

    margin-top: 15px;

    color: rgba(255,255,255,0.95);

    font-size: 16px;
    font-weight: 400;

    letter-spacing: 2px;

    text-shadow:
        0 2px 8px rgba(0,0,0,0.38);
}}


/* =====================================================
   手機
===================================================== */

@media (max-width: 768px) {{

    .aiddes-home {{
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
            1px solid rgba(255,255,255,0.40);
    }}


    .aiddes-main-title {{

        top: 3%;

        font-size: 21px;

        letter-spacing: 3px;

        padding: 11px 25px;

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


<div class="aiddes-home">


    <div class="aiddes-main-title">
        AIDDES 問卷填寫
    </div>


    <a
        class="survey-choice left-choice"
        href="./CCMQ"
        target="_self"
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


    <a
        class="survey-choice right-choice"
        href="./OSDI"
        target="_self"
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
"""

    st.html(page_html)


# =========================================================
# Pages
# =========================================================

home_page = st.Page(
    home,
    title="AIDDES 問卷",
    icon="🏠",
    default=True
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
