import streamlit as st
import pandas as pd
import requests
import base64

from datetime import datetime
from io import StringIO


# =========================================================
# GitHub 設定
#
# Streamlit Secrets：
#
# GITHUB_TOKEN = "你的 GitHub Token"
# GITHUB_REPO = "ssssongwu/aiddes-questionnaire"
#
# =========================================================

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

FILE_PATH = "osdi_data.csv"

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


all_questions = (
    cat_a
    + cat_b
    + cat_c
)


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
# 從 GitHub 讀取最新 CSV
#
# 回傳：
# df
# sha
# error
# =========================================================

def get_github_data():

    try:

        response = requests.get(
            GITHUB_URL,
            headers=GITHUB_HEADERS,
            timeout=20
        )

        print(
            "OSDI GET GitHub status:",
            response.status_code
        )


        # =================================================
        # CSV 已存在
        # =================================================

        if response.status_code == 200:

            data = response.json()

            encoded_content = data.get(
                "content",
                ""
            )


            # GitHub 回傳 Base64
            csv_bytes = base64.b64decode(
                encoded_content
            )


            # utf-8-sig 可以同時處理 BOM
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


            return (
                df,
                data.get("sha"),
                None
            )


        # =================================================
        # CSV 尚未存在
        #
        # 第一次填寫時會走這裡
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

                error_detail = (
                    response.json()
                )

            except Exception:

                error_detail = {
                    "message":
                        response.text
                }


            return (
                pd.DataFrame(
                    columns=create_columns()
                ),
                None,
                {
                    "status":
                        response.status_code,

                    "detail":
                        error_detail
                }
            )


    # =====================================================
    # Timeout
    # =====================================================

    except requests.exceptions.Timeout:

        return (
            pd.DataFrame(
                columns=create_columns()
            ),
            None,
            {
                "status": "timeout",
                "detail":
                    "GitHub 連線逾時"
            }
        )


    # =====================================================
    # Request error
    # =====================================================

    except requests.exceptions.RequestException as e:

        return (
            pd.DataFrame(
                columns=create_columns()
            ),
            None,
            {
                "status":
                    "request_error",

                "detail":
                    str(e)
            }
        )


    # =====================================================
    # 其他
    # =====================================================

    except Exception as e:

        return (
            pd.DataFrame(
                columns=create_columns()
            ),
            None,
            {
                "status":
                    "unknown",

                "detail":
                    str(e)
            }
        )


# =========================================================
# 寫入 GitHub
#
# 重要：
# 每次按送出時，
# 都重新抓最新 CSV 和最新 sha。
#
# 避免：
# 兩個人同時填問卷時，
# 使用舊 sha 導致寫入失敗。
# =========================================================

def save_to_github(
    current_data
):

    # =====================================================
    # 重新取得最新版 CSV
    # =====================================================

    latest_df, latest_sha, read_error = (
        get_github_data()
    )


    if read_error is not None:

        return (
            False,
            {
                "stage": "read",
                "error": read_error
            }
        )


    # =====================================================
    # 確保欄位一致
    # =====================================================

    expected_columns = (
        create_columns()
    )


    for col in expected_columns:

        if col not in latest_df.columns:

            latest_df[col] = ""


    latest_df = latest_df[
        expected_columns
    ]


    # =====================================================
    # 新增一筆資料
    # =====================================================

    new_row_df = pd.DataFrame(
        [current_data]
    )


    updated_df = pd.concat(
        [
            latest_df,
            new_row_df
        ],
        ignore_index=True
    )


    # =====================================================
    # 轉成 CSV
    # =====================================================

    csv_string = (
        updated_df.to_csv(
            index=False
        )
    )


    # =====================================================
    # Base64
    #
    # 使用 utf-8-sig
    # Excel 開中文比較不容易亂碼
    # =====================================================

    encoded_csv = base64.b64encode(
        csv_string.encode(
            "utf-8-sig"
        )
    ).decode(
        "utf-8"
    )


    # =====================================================
    # GitHub payload
    # =====================================================

    payload = {

        "message":
            (
                "OSDI questionnaire update - "
                f"{current_data['姓名']}"
            ),

        "content":
            encoded_csv
    }


    # CSV 已存在才加 sha
    if latest_sha is not None:

        payload["sha"] = (
            latest_sha
        )


    # =====================================================
    # PUT
    # =====================================================

    try:

        response = requests.put(
            GITHUB_URL,
            headers=GITHUB_HEADERS,
            json=payload,
            timeout=20
        )


        print(
            "OSDI PUT GitHub status:",
            response.status_code
        )

        print(
            "OSDI PUT GitHub response:",
            response.text[:1000]
        )


        # -------------------------------------------------
        # 成功
        #
        # 201 = 第一次建立
        # 200 = 更新
        # -------------------------------------------------

        if response.status_code in [
            200,
            201
        ]:

            return (
                True,
                response.json()
            )


        # =================================================
        # 409
        #
        # 可能剛好另一個人也寫入 CSV
        # 重新抓最新版再試一次
        # =================================================

        if response.status_code == 409:

            retry_df, retry_sha, retry_error = (
                get_github_data()
            )


            if retry_error is not None:

                return (
                    False,
                    {
                        "stage":
                            "retry_read",

                        "error":
                            retry_error
                    }
                )


            # ---------------------------------------------
            # 補齊欄位
            # ---------------------------------------------

            for col in expected_columns:

                if col not in retry_df.columns:

                    retry_df[col] = ""


            retry_df = retry_df[
                expected_columns
            ]


            # ---------------------------------------------
            # 再加入這筆資料
            # ---------------------------------------------

            retry_updated_df = (
                pd.concat(
                    [
                        retry_df,
                        pd.DataFrame(
                            [current_data]
                        )
                    ],
                    ignore_index=True
                )
            )


            retry_csv = (
                retry_updated_df.to_csv(
                    index=False
                )
            )


            # ---------------------------------------------
            # Retry payload
            # ---------------------------------------------

            retry_payload = {

                "message":
                    (
                        "OSDI questionnaire update - "
                        f"{current_data['姓名']}"
                    ),

                "content":
                    base64.b64encode(
                        retry_csv.encode(
                            "utf-8-sig"
                        )
                    ).decode(
                        "utf-8"
                    )
            }


            if retry_sha is not None:

                retry_payload["sha"] = (
                    retry_sha
                )


            # ---------------------------------------------
            # Retry PUT
            # ---------------------------------------------

            retry_response = (
                requests.put(
                    GITHUB_URL,
                    headers=
                        GITHUB_HEADERS,
                    json=
                        retry_payload,
                    timeout=20
                )
            )


            print(
                "OSDI RETRY status:",
                retry_response.status_code
            )


            if retry_response.status_code in [
                200,
                201
            ]:

                return (
                    True,
                    retry_response.json()
                )


            try:

                retry_detail = (
                    retry_response.json()
                )

            except Exception:

                retry_detail = {
                    "message":
                        retry_response.text
                }


            return (
                False,
                {
                    "stage":
                        "retry_write",

                    "status":
                        retry_response.status_code,

                    "detail":
                        retry_detail
                }
            )


        # =================================================
        # 其他 HTTP 錯誤
        # =================================================

        try:

            error_detail = (
                response.json()
            )

        except Exception:

            error_detail = {
                "message":
                    response.text
            }


        return (
            False,
            {
                "stage":
                    "write",

                "status":
                    response.status_code,

                "detail":
                    error_detail
            }
        )


    # =====================================================
    # Timeout
    # =====================================================

    except requests.exceptions.Timeout:

        return (
            False,
            {
                "stage":
                    "write",

                "status":
                    "timeout",

                "detail":
                    "連線 GitHub 逾時"
            }
        )


    # =====================================================
    # Request Error
    # =====================================================

    except requests.exceptions.RequestException as e:

        return (
            False,
            {
                "stage":
                    "write",

                "status":
                    "request_error",

                "detail":
                    str(e)
            }
        )


    # =====================================================
    # 其他錯誤
    # =====================================================

    except Exception as e:

        return (
            False,
            {
                "stage":
                    "write",

                "status":
                    "unknown",

                "detail":
                    str(e)
            }
        )


# =========================================================
# OSDI 分數計算
# =========================================================

def calculate_osdi(
    responses
):

    sum_scores = 0

    answered_count = 0


    for q in all_questions:

        score = options_map[
            responses[q]
        ]


        # -1 = 未作答
        if score != -1:

            sum_scores += (
                score
            )

            answered_count += 1


    # =====================================================
    # OSDI 公式
    #
    # (回答分數總和 × 25)
    # ÷ 實際回答題數
    # =====================================================

    if answered_count > 0:

        osdi_score = (
            sum_scores
            * 25
            / answered_count
        )


        osdi_score = round(
            osdi_score,
            2
        )


    else:

        osdi_score = 0


    return (
        osdi_score,
        answered_count
    )


# =========================================================
# OSDI 程度判定
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

    /* ================================================
       主內容
    ================================================ */

    .block-container {
        max-width: 950px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }


    /* ================================================
       返回首頁
    ================================================ */

    .back-home {

        display: inline-block;

        margin-bottom: 18px;

        padding: 8px 16px;

        background-color: #EDE7E1;

        color: #6F6259 !important;

        text-decoration: none !important;

        border-radius: 10px;

        font-size: 14px;

        font-weight: 600;

        transition:
            background-color 0.2s ease;
    }


    .back-home:hover {

        background-color: #DDD3CA;

        color: #6F6259 !important;
    }


    /* ================================================
       標題
    ================================================ */

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


    /* ================================================
       Section
    ================================================ */

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


    /* ================================================
       Radio
    ================================================ */

    div[role="radiogroup"] {

        margin-bottom: 12px;
    }


    /* ================================================
       Submit
    ================================================ */

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


    /* ================================================
       結果
    ================================================ */

     .osdi-result {
        margin-top: 24px;
        padding: 30px 32px;
    
        background-color: #F5F0EB;
    
        border-radius: 18px;
    
        text-align: center;
    
        color: #6F6259;
    }
    
    .result-label {
        font-size: 15px;
        color: #8A817A;
        letter-spacing: 1px;
    }
    
    .osdi-score {
        font-size: 42px;
        font-weight: 700;
    
        color: #806F62;
    
        margin-top: 4px;
        margin-bottom: 20px;
    }
    
    .result-status-label {
        margin-top: 8px;
    }
    
    .result-status {
        display: inline-block;
    
        margin-top: 8px;
    
        padding: 8px 22px;
    
        background-color: #B5A293;
        color: white;
    
        border-radius: 20px;
    
        font-size: 18px;
        font-weight: 600;
    }
    
    .result-note {
        margin-top: 22px;
    
        color: #9A918A;
    
        font-size: 13px;
    
        line-height: 1.7;
    }
    /* ================================================
       手機
    ================================================ */

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
# 不再使用：
#
# st.switch_page("main.py")
#
# 因為 main.py 是 navigation entrypoint，
# 不是可以被 switch_page 直接指定的 page。
# =========================================================

st.markdown(
    """
    <a
        class="back-home"
        href="/"
        target="_self"
    >
        ← 返回首頁
    </a>
    """,
    unsafe_allow_html=True
)


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
    # A. 眼睛症狀
    # =====================================================

    st.markdown(
        """
        <div class="section-title">
            A. 眼睛症狀
        </div>
        """,
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

        responses[q] = (
            st.radio(
                q,

                options=list(
                    options_map.keys()
                ),

                # 預設「未作答」
                index=None,

                horizontal=True,

                key=f"osdi_{q}"
            )
        )


    # =====================================================
    # B. 日常活動
    # =====================================================

    st.markdown(
        """
        <div class="section-title">
            B. 日常活動
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="section-caption">
            在過去一週從事下列任一活動時，
            您是否曾因眼睛的問題而受到限制？
        </div>
        """,
        unsafe_allow_html=True
    )


    for q in cat_b:

        responses[q] = (
            st.radio(
                q,

                options=list(
                    options_map.keys()
                ),

                index=5,

                horizontal=True,

                key=f"osdi_{q}"
            )
        )


    # =====================================================
    # C. 環境因素
    # =====================================================

    st.markdown(
        """
        <div class="section-title">
            C. 環境因素
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="section-caption">
            在過去一週中遇到下列任一狀況時，
            您的眼睛是否曾感覺不適？
        </div>
        """,
        unsafe_allow_html=True
    )


    for q in cat_c:

        responses[q] = (
            st.radio(
                q,

                options=list(
                    options_map.keys()
                ),

                index=5,

                horizontal=True,

                key=f"osdi_{q}"
            )
        )


    # =====================================================
    # Submit
    # =====================================================

    submitted = (
        st.form_submit_button(
            "確認送出",
            use_container_width=True
        )
    )


# =========================================================
# 送出
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
    # 手機號碼
    # =====================================================

    elif not phone.strip():

        st.error(
            "請輸入手機號碼。"
        )


    # =====================================================
    # 建立資料
    # =====================================================

    else:

        current_data = {

            "姓名":
                name.strip(),

            "手機號碼":
                phone.strip()
        }


        # =================================================
        # 儲存每題回答
        # =================================================

        for q in all_questions:

            current_data[
                q
            ] = options_map[
                responses[q]
            ]


        # =================================================
        # OSDI 計算
        # =================================================

        (
            osdi_score,
            answered_count
        ) = calculate_osdi(
            responses
        )


        # =================================================
        # 全部都是未作答
        # =================================================

        if answered_count == 0:

            st.error(
                "請至少回答一題 OSDI 題目後再送出。"
            )


        else:

            # =============================================
            # 程度
            # =============================================

            status = (
                determine_osdi_status(
                    osdi_score
                )
            )


            # =============================================
            # 存結果
            # =============================================

            current_data[
                "OSDI總分"
            ] = osdi_score


            current_data[
                "程度評估"
            ] = status


            current_data[
                "填寫時間"
            ] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )


            # =============================================
            # 寫入 GitHub
            # =============================================

            with st.spinner(
                "正在儲存問卷資料..."
            ):

                success, result = (
                    save_to_github(
                        current_data
                    )
                )


            if success:
            
                st.success("眼睛疾病問卷送出成功！")
            
                st.markdown(
                    f"""
            <div class="osdi-result">
                <div class="result-label">OSDI 分數</div>
                <div class="osdi-score">{osdi_score}</div>
            
                <div class="result-label result-status-label">
                    評估結果
                </div>
            
                <div class="result-status">
                    {status}
                </div>
            
                <div class="result-note">
                    此結果僅供問卷評估參考，實際狀況仍需由專業醫療人員判斷。
                </div>
            </div>
                    """,
                    unsafe_allow_html=True
                )
            # =============================================
            # 失敗
            # =============================================

            else:

                st.error(
                    "問卷已完成，但資料沒有成功寫入 GitHub。"
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
