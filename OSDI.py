import streamlit as st
import pandas as pd
import requests
import base64
import json
from datetime import datetime
from io import StringIO


# =========================================================
# GitHub 設定
# =========================================================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

FILE_PATH = "osdi_data.csv"

URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"


# =========================================================
# OSDI 問卷題目
# =========================================================
cat_a = [
    "眼睛對光敏感",
    "眼睛有異物感",
    "眼睛疼痛",
    "視線模糊",
    "視力減退"
]

cat_b = [
    "閱讀",
    "夜間駕駛",
    "操作電腦或提款機",
    "觀看電視"
]

cat_c = [
    "刮風的狀況",
    "所在的地點或區域的濕度較低(非常乾燥)",
    "所在的區域使用空調"
]

all_questions = cat_a + cat_b + cat_c


# =========================================================
# 選項分數
# =========================================================
options_map = {
    "總是": 4,
    "經常": 3,
    "一半一半": 2,
    "偶而": 1,
    "完全不曾": 0,
    "未作答": -1
}


# =========================================================
# 讀取 GitHub CSV
# =========================================================
def get_github_data():

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    try:
        response = requests.get(
            URL,
            headers=headers,
            timeout=20
        )

        if response.status_code == 200:

            content = response.json()

            csv_content = base64.b64decode(
                content["content"]
            ).decode("utf-8")

            df = pd.read_csv(
                StringIO(csv_content)
            )

            return df, content["sha"]

        elif response.status_code == 404:

            columns = (
                ["姓名", "手機號碼"]
                + all_questions
                + [
                    "OSDI總分",
                    "程度評估",
                    "填寫時間"
                ]
            )

            return pd.DataFrame(
                columns=columns
            ), None

        else:

            st.error(
                f"讀取資料失敗：HTTP {response.status_code}"
            )

            columns = (
                ["姓名", "手機號碼"]
                + all_questions
                + [
                    "OSDI總分",
                    "程度評估",
                    "填寫時間"
                ]
            )

            return pd.DataFrame(
                columns=columns
            ), None

    except Exception as e:

        st.error(f"讀取資料時發生錯誤：{e}")

        columns = (
            ["姓名", "手機號碼"]
            + all_questions
            + [
                "OSDI總分",
                "程度評估",
                "填寫時間"
            ]
        )

        return pd.DataFrame(
            columns=columns
        ), None


# =========================================================
# CSS
# =========================================================
st.markdown(
    """
    <style>

    .block-container {
        max-width: 950px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .osdi-title {
        text-align: center;
        font-size: 34px;
        font-weight: 700;
        color: #6F6259;
        margin-bottom: 8px;
    }

    .osdi-subtitle {
        text-align: center;
        color: #8A817A;
        font-size: 15px;
        margin-bottom: 28px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 650;
        color: #6F6259;
        margin-top: 28px;
        margin-bottom: 5px;
    }

    .section-caption {
        color: #8D8782;
        font-size: 14px;
        margin-bottom: 15px;
    }

    div[data-testid="stFormSubmitButton"] button {
        background-color: #75665B;
        color: white;
        border-radius: 12px;
        height: 48px;
        border: none;
        font-size: 17px;
        font-weight: 600;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #62564D;
        color: white;
        border: none;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 返回首頁
# =========================================================
if st.button("← 返回首頁"):
    st.switch_page("main.py")


# =========================================================
# 標題
# =========================================================
st.markdown(
    """
    <div class="osdi-title">
        OSDI 眼睛疾病量表
    </div>

    <div class="osdi-subtitle">
        請依照您過去一週的實際情況填寫
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 先讀取 CSV
# =========================================================
df, file_sha = get_github_data()


# =========================================================
# 問卷
# =========================================================
with st.form("osdi_survey_form"):

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input(
            "姓名",
            placeholder="請輸入姓名"
        )

    with col2:
        phone = st.text_input(
            "手機號碼",
            placeholder="請輸入手機號碼"
        )

    responses = {}


    # =====================================================
    # A
    # =====================================================
    st.markdown(
        '<div class="section-title">A. 眼睛症狀</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="section-caption">
        在過去一週中，您是否出現下列任一症狀？
        </div>
        """,
        unsafe_allow_html=True
    )

    for q in cat_a:

        responses[q] = st.radio(
            q,
            options=list(options_map.keys()),
            index=5,
            horizontal=True,
            key=f"osdi_{q}"
        )


    # =====================================================
    # B
    # =====================================================
    st.markdown(
        '<div class="section-title">B. 日常活動</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="section-caption">
        在過去一週從事下列任一活動，
        您是否曾因眼睛的問題而受到限制？
        </div>
        """,
        unsafe_allow_html=True
    )

    for q in cat_b:

        responses[q] = st.radio(
            q,
            options=list(options_map.keys()),
            index=5,
            horizontal=True,
            key=f"osdi_{q}"
        )


    # =====================================================
    # C
    # =====================================================
    st.markdown(
        '<div class="section-title">C. 環境因素</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="section-caption">
        在過去一週中遇到任一狀況時，
        您的眼睛是否曾感覺不適？
        </div>
        """,
        unsafe_allow_html=True
    )

    for q in cat_c:

        responses[q] = st.radio(
            q,
            options=list(options_map.keys()),
            index=5,
            horizontal=True,
            key=f"osdi_{q}"
        )


    submitted = st.form_submit_button(
        "確認送出",
        use_container_width=True
    )


# =========================================================
# 送出
# =========================================================
if submitted:

    # -----------------------------------------------------
    # 基本資料確認
    # -----------------------------------------------------
    if not name.strip():

        st.error("請輸入姓名")

    else:

        sum_scores = 0
        answered_count = 0

        current_data = {
            "姓名": name.strip(),
            "手機號碼": phone.strip()
        }


        # -------------------------------------------------
        # 計算 OSDI
        # -------------------------------------------------
        for q in all_questions:

            score = options_map[
                responses[q]
            ]

            current_data[q] = score

            if score != -1:

                sum_scores += score
                answered_count += 1


        if answered_count > 0:

            osdi_score = round(
                (sum_scores * 25)
                / answered_count,
                2
            )

        else:

            osdi_score = 0


        # -------------------------------------------------
        # 程度判斷
        # -------------------------------------------------
        if osdi_score <= 12:

            status = "正常"

        elif osdi_score <= 22:

            status = "輕度乾眼"

        elif osdi_score <= 32:

            status = "中度乾眼"

        else:

            status = "重度乾眼"


        current_data["OSDI總分"] = osdi_score
        current_data["程度評估"] = status

        current_data["填寫時間"] = (
            datetime.now()
            .strftime("%Y-%m-%d %H:%M:%S")
        )


        # =================================================
        # 新增資料
        # =================================================
        updated_df = pd.concat(
            [
                df,
                pd.DataFrame(
                    [current_data]
                )
            ],
            ignore_index=True
        )


        csv_string = updated_df.to_csv(
            index=False
        )


        # =================================================
        # GitHub API
        # =================================================
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }


        payload = {

            "message": (
                f"OSDI Update: {name}"
            ),

            "content": base64.b64encode(
                csv_string.encode("utf-8")
            ).decode("utf-8")
        }


        if file_sha:

            payload["sha"] = file_sha


        # =================================================
        # 上傳
        # =================================================
        try:

            res = requests.put(
                URL,
                headers=headers,
                json=payload,
                timeout=20
            )


            if res.status_code in [200, 201]:

                st.success(
                    "問卷送出成功！"
                )

                st.info(
                    f"""
                    OSDI 分數：**{osdi_score}**

                    評估結果：**{status}**
                    """
                )


            else:

                st.error(
                    f"儲存失敗：HTTP {res.status_code}"
                )

                try:

                    error_data = res.json()

                    st.code(
                        json.dumps(
                            error_data,
                            ensure_ascii=False,
                            indent=2
                        )
                    )

                except Exception:

                    st.code(res.text)


        except Exception as e:

            st.error(
                f"儲存資料時發生錯誤：{e}"
            )