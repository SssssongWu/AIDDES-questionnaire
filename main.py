import streamlit as st
import base64
from pathlib import Path
from textwrap import dedent


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
# 圖片轉 Base64 Data URI
# 自動判斷 PNG / JPG / JPEG / WEBP
# =========================================================
def get_image_data_uri(image_path):

    path = Path(image_path)

    if not path.exists():
        print(f"❌ 找不到圖片：{path.resolve()}")
        return ""

    suffix = path.suffix.lower()

    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp"
    }

    mime_type = mime_map.get(suffix, "image/png")

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    print(f"✅ 圖片載入成功：{path.resolve()}")

    return f"data:{mime_type};base64,{encoded}"


# =========================================================
# 首頁
# =========================================================
def home():

    # -----------------------------------------------------
    # 圖片路徑
    #
    # GitHub：
    #
    # image/
    # ├── CCMQ.png
    # └── OSDI.png
    #
    # -----------------------------------------------------

    left_image_path = "image/CCMQ.png"
    right_image_path = "image/OSDI.png"

    left_image = get_image_data_uri(left_image_path)
    right_image = get_image_data_uri(right_image_path)


    # -----------------------------------------------------
    # 左邊背景
    # -----------------------------------------------------

    if left_image:

        left_background = (
            "linear-gradient("
            "rgba(74, 64, 57, 0.20), "
            "rgba(74, 64, 57, 0.20)"
            "), "
            f'url("{left_image}")'
        )

    else:

        left_background = "#C7B9AE"


    # -----------------------------------------------------
    # 右邊背景
    # -----------------------------------------------------

    if right_image:

        right_background = (
            "linear-gradient("
            "rgba(74, 64, 57, 0.18), "
            "rgba(74, 64, 57, 0.18)"
            "), "
            f'url("{right_image}")'
        )

    else:

        right_background = "#BEB1A6"


    # =====================================================
    # CSS
    # =====================================================

    css = f"""
<style>

/* ========================================================
   清除 Streamlit 預設版面
======================================================== */

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
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100% !important;
}}

.block-container {{
    margin: 0 !important;
    padding: 0 !important;
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


/* ========================================================
   首頁
======================================================== */

.aid-home {{
    position: relative;

    width: 100vw;
    height: 100vh;

    margin: 0;
    padding: 0;

    display: flex;

    overflow: hidden;
}}


/* ========================================================
   上方中央標題
======================================================== */

.aid-main-title {{
    position: absolute;

    top: 6%;
    left: 50%;

    transform: translateX(-50%);

    z-index: 999;

    background: rgba(190, 176, 164, 0.92);

    color: #FFFFFF;

    font-size: 30px;
    font-weight: 600;

    letter-spacing: 4px;

    padding: 15px 42px;

    border-radius: 18px;

    white-space: nowrap;

    box-shadow:
        0px 6px 20px rgba(60, 50, 45, 0.16);
}}


/* ========================================================
   左右整片按鈕
======================================================== */

.survey-choice {{
    position: relative;

    display: flex;

    width: 50%;
    height: 100vh;

    align-items: center;
    justify-content: center;

    margin: 0;
    padding: 0;

    overflow: hidden;

    cursor: pointer;

    text-decoration: none !important;

    background-size: cover !important;
    background-position: center !important;
    background-repeat: no-repeat !important;

    transition:
        filter 0.35s ease,
        transform 0.35s ease;
}}


/* 左邊 */

.left-choice {{
    background: {left_background};

    border-right:
        1px solid rgba(255, 255, 255, 0.40);
}}


/* 右邊 */

.right-choice {{
    background: {right_background};
}}


/* ========================================================
   Hover
======================================================== */

.survey-choice:hover {{
    filter: brightness(1.08);
}}

.survey-choice:hover .survey-content {{
    transform: translateY(-6px);
}}


/* ========================================================
   問卷文字
======================================================== */

.survey-content {{
    position: relative;

    z-index: 20;

    text-align: center;

    color: white;

    transition: transform 0.35s ease;
}}


.survey-title {{
    color: white;

    font-size: 36px;
    font-weight: 600;

    letter-spacing: 4px;

    text-shadow:
        0px 3px 14px rgba(0, 0, 0, 0.48);
}}


.survey-subtitle {{
    margin-top: 14px;

    color: rgba(255, 255, 255, 0.96);

    font-size: 16px;
    font-weight: 400;

    letter-spacing: 2px;

    text-shadow:
        0px 2px 8px rgba(0, 0, 0, 0.38);
}}


/* ========================================================
   圖片上淡淡遮罩
======================================================== */

.survey-choice::after {{
    content: "";

    position: absolute;

    inset: 0;

    background:
        linear-gradient(
            to bottom,
            rgba(50, 40, 35, 0.02),
            rgba(50, 40, 35, 0.08)
        );

    pointer-events: none;

    z-index: 5;
}}


/* ========================================================
   中間 hover 微微放大感
======================================================== */

.survey-choice::before {{
    content: "";

    position: absolute;

    inset: 0;

    background: rgba(255,255,255,0);

    z-index: 6;

    transition: background 0.35s ease;

    pointer-events: none;
}}

.survey-choice:hover::before {{
    background: rgba(255,255,255,0.035);
}}


/* ========================================================
   手機
======================================================== */

@media (max-width: 768px) {{

    html,
    body {{
        overflow: hidden !important;
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
            1px solid rgba(255,255,255,0.40);
    }}

    .aid-main-title {{
        top: 3%;

        font-size: 21px;

        padding: 11px 25px;

        letter-spacing: 3px;

        border-radius: 14px;
    }}

    .survey-title {{
        font-size: 27px;

        letter-spacing: 3px;
    }}

    .survey-subtitle {{
        font-size: 14px;
    }}

}}

</style>
"""

    st.markdown(
        dedent(css),
        unsafe_allow_html=True
    )


    # =====================================================
    # 首頁 HTML
    #
    # 注意：
    # 這裡故意不做 Python 縮排
    # 防止 Markdown 把 HTML 當 code block
    # =====================================================

    html = """
<div class="aid-home">

<div class="aid-main-title">
AIDDES 問卷填寫
</div>

<a
href="./CCMQ"
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

<a
href="./OSDI"
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
"""

    st.markdown(
        dedent(html),
        unsafe_allow_html=True
    )


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
