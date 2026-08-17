import streamlit as st
import pandas as pd
import requests
import base64

from datetime import datetime
from io import StringIO


# =========================================================
# 基本設定
# =========================================================

# GitHub Token 與 Repository 都從 Streamlit Secrets 取得
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

BRANCH = "main"
FILE_PATH = "osdi_data.csv"

# Streamlit App 首頁
HOME_URL = (
    "https://aiddes-questionnaire-hqqjp6u3pbssjeehd9aaz7"
    ".streamlit.app/"
)

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
# OSDI 題目
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
# CSV 欄位
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
# Answer → Score
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
            "OSDI GET:",
            response.status_code,
            GITHUB_URL
        )

        # -------------------------------------------------
        # 已存在
        # -------------------------------------------------

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
                        StringIO(csv_content),
                        dtype={
                            "姓名": str,
                            "手機號碼": str
                        }
                    )

                except pd.errors.EmptyDataError:

                    df = pd.DataFrame(
                        columns=create_columns()
                    )

            else:

                df = pd.DataFrame(
                    columns=create_columns()
                )


            expected_columns = create_columns()

            for col in expected_columns:

                if col not in df.columns:
                    df[col] = ""


            df = df.reindex(
                columns=expected_columns
            )


            return (
                df,
                data.get("sha"),
                None
            )


        # -------------------------------------------------
        # CSV 尚未存在
        # -------------------------------------------------

        elif response.status_code == 404:

            return (
                pd.DataFrame(
                    columns=create_columns()
                ),
                None,
                None
            )


        # -------------------------------------------------
        # API error
        # -------------------------------------------------

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
                "detail": "GitHub 連線逾時"
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
# 真正執行 GitHub PUT
# =========================================================

def put_github_csv(
    df,
    sha,
    name
):

    csv_string = df.to_csv(
        index=False
    )

    encoded_csv = base64.b64encode(
        csv_string.encode(
            "utf-8-sig"
        )
    ).decode(
        "utf-8"
    )


    payload = {
        "message":
            f"OSDI questionnaire update - {name}",

        "content":
            encoded_csv,

        "branch":
            BRANCH
    }


    # 更新既有檔案一定要 SHA
    # 第一次建立則不能放 SHA
    if sha is not None:

        payload["sha"] = sha


    try:

        response = requests.put(
            GITHUB_URL,
            headers=GITHUB_HEADERS,
            json=payload,
            timeout=30
        )


        print(
            "OSDI PUT status:",
            response.status_code
        )

        print(
            "OSDI PUT body:",
            response.text[:1500]
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
                "status":
                    response.status_code,

                "detail":
                    detail
            }
        )


    except Exception as e:

        return (
            False,
            {
                "status": "error",
                "detail": str(e)
            }
        )


# =========================================================
# 儲存一筆問卷
# =========================================================

def save_to_github(
    current_data
):

    # -----------------------------------------------------
    # 先讀最新版
    # -----------------------------------------------------

    latest_df, latest_sha, error = (
        get_github_data()
    )


    if error is not None:

        return (
            False,
            {
                "stage": "read",
                **error
            }
        )


    # -----------------------------------------------------
    # 新增資料
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


    updated_df = updated_df.reindex(
        columns=create_columns()
    )


    # -----------------------------------------------------
    # PUT
    # -----------------------------------------------------

    success, result = put_github_csv(
        updated_df,
        latest_sha,
        current_data["姓名"]
    )


    # -----------------------------------------------------
    # 成功
    # -----------------------------------------------------

    if success:

        return (
            True,
            result
        )


    # -----------------------------------------------------
    # 如果 SHA conflict
    # 重新取得一次再寫
    # -----------------------------------------------------

    if (
        isinstance(result, dict)
        and result.get("status") == 409
    ):

        retry_df, retry_sha, retry_error = (
            get_github_data()
        )


        if retry_error is not None:

            return (
                False,
                {
                    "stage": "retry_read",
                    **retry_error
                }
            )


        retry_df = pd.concat(
            [
                retry_df,
                pd.DataFrame(
                    [current_data]
                )
            ],
            ignore_index=True
        )


        retry_df = retry_df.reindex(
            columns=create_columns()
        )


        retry_success, retry_result = (
            put_github_csv(
                retry_df,
                retry_sha,
                current_data["姓名"]
            )
        )


        return (
            retry_success,
            retry_result
        )


    return (
        False,
        {
            "stage": "write",
            **result
        }
    )


# =========================================================
# 確認 GitHub 上真的存在這筆
# =========================================================

def verify_saved_data(
    name,
    phone,
    filled_time
):

    try:

        df, _, error = (
            get_github_data()
        )


        if error is not None:

            return False


        if df.empty:

            return False


        # 去除可能的空白
        df["姓名"] = (
            df["姓名"]
            .astype(str)
            .str.strip()
        )

        df["手機號碼"] = (
            df["手機號碼"]
            .astype(str)
            .str.strip()
        )

        df["填寫時間"] = (
            df["填寫時間"]
            .astype(str)
            .str.strip()
        )


        matched = df[
            (
                df["姓名"]
                == str(name).strip()
            )
            &
            (
                df["手機號碼"]
                == str(phone).strip()
            )
            &
            (
                df["填寫時間"]
                == str(filled_time).strip()
            )
        ]


        return not matched.empty


    except Exception as e:

        print(
            "VERIFY ERROR:",
            e
        )

        return False


# =========================================================
# OSDI 計算
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

div[data-testid="stLinkButton"] a {

    width: auto !important;

    background: #EDE7E1 !important;

    color: #6F6259 !important;

    border: none !important;

    border-radius: 10px !important;

    padding: 8px 17px !important;

    font-weight: 600 !important;

    text-decoration: none !important;
}


div[data-testid="stLinkButton"] a:hover {

    background: #DDD3CA !important;

    color: #6F6259 !important;
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
# 這次不用 href="./"
# 直接使用 Streamlit 的 Link Button + 完整網址
# =========================================================

st.link_button(
    "← 返回首頁",
    HOME_URL
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

    col1, col2 = st.columns(
        2
    )


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
        # Current Data
        # =================================================

        current_data = {

            "姓名":
                name.strip(),

            "手機號碼":
                phone.strip()
        }


        # =================================================
        # 每題
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
        # 全部沒答
        # =================================================

        if answered_count == 0:

            st.error(
                "請至少回答一題 OSDI 題目後再送出。"
            )


        else:

            # =============================================
            # OSDI 狀態
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
            # 儲存
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
            # PUT 成功
            # =============================================

            if success:

                # GitHub 回傳的實際檔案資訊
                github_content = (
                    result.get(
                        "content",
                        {}
                    )
                    if isinstance(
                        result,
                        dict
                    )
                    else {}
                )


                actual_path = (
                    github_content.get(
                        "path",
                        FILE_PATH
                    )
                )


                # =========================================
                # 再重新 GET 確認
                # =========================================

                saved_confirmed = (
                    verify_saved_data(
                        name.strip(),
                        phone.strip(),
                        filled_time
                    )
                )


                if saved_confirmed:

                    st.success(
                        "眼睛疾病問卷送出成功！"
                    )


                    st.caption(
                        f"資料已寫入："
                        f"{GITHUB_REPO}/"
                        f"{actual_path} "
                        f"（{BRANCH} branch）"
                    )


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
                # PUT 成功但 GET 驗證失敗
                # =========================================

                else:

                    st.error(
                        "GitHub 回傳寫入成功，"
                        "但重新讀取後找不到這筆資料。"
                    )

                    st.write(
                        "目前設定的 Repository：",
                        GITHUB_REPO
                    )

                    st.write(
                        "目前設定的 Branch：",
                        BRANCH
                    )

                    st.write(
                        "目前設定的檔案：",
                        FILE_PATH
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
                        ""
                    )


                    if stage:

                        st.write(
                            "錯誤階段：",
                            stage
                        )


                    if status_code:

                        st.write(
                            "HTTP 狀態：",
                            status_code
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
