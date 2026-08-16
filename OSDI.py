import streamlit as st
import pandas as pd
import requests
import base64

from datetime import datetime
from io import StringIO


# =========================================================
# GitHub 設定
# =========================================================

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

FILE_PATH = "osdi_data.csv"
BRANCH = "main"

GITHUB_URL = (
    f"https://api.github.com/repos/"
    f"{GITHUB_REPO}/contents/{FILE_PATH}"
)

GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


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
    "所在的地點或區域的濕度較低（非常乾燥）",
    "所在的區域使用空調"
]

all_questions = cat_a + cat_b + cat_c


# =========================================================
# 選項
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
# 建立 CSV 欄位
# =========================================================

def create_columns():

    return (
        [
            "姓名",
            "手機號碼"
        ]
        + all_questions
        + [
            "OSDI總分",
            "程度評估",
            "填寫時間"
        ]
    )


# =========================================================
# 回答 → 分數
#
# 如果 radio 沒選，
# 直接視為「未作答」
# =========================================================

def answer_to_score(answer):

    if answer is None:
        return -1

    return options_map.get(
        answer,
        -1
    )


# =========================================================
# 讀取 GitHub CSV
# =========================================================

def get_github_data():

    try:

        response = requests.get(
            GITHUB_URL,
            headers=GITHUB_HEADERS,
            params={
                "ref": BRANCH
            },
            timeout=20
        )

        print(
            "OSDI GET status:",
            response.status_code
        )


        # =================================================
        # 已存在
        # =================================================

        if response.status_code == 200:

            data = response.json()

            encoded_content = data.get(
                "content",
                ""
            )

            csv_bytes = base64.b64decode(
                encoded_content
            )

            csv_content = csv_bytes.decode(
                "utf-8-sig"
            )


            if csv_content.strip():

                try:

                    df = pd.read_csv(
                        StringIO(csv_content)
                    )

                except pd.errors.EmptyDataError:

                    df = pd.DataFrame(
                        columns=create_columns()
                    )

            else:

                df = pd.DataFrame(
                    columns=create_columns()
                )


            # 補齊欄位
            expected_columns = create_columns()

            for col in expected_columns:

                if col not in df.columns:
                    df[col] = ""

            df = df[
                expected_columns
            ]


            return (
                df,
                data.get("sha"),
                None
            )


        # =================================================
        # 第一次使用
        # =================================================

        elif response.status_code == 404:

            return (
                pd.DataFrame(
                    columns=create_columns()
                ),
                None,
                None
            )


        # =================================================
        # 其他錯誤
        # =================================================

        else:

            try:
                detail = response.json()

            except Exception:
                detail = response.text


            return (
                pd.DataFrame(
                    columns=create_columns()
                ),
                None,
                {
                    "status": response.status_code,
                    "detail": detail
                }
            )


    except requests.exceptions.Timeout:

        return (
            pd.DataFrame(
                columns=create_columns()
            ),
            None,
            {
                "status": "timeout",
                "detail": "連線 GitHub 逾時"
            }
        )


    except Exception as e:

        return (
            pd.DataFrame(
                columns=create_columns()
            ),
            None,
            {
                "status": "error",
                "detail": str(e)
            }
        )


# =========================================================
# 寫入 GitHub
# =========================================================

def save_to_github(current_data):

    # -----------------------------------------------------
    # 每次送出重新讀最新版
    # -----------------------------------------------------

    latest_df, latest_sha, read_error = (
        get_github_data()
    )


    if read_error is not None:

        return (
            False,
            {
                "stage": "read",
                **read_error
            }
        )


    expected_columns = create_columns()


    # -----------------------------------------------------
    # 新的一筆
    # -----------------------------------------------------

    new_row = pd.DataFrame(
        [current_data]
    )

    updated_df = pd.concat(
        [
            latest_df,
            new_row
        ],
        ignore_index=True
    )


    # 欄位固定
    updated_df = updated_df.reindex(
        columns=expected_columns
    )


    # -----------------------------------------------------
    # CSV
    # -----------------------------------------------------

    csv_string = updated_df.to_csv(
        index=False
    )

    encoded_csv = base64.b64encode(
        csv_string.encode(
            "utf-8-sig"
        )
    ).decode(
        "utf-8"
    )


    # -----------------------------------------------------
    # Payload
    # -----------------------------------------------------

    payload = {
        "message": (
            f"OSDI questionnaire update - "
            f"{current_data['姓名']}"
        ),
        "content": encoded_csv,
        "branch": BRANCH
    }


    if latest_sha is not None:
        payload["sha"] = latest_sha


    # -----------------------------------------------------
    # PUT
    # -----------------------------------------------------

    try:

        response = requests.put(
            GITHUB_URL,
            headers=GITHUB_HEADERS,
            json=payload,
            timeout=20
        )

        print(
            "OSDI PUT status:",
            response.status_code
        )

        print(
            "OSDI PUT response:",
            response.text[:1000]
        )


        # =================================================
        # 成功
        # =================================================

        if response.status_code in [
            200,
            201
        ]:

            return (
                True,
                response.json()
            )


        # =================================================
        # SHA 衝突
        # 再試一次
        # =================================================

        if response.status_code == 409:

            return retry_save_to_github(
                current_data
            )


        # =================================================
        # 其他錯誤
        # =================================================

        try:
            detail = response.json()

        except Exception:
            detail = response.text


        return (
            False,
            {
                "stage": "write",
                "status": response.status_code,
                "detail": detail
            }
        )


    except requests.exceptions.Timeout:

        return (
            False,
            {
                "stage": "write",
                "status": "timeout",
                "detail": "GitHub 寫入逾時"
            }
        )


    except Exception as e:

        return (
            False,
            {
                "stage": "write",
                "status": "error",
                "detail": str(e)
            }
        )


# =========================================================
# 409 Retry
# =========================================================

def retry_save_to_github(current_data):

    latest_df, latest_sha, read_error = (
        get_github_data()
    )


    if read_error is not None:

        return (
            False,
            {
                "stage": "retry_read",
                **read_error
            }
        )


    updated_df = pd.concat(
        [
            latest_df,
            pd.DataFrame(
                [current_data]
            )
        ],
        ignore_index=True
    )


    updated_df = updated_df.reindex(
        columns=create_columns()
    )


    csv_string = updated_df.to_csv(
        index=False
    )


    payload = {
        "message": (
            f"OSDI questionnaire update - "
            f"{current_data['姓名']}"
        ),

        "content": base64.b64encode(
            csv_string.encode(
                "utf-8-sig"
            )
        ).decode(
            "utf-8"
        ),

        "branch": BRANCH
    }


    if latest_sha is not None:
        payload["sha"] = latest_sha


    try:

        response = requests.put(
            GITHUB_URL,
            headers=GITHUB_HEADERS,
            json=payload,
            timeout=20
        )


        print(
            "OSDI RETRY status:",
            response.status_code
        )


        if response.status_code in [
            200,
            201
        ]:

            return (
                True,
                response.json()
            )


        try:
            detail = response.json()

        except Exception:
            detail = response.text


        return (
            False,
            {
                "stage": "retry_write",
                "status": response.status_code,
                "detail": detail
            }
        )


    except Exception as e:

        return (
            False,
            {
                "stage": "retry_write",
                "status": "error",
                "detail": str(e)
            }
        )


# =========================================================
# 驗證資料真的存在 GitHub CSV
# =========================================================

def verify_saved_data(
    name,
    phone,
    filled_time
):

    try:

        df, _, error = get_github_data()


        if error is not None:
            return False


        if df.empty:
            return False


        matched = df[
            (
                df["姓名"].astype(str)
                == str(name)
            )
            &
            (
                df["手機號碼"].astype(str)
                == str(phone)
            )
            &
            (
                df["填寫時間"].astype(str)
                == str(filled_time)
            )
        ]


        return not matched.empty


    except Exception:

        return False


# =========================================================
# OSDI 分數計算
# =========================================================

def calculate_osdi(
    responses
):

    sum_scores = 0
    answered_count = 0


    for q in all_questions:

        score = answer_to_score(
            responses.get(q)
        )


        if score != -1:

            sum_scores += score
            answered_count += 1


    if answered_count > 0:

        osdi_score = round(
            (
                sum_scores
                * 25
            )
            /
            answered_count,
            2
        )

    else:

        osdi_score = 0


    return (
        osdi_score,
        answered_count
    )


# =========================================================
# OSDI 程度
# =========================================================

def determine_osdi_status(
    osdi_score
):

    if osdi_score <= 12:
        return "正常"

    elif osdi_score <= 22:
        return "輕度乾眼"

    elif osdi_score <= 32:
        return "中度乾眼"

    else:
        return "重度乾眼"


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


/* =====================================================
   返回首頁
===================================================== */

.home-link {
    display: inline-flex;

    align-items: center;

    gap: 6px;

    padding: 9px 17px;

    margin-bottom: 20px;

    background: #EDE7E1;

    color: #6F6259 !important;

    text-decoration: none !important;

    border-radius: 10px;

    font-size: 14px;

    font-weight: 600;

    transition: 0.2s ease;
}

.home-link:hover {
    background: #DDD3CA;
}


/* =====================================================
   Title
===================================================== */

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


/* =====================================================
   Section
===================================================== */

.section-title {
    font-size: 22px;

    font-weight: 650;

    color: #6F6259;

    margin-top: 32px;

    margin-bottom: 6px;

    padding-bottom: 8px;

    border-bottom:
        2px solid #DDD4CC;
}


.section-caption {
    color: #8D8782;

    font-size: 14px;

    margin-bottom: 18px;

    line-height: 1.7;
}


/* =====================================================
   Submit
===================================================== */

div[data-testid="stFormSubmitButton"] button {
    background-color: #A99687;

    color: white;

    border-radius: 12px;

    min-height: 50px;

    border: none;

    font-size: 17px;

    font-weight: 600;

    margin-top: 20px;
}


div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #8F7D70;

    color: white;

    border: none;
}


/* =====================================================
   Result
===================================================== */

.osdi-result {
    margin-top: 25px;

    padding: 38px 32px;

    background-color: #F5F0EB;

    border-radius: 20px;

    text-align: center;

    color: #6F6259;
}


.result-label {
    font-size: 16px;

    color: #8A817A;

    letter-spacing: 1px;
}


.osdi-score {
    margin-top: 4px;

    margin-bottom: 25px;

    font-size: 46px;

    font-weight: 700;

    color: #806F62;
}


.result-status-label {
    margin-top: 10px;
}


.result-status {
    display: inline-block;

    margin-top: 10px;

    padding: 9px 24px;

    background-color: #B5A293;

    color: white;

    border-radius: 22px;

    font-size: 18px;

    font-weight: 600;
}


.result-note {
    margin-top: 24px;

    color: #9A918A;

    font-size: 13px;

    line-height: 1.7;
}


/* =====================================================
   Mobile
===================================================== */

@media (max-width: 768px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .osdi-title {
        font-size: 27px;
    }

    .section-title {
        font-size: 20px;
    }

}

</style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 返回首頁
#
# 注意：
# 使用 ./ 而不是 /
#
# OSDI URL：
# ...streamlit.app/OSDI
#
# ./ 會回：
# ...streamlit.app/
# =========================================================

st.html(
    """
<a
    class="home-link"
    href="./"
    target="_self"
>
    ← 返回首頁
</a>
    """
)


# =========================================================
# 標題
# =========================================================

st.html(
    """
<div class="osdi-title">
    OSDI 眼睛疾病量表
</div>

<div class="osdi-subtitle">
    請依照您過去一週的實際情況填寫
</div>
    """
)


# =========================================================
# 問卷
# =========================================================

with st.form(
    "osdi_survey_form"
):

    # =====================================================
    # 基本資料
    # =====================================================

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

    st.html(
        """
<div class="section-title">
    A. 眼睛症狀
</div>

<div class="section-caption">
    在過去一週中，您是否出現下列任一症狀？
</div>
        """
    )


    for q in cat_a:

        responses[q] = st.radio(
            q,

            options=list(
                options_map.keys()
            ),

            index=None,

            horizontal=True,

            key=f"osdi_{q}"
        )


    # =====================================================
    # B
    # =====================================================

    st.html(
        """
<div class="section-title">
    B. 日常活動
</div>

<div class="section-caption">
    在過去一週從事下列任一活動時，
    您是否曾因眼睛的問題而受到限制？
</div>
        """
    )


    for q in cat_b:

        responses[q] = st.radio(
            q,

            options=list(
                options_map.keys()
            ),

            index=None,

            horizontal=True,

            key=f"osdi_{q}"
        )


    # =====================================================
    # C
    # =====================================================

    st.html(
        """
<div class="section-title">
    C. 環境因素
</div>

<div class="section-caption">
    在過去一週中遇到下列任一狀況時，
    您的眼睛是否曾感覺不適？
</div>
        """
    )


    for q in cat_c:

        responses[q] = st.radio(
            q,

            options=list(
                options_map.keys()
            ),

            index=None,

            horizontal=True,

            key=f"osdi_{q}"
        )


    # =====================================================
    # Submit
    # =====================================================

    submitted = st.form_submit_button(
        "確認送出",
        use_container_width=True
    )


# =========================================================
# Submit
# =========================================================

if submitted:


    # =====================================================
    # 姓名
    # =====================================================

    if not name.strip():

        st.error(
            "請輸入姓名。"
        )


    # =====================================================
    # 手機
    # =====================================================

    elif not phone.strip():

        st.error(
            "請輸入手機號碼。"
        )


    else:

        # =================================================
        # 建立資料
        # =================================================

        current_data = {
            "姓名": name.strip(),
            "手機號碼": phone.strip()
        }


        # =================================================
        # 回答
        # =================================================

        for q in all_questions:

            current_data[q] = (
                answer_to_score(
                    responses.get(q)
                )
            )


        # =================================================
        # 計算
        # =================================================

        (
            osdi_score,
            answered_count
        ) = calculate_osdi(
            responses
        )


        # =================================================
        # 全部沒回答
        # =================================================

        if answered_count == 0:

            st.error(
                "請至少回答一題 OSDI 題目後再送出。"
            )


        else:

            # =============================================
            # 狀態
            # =============================================

            osdi_status = (
                determine_osdi_status(
                    osdi_score
                )
            )


            # =============================================
            # 時間
            # =============================================

            filled_time = (
                datetime.now()
                .strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )


            # =============================================
            # 完整資料
            # =============================================

            current_data[
                "OSDI總分"
            ] = osdi_score


            current_data[
                "程度評估"
            ] = osdi_status


            current_data[
                "填寫時間"
            ] = filled_time


            # =============================================
            # 寫入
            # =============================================

            with st.spinner(
                "正在儲存問卷資料..."
            ):

                success, result = (
                    save_to_github(
                        current_data
                    )
                )


            # =============================================
            # PUT 成功後再驗證一次
            # =============================================

            if success:

                saved_confirmed = (
                    verify_saved_data(
                        name.strip(),
                        phone.strip(),
                        filled_time
                    )
                )


                # =========================================
                # GitHub 真的有資料
                # =========================================

                if saved_confirmed:

                    st.success(
                        "眼睛疾病問卷送出成功！"
                    )


                    # =====================================
                    # 使用 st.html
                    #
                    # 不會再把 div 顯示成程式碼
                    # =====================================

                    result_html = f"""
<div class="osdi-result">

    <div class="result-label">
        OSDI 分數
    </div>

    <div class="osdi-score">
        {osdi_score}
    </div>

    <div class="result-label result-status-label">
        評估結果
    </div>

    <div class="result-status">
        {osdi_status}
    </div>

    <div class="result-note">
        此結果僅供問卷評估參考，
        實際狀況仍需由專業醫療人員判斷。
    </div>

</div>
"""

                    st.html(
                        result_html
                    )


                # =========================================
                # PUT 說成功但重新讀不到
                # =========================================

                else:

                    st.warning(
                        "GitHub API 已回報寫入成功，"
                        "但系統暫時無法再次確認資料。"
                        "請至 GitHub 的 osdi_data.csv 確認。"
                    )


            # =============================================
            # PUT 失敗
            # =============================================

            else:

                st.error(
                    "資料沒有成功寫入 GitHub。"
                )


                if isinstance(
                    result,
                    dict
                ):

                    stage = result.get(
                        "stage",
                        ""
                    )

                    status_code = result.get(
                        "status",
                        ""
                    )

                    detail = result.get(
                        "detail",
                        result.get(
                            "error",
                            ""
                        )
                    )


                    if stage:

                        st.write(
                            f"錯誤階段：{stage}"
                        )


                    if status_code:

                        st.write(
                            f"HTTP 狀態：{status_code}"
                        )


                    if detail:

                        if isinstance(
                            detail,
                            (
                                dict,
                                list
                            )
                        ):

                            st.json(
                                detail
                            )

                        else:

                            st.code(
                                str(detail)
                            )


                else:

                    st.code(
                        str(result)
                    )
