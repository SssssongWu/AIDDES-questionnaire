import streamlit as st
import pandas as pd
import requests
import base64
import json

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

FILE_PATH = "ccmq_data.csv"

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
# 選項
# =========================================================

options_map = {
    "沒有": 1,
    "很少": 2,
    "有時": 3,
    "經常": 4,
    "總是": 5
}


# =========================================================
# CCMQ 題目
# =========================================================

questions = {

    # =====================================================
    # 平和質
    # =====================================================
    "平和質": [
        "您精力充沛嗎？",
        "您容易疲乏嗎？",
        "您說話聲音低弱無力嗎？",
        "您感到悶悶不樂、情緒低沉嗎？",
        "您比一般人耐受不了寒冷（冬天的寒冷、夏天的冷氣、電風扇等）嗎？",
        "您能適應外界自然和社會環境的變化嗎？",
        "您容易失眠嗎？",
        "您容易忘事（健忘）嗎？"
    ],

    # =====================================================
    # 氣虛質
    # =====================================================
    "氣虛質": [
        "您容易疲乏嗎？",
        "您容易氣短（呼吸短促、接不上氣）嗎？",
        "您容易心慌嗎？",
        "您容易頭暈或站起時暈眩嗎？",
        "您比別人容易患感冒嗎？",
        "您喜歡安靜、懶得說話嗎？",
        "您說話聲音低弱無力嗎？",
        "您活動量稍大就容易出虛汗嗎？"
    ],

    # =====================================================
    # 痰濕質
    # =====================================================
    "痰濕質": [
        "您感到胸悶或腹部脹滿嗎？",
        "您感到身體沉重不輕鬆或不爽快嗎？",
        "您腹部肥滿鬆軟嗎？",
        "您有額部油脂分泌多的現象嗎？",
        "您上眼瞼比別人腫（上眼瞼有輕微隆起的現象）嗎？",
        "您嘴裡有黏黏的感覺嗎？",
        "您平時痰多，特別是咽喉部總感到有痰堵著嗎？",
        "您舌苔厚膩或有舌苔厚厚的感覺嗎？"
    ],

    # =====================================================
    # 氣鬱質
    # =====================================================
    "氣鬱質": [
        "您感到悶悶不樂、情緒低沉嗎？",
        "您容易精神緊張、焦慮不安嗎？",
        "您多愁善感、感情脆弱嗎？",
        "您容易感到害怕或受到驚嚇嗎？",
        "您胸脅部或乳房脹痛嗎？",
        "您無緣無故嘆氣嗎？",
        "您咽喉部有異物感，且吐之不出、咽之不下嗎？"
    ],

    # =====================================================
    # 血瘀質
    # =====================================================
    "血瘀質": [
        "您的皮膚在不知不覺中會出現青紫瘀斑（皮下出血）嗎？",
        "您兩顴部有細微紅絲嗎？",
        "您身體上有哪裡疼痛嗎？",
        "您面色晦黯，或容易出現褐斑嗎？",
        "您容易有黑眼圈嗎？",
        "您容易忘事（健忘）嗎？",
        "您口唇顏色偏黯嗎？"
    ],

    # =====================================================
    # 陰虛質
    # =====================================================
    "陰虛質": [
        "您感到手腳心發熱嗎？",
        "您感覺身體、臉上發熱嗎？",
        "您皮膚或口唇乾嗎？",
        "您口唇的顏色比一般人紅嗎？",
        "您容易便秘或大便乾燥嗎？",
        "您面部兩顴潮紅或偏紅嗎？",
        "您感到眼睛乾澀嗎？",
        "您感到口乾咽燥、總想喝水嗎？"
    ],

    # =====================================================
    # 陽虛質
    # =====================================================
    "陽虛質": [
        "您手腳發冷嗎？",
        "您胃脘部、背部或腰膝部怕冷嗎？",
        "您感到怕冷、衣服比別人穿得多嗎？",
        "您比一般人耐受不了寒冷（冬天的寒冷、夏天的冷氣、電風扇等）嗎？",
        "您比別人容易患感冒嗎？",
        "您吃（喝）涼的東西會感到不舒服，或者怕吃（喝）涼的東西嗎？",
        "您受涼或吃（喝）涼的東西後容易腹瀉（拉肚子）嗎？"
    ],

    # =====================================================
    # 濕熱質
    # =====================================================
    "濕熱質": [
        "您面部或鼻部有油膩感或者油亮發光嗎？",
        "您易生痤瘡或瘡癤嗎？",
        "您感到口苦或嘴裡有異味嗎？",
        "您大便黏滯不爽、有解不盡的感覺嗎？",
        "您小便時尿道有發熱感、尿色濃（深）嗎？",
        "您帶下色黃（白帶顏色發黃）嗎？（限女性）",
        "您陰囊部位潮濕嗎？（限男性）"
    ],

    # =====================================================
    # 特稟質
    # =====================================================
    "特稟質": [
        "您不感冒也會打噴嚏嗎？",
        "您不感冒也會鼻塞、流鼻涕嗎？",
        "您有因季節變化、溫度變化或異味等原因而咳喘的現象嗎？",
        "您容易過敏（對藥物、食物、氣味、花粉或在季節交替、氣候變化時）嗎？",
        "您的皮膚容易起蕁麻疹（風團、風疹塊、風疙瘩）嗎？",
        "您的皮膚因過敏出現過紫瘢（紫紅色瘀點、瘀斑）嗎？",
        "您的皮膚一抓就紅，並出現抓痕嗎？"
    ]
}


# =========================================================
# 平和質逆向題
#
# 第 2、3、4、5、7、8 題逆向
#
# Python index：
# 1、2、3、4、6、7
# =========================================================

reverse_questions = {
    "平和質": [1, 2, 3, 4, 6, 7]
}


# =========================================================
# 建立 CSV 欄位
# =========================================================

def create_columns():

    columns = [
        "姓名",
        "手機號碼"
    ]

    # 每一題
    for constitution, qs in questions.items():

        for i, _ in enumerate(qs, start=1):

            columns.append(
                f"{constitution}_Q{i}"
            )

    # 原始分
    for constitution in questions:

        columns.append(
            f"{constitution}_原始分"
        )

    # 轉化分
    for constitution in questions:

        columns.append(
            f"{constitution}_轉化分"
        )

    # 判定
    for constitution in questions:

        columns.append(
            f"{constitution}_判定"
        )

    columns.append("填寫時間")

    return columns


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
            "GET GitHub status:",
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

            csv_content = base64.b64decode(
                encoded_content
            ).decode(
                "utf-8"
            )

            # CSV 有資料
            if csv_content.strip():

                try:

                    df = pd.read_csv(
                        StringIO(csv_content)
                    )

                except pd.errors.EmptyDataError:

                    df = pd.DataFrame(
                        columns=create_columns()
                    )

            # CSV 空檔案
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
        # CSV 不存在
        # 第一次使用
        # =================================================
        elif response.status_code == 404:

            df = pd.DataFrame(
                columns=create_columns()
            )

            return (
                df,
                None,
                None
            )


        # =================================================
        # GitHub API 錯誤
        # =================================================
        else:

            try:

                error_detail = response.json()

            except Exception:

                error_detail = {
                    "message": response.text
                }

            return (
                pd.DataFrame(
                    columns=create_columns()
                ),
                None,
                {
                    "status": response.status_code,
                    "detail": error_detail
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


    except requests.exceptions.RequestException as e:

        return (
            pd.DataFrame(
                columns=create_columns()
            ),
            None,
            {
                "status": "request_error",
                "detail": str(e)
            }
        )


    except Exception as e:

        return (
            pd.DataFrame(
                columns=create_columns()
            ),
            None,
            {
                "status": "unknown",
                "detail": str(e)
            }
        )


# =========================================================
# 寫入 GitHub
#
# 重要：
# 每次送出都重新抓最新 CSV + sha
# 避免使用者開頁面太久後 sha 過期
# =========================================================

def save_to_github(current_data):

    # -----------------------------------------------------
    # 送出當下重新讀最新資料
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # 確保欄位完整
    # -----------------------------------------------------

    expected_columns = create_columns()

    for col in expected_columns:

        if col not in latest_df.columns:

            latest_df[col] = ""


    # 依照固定欄位排序
    latest_df = latest_df[
        expected_columns
    ]


    # -----------------------------------------------------
    # 新資料
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # CSV
    #
    # utf-8-sig：
    # Excel 開啟中文比較不容易亂碼
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
    # GitHub payload
    # -----------------------------------------------------

    payload = {
        "message":
            f"CCMQ questionnaire update - "
            f"{current_data['姓名']}",

        "content":
            encoded_csv
    }


    # CSV 已存在才需要 sha
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
            "PUT GitHub status:",
            response.status_code
        )

        print(
            "PUT GitHub response:",
            response.text[:1000]
        )


        # 200 = 更新
        # 201 = 新建
        if response.status_code in [
            200,
            201
        ]:

            return (
                True,
                response.json()
            )


        # -------------------------------------------------
        # 如果剛好有人同時寫入造成 sha conflict
        # 再嘗試一次
        # -------------------------------------------------

        if response.status_code == 409:

            retry_df, retry_sha, retry_error = (
                get_github_data()
            )

            if retry_error is not None:

                return (
                    False,
                    {
                        "stage": "retry_read",
                        "error": retry_error
                    }
                )


            for col in expected_columns:

                if col not in retry_df.columns:

                    retry_df[col] = ""


            retry_df = retry_df[
                expected_columns
            ]


            retry_updated_df = pd.concat(
                [
                    retry_df,
                    pd.DataFrame(
                        [current_data]
                    )
                ],
                ignore_index=True
            )


            retry_csv = retry_updated_df.to_csv(
                index=False
            )


            retry_payload = {
                "message":
                    f"CCMQ questionnaire update - "
                    f"{current_data['姓名']}",

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


            retry_response = requests.put(
                GITHUB_URL,
                headers=GITHUB_HEADERS,
                json=retry_payload,
                timeout=20
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
                    "stage": "retry_write",
                    "status":
                        retry_response.status_code,
                    "detail":
                        retry_detail
                }
            )


        # -------------------------------------------------
        # 其他錯誤
        # -------------------------------------------------

        try:

            error_detail = response.json()

        except Exception:

            error_detail = {
                "message":
                    response.text
            }


        return (
            False,
            {
                "stage": "write",
                "status":
                    response.status_code,
                "detail":
                    error_detail
            }
        )


    except requests.exceptions.Timeout:

        return (
            False,
            {
                "stage": "write",
                "status": "timeout",
                "detail":
                    "連線 GitHub 逾時"
            }
        )


    except requests.exceptions.RequestException as e:

        return (
            False,
            {
                "stage": "write",
                "status": "request_error",
                "detail": str(e)
            }
        )


    except Exception as e:

        return (
            False,
            {
                "stage": "write",
                "status": "unknown",
                "detail": str(e)
            }
        )


# =========================================================
# 計算某一體質分數
# =========================================================

def calculate_constitution_score(
    constitution,
    scores
):

    corrected_scores = scores.copy()


    # =====================================================
    # 逆向題
    #
    # 1 → 5
    # 2 → 4
    # 3 → 3
    # 4 → 2
    # 5 → 1
    #
    # 公式：6 - score
    # =====================================================

    if constitution in reverse_questions:

        for index in reverse_questions[
            constitution
        ]:

            corrected_scores[index] = (
                6 - corrected_scores[index]
            )


    # =====================================================
    # 原始分
    # =====================================================

    raw_score = sum(
        corrected_scores
    )

    n = len(
        corrected_scores
    )


    # =====================================================
    # 轉化分
    #
    # [(原始分 - 條目數)
    # / (條目數 × 4)] × 100
    # =====================================================

    transformed_score = (
        (raw_score - n)
        /
        (n * 4)
    ) * 100


    transformed_score = round(
        transformed_score,
        2
    )


    return (
        raw_score,
        transformed_score
    )


# =========================================================
# 判定九種體質
# =========================================================

def determine_constitution(
    transformed_scores
):

    results = {}


    # =====================================================
    # 八種偏頗體質
    # =====================================================

    for (
        constitution,
        score
    ) in transformed_scores.items():

        if constitution == "平和質":

            continue


        if score >= 40:

            results[
                constitution
            ] = "是"


        elif score >= 30:

            results[
                constitution
            ] = "傾向是"


        else:

            results[
                constitution
            ] = "否"


    # =====================================================
    # 平和質
    # =====================================================

    pinghe_score = (
        transformed_scores[
            "平和質"
        ]
    )


    other_scores = [

        score

        for (
            constitution,
            score
        ) in transformed_scores.items()

        if constitution != "平和質"
    ]


    # -----------------------------------------------------
    # 是
    # 平和 >= 60
    # 其他全部 < 30
    # -----------------------------------------------------

    if (
        pinghe_score >= 60
        and
        all(
            score < 30
            for score in other_scores
        )
    ):

        results["平和質"] = "是"


    # -----------------------------------------------------
    # 基本是
    # 平和 >= 60
    # 其他全部 < 40
    # -----------------------------------------------------

    elif (
        pinghe_score >= 60
        and
        all(
            score < 40
            for score in other_scores
        )
    ):

        results[
            "平和質"
        ] = "基本是"


    else:

        results[
            "平和質"
        ] = "否"


    return results


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
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 5rem;
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
    }


    .back-home:hover {
        background-color: #DDD3CA;
    }


    /* ================================================
       標題
    ================================================ */

    .ccmq-title {
        text-align: center;

        font-size: 34px;

        font-weight: 700;

        color: #6F6259;

        margin-bottom: 8px;
    }


    .ccmq-subtitle {
        text-align: center;

        color: #8A817A;

        font-size: 15px;

        margin-bottom: 30px;
    }


    /* ================================================
       體質標題
    ================================================ */

    .constitution-title {

        font-size: 23px;

        font-weight: 700;

        color: #6F6259;

        margin-top: 36px;

        margin-bottom: 8px;

        padding-bottom: 8px;

        border-bottom:
            2px solid #DDD4CC;
    }


    .constitution-caption {

        color: #8D8782;

        font-size: 14px;

        margin-bottom: 18px;
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

    .result-box {

        background-color: #F3EFEA;

        border-radius: 14px;

        padding: 18px 22px;

        margin-top: 12px;

        margin-bottom: 12px;
    }


    /* ================================================
       手機
    ================================================ */

    @media (max-width: 768px) {

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .ccmq-title {
            font-size: 27px;
        }

        .constitution-title {
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
# 不使用：
# st.switch_page("main.py")
#
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
# 頁面標題
# =========================================================

st.markdown(
    """
    <div class="ccmq-title">
        中醫體質分類與判定表
    </div>

    <div class="ccmq-subtitle">
        請根據近一年的體驗和感覺回答下列問題
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 問卷
# =========================================================

with st.form(
    "ccmq_survey_form"
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


    # =====================================================
    # 儲存回答
    # =====================================================

    responses = {}


    # =====================================================
    # 九種體質
    # =====================================================

    for (
        constitution,
        qs
    ) in questions.items():


        st.markdown(
            f"""
            <div class="constitution-title">
                {constitution}
            </div>
            """,
            unsafe_allow_html=True
        )


        # -------------------------------------------------
        # 平和質提醒
        # -------------------------------------------------

        if constitution == "平和質":

            st.markdown(
                """
                <div class="constitution-caption">
                    請依照您近一年的實際感受作答。
                </div>
                """,
                unsafe_allow_html=True
            )


        # -------------------------------------------------
        # 題目
        # -------------------------------------------------

        for i, q in enumerate(
            qs,
            start=1
        ):

            key = (
                f"{constitution}_Q{i}"
            )


            responses[
                key
            ] = st.radio(

                f"{i}. {q}",

                options=list(
                    options_map.keys()
                ),

                index=None,

                horizontal=True,

                key=f"radio_{key}"
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
# 送出處理
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
    # 檢查有沒有漏答
    # =====================================================

    elif any(
        answer is None
        for answer in responses.values()
    ):

        unanswered = sum(
            answer is None
            for answer in responses.values()
        )


        st.error(
            f"尚有 {unanswered} 題未填寫，"
            f"請完成所有題目後再送出。"
        )


    # =====================================================
    # 全部完成
    # =====================================================

    else:


        # =================================================
        # 建立單筆資料
        # =================================================

        current_data = {

            "姓名":
                name.strip(),

            "手機號碼":
                phone.strip()
        }


        # =================================================
        # 每一體質回答
        # =================================================

        raw_scores_by_constitution = {}


        for (
            constitution,
            qs
        ) in questions.items():


            constitution_scores = []


            for i, _ in enumerate(
                qs,
                start=1
            ):

                key = (
                    f"{constitution}_Q{i}"
                )


                answer_text = (
                    responses[
                        key
                    ]
                )


                score = (
                    options_map[
                        answer_text
                    ]
                )


                # -----------------------------------------
                # CSV 儲存使用者原始回答
                # 1 ~ 5
                # -----------------------------------------

                current_data[
                    key
                ] = score


                constitution_scores.append(
                    score
                )


            raw_scores_by_constitution[
                constitution
            ] = constitution_scores


        # =================================================
        # 計算體質
        # =================================================

        raw_total_scores = {}

        transformed_scores = {}


        for (
            constitution,
            constitution_scores
        ) in (
            raw_scores_by_constitution.items()
        ):


            (
                raw_score,
                transformed_score
            ) = (
                calculate_constitution_score(
                    constitution,
                    constitution_scores
                )
            )


            raw_total_scores[
                constitution
            ] = raw_score


            transformed_scores[
                constitution
            ] = transformed_score


        # =================================================
        # 判定
        # =================================================

        constitution_results = (
            determine_constitution(
                transformed_scores
            )
        )


        # =================================================
        # 存入資料
        # =================================================

        for constitution in questions:


            current_data[
                f"{constitution}_原始分"
            ] = (
                raw_total_scores[
                    constitution
                ]
            )


            current_data[
                f"{constitution}_轉化分"
            ] = (
                transformed_scores[
                    constitution
                ]
            )


            current_data[
                f"{constitution}_判定"
            ] = (
                constitution_results[
                    constitution
                ]
            )


        # =================================================
        # 時間
        # =================================================

        current_data[
            "填寫時間"
        ] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        # =================================================
        # 寫入 GitHub
        # =================================================

        with st.spinner(
            "正在儲存問卷資料..."
        ):


            success, result = (
                save_to_github(
                    current_data
                )
            )


        # =================================================
        # 成功
        # =================================================

        if success:


            st.success(
                "中醫體質問卷送出成功！"
            )


            st.markdown(
                "### 體質評估結果"
            )


            for constitution in questions:


                score = (
                    transformed_scores[
                        constitution
                    ]
                )


                result_text = (
                    constitution_results[
                        constitution
                    ]
                )


                st.markdown(
                    f"""
                    <div class="result-box">

                        <b>
                            {constitution}
                        </b>

                        <br>

                        轉化分：
                        {score}

                        <br>

                        判定：
                        <b>
                            {result_text}
                        </b>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


        # =================================================
        # 失敗
        # =================================================

        else:


            st.error(
                "問卷已完成，但資料沒有成功寫入 GitHub。"
            )


            # ---------------------------------------------
            # 顯示詳細原因
            # 方便現在除錯
            # ---------------------------------------------

            if isinstance(
                result,
                dict
            ):

                stage = result.get(
                    "stage",
                    ""
                )

                status = result.get(
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


                if status:

                    st.write(
                        f"HTTP 狀態：{status}"
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
