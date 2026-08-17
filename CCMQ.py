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

BRANCH = "main"
FILE_PATH = "ccmq_data.csv"

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

    "氣鬱質": [
        "您感到悶悶不樂、情緒低沉嗎？",
        "您容易精神緊張、焦慮不安嗎？",
        "您多愁善感、感情脆弱嗎？",
        "您容易感到害怕或受到驚嚇嗎？",
        "您胸脅部或乳房脹痛嗎？",
        "您無緣無故嘆氣嗎？",
        "您咽喉部有異物感，且吐之不出、咽之不下嗎？"
    ],

    "血瘀質": [
        "您的皮膚在不知不覺中會出現青紫瘀斑（皮下出血）嗎？",
        "您兩顴部有細微紅絲嗎？",
        "您身體上有哪裡疼痛嗎？",
        "您面色晦黯，或容易出現褐斑嗎？",
        "您容易有黑眼圈嗎？",
        "您容易忘事（健忘）嗎？",
        "您口唇顏色偏黯嗎？"
    ],

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

    "陽虛質": [
        "您手腳發冷嗎？",
        "您胃脘部、背部或腰膝部怕冷嗎？",
        "您感到怕冷、衣服比別人穿得多嗎？",
        "您比一般人耐受不了寒冷（冬天的寒冷、夏天的冷氣、電風扇等）嗎？",
        "您比別人容易患感冒嗎？",
        "您吃（喝）涼的東西會感到不舒服，或者怕吃（喝）涼的東西嗎？",
        "您受涼或吃（喝）涼的東西後容易腹瀉（拉肚子）嗎？"
    ],

    "濕熱質": [
        "您面部或鼻部有油膩感或者油亮發光嗎？",
        "您易生痤瘡或瘡癤嗎？",
        "您感到口苦或嘴裡有異味嗎？",
        "您大便黏滯不爽、有解不盡的感覺嗎？",
        "您小便時尿道有發熱感、尿色濃（深）嗎？",
        "您帶下色黃（白帶顏色發黃）嗎？（限女性）",
        "您陰囊部位潮濕嗎？（限男性）"
    ],

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
# 第 2、3、4、5、7、8 題
#
# Python index：
# 1、2、3、4、6、7
# =========================================================

reverse_questions = {
    "平和質": [1, 2, 3, 4, 6, 7]
}


# =========================================================
# CSV 欄位
# =========================================================

def create_columns():

    columns = [
        "姓名",
        "手機號碼"
    ]

    # 每一題
    for constitution, qs in questions.items():

        for i, _ in enumerate(
            qs,
            start=1
        ):

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


    columns.append(
        "填寫時間"
    )


    return columns


# =========================================================
# GitHub：讀取 CSV
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
            "CCMQ GET:",
            response.status_code,
            GITHUB_URL
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


            csv_bytes = base64.b64decode(
                encoded_content
            )


            csv_content = csv_bytes.decode(
                "utf-8-sig"
            )


            if csv_content.strip():

                try:

                    df = pd.read_csv(
                        StringIO(
                            csv_content
                        ),
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


            # -------------------------------------------------
            # 補齊欄位
            # -------------------------------------------------

            expected_columns = (
                create_columns()
            )


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


        # =================================================
        # CSV 尚未存在
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
                "status":
                    response.status_code,

                "detail":
                    detail
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
                "detail":
                    "GitHub 連線逾時"
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
# GitHub：PUT CSV
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
            (
                f"CCMQ questionnaire update - "
                f"{name}"
            ),

        "content":
            encoded_csv,

        "branch":
            BRANCH
    }


    # 已存在才放 SHA
    if sha is not None:

        payload[
            "sha"
        ] = sha


    try:

        response = requests.put(
            GITHUB_URL,
            headers=GITHUB_HEADERS,
            json=payload,
            timeout=30
        )


        print(
            "CCMQ PUT status:",
            response.status_code
        )


        print(
            "CCMQ PUT body:",
            response.text[:1500]
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


    except requests.exceptions.Timeout:

        return (
            False,
            {
                "status":
                    "timeout",

                "detail":
                    "GitHub 寫入逾時"
            }
        )


    except Exception as e:

        return (
            False,
            {
                "status":
                    "error",

                "detail":
                    str(e)
            }
        )


# =========================================================
# 儲存一筆問卷
# =========================================================

def save_to_github(
    current_data
):

    # -----------------------------------------------------
    # 讀最新版
    # -----------------------------------------------------

    latest_df, latest_sha, error = (
        get_github_data()
    )


    if error is not None:

        return (
            False,
            {
                "stage":
                    "read",

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

    success, result = (
        put_github_csv(
            updated_df,
            latest_sha,
            current_data["姓名"]
        )
    )


    if success:

        return (
            True,
            result
        )


    # =====================================================
    # SHA 衝突 → 再試一次
    # =====================================================

    if (
        isinstance(result, dict)
        and
        result.get("status") == 409
    ):

        retry_df, retry_sha, retry_error = (
            get_github_data()
        )


        if retry_error is not None:

            return (
                False,
                {
                    "stage":
                        "retry_read",

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
            "stage":
                "write",

            **result
        }
    )


# =========================================================
# GitHub：驗證資料
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


        # -------------------------------------------------
        # 統一轉成字串
        # -------------------------------------------------

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
            "CCMQ VERIFY ERROR:",
            e
        )

        return False


# =========================================================
# 計算體質分數
# =========================================================

def calculate_constitution_score(
    constitution,
    scores
):

    corrected_scores = (
        scores.copy()
    )


    # =====================================================
    # 平和質逆向
    # =====================================================

    if constitution in reverse_questions:

        for index in reverse_questions[
            constitution
        ]:

            corrected_scores[
                index
            ] = (
                6
                - corrected_scores[
                    index
                ]
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
        (
            raw_score
            - n
        )
        /
        (
            n
            * 4
        )
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
# 判定體質
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
    # -----------------------------------------------------

    if (
        pinghe_score >= 60
        and
        all(
            score < 30
            for score in other_scores
        )
    ):

        results[
            "平和質"
        ] = "是"


    # -----------------------------------------------------
    # 基本是
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


/* =====================================================
   主畫面
===================================================== */

.block-container {

    max-width: 1000px;

    padding-top: 2rem;

    padding-bottom: 5rem;
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


/* =====================================================
   Constitution
===================================================== */

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
   跟 OSDI 同色系
===================================================== */

.ccmq-result {

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


.result-main-title {

    margin-top: 6px;

    margin-bottom: 28px;

    font-size: 30px;

    font-weight: 700;

    color: #806F62;
}


/* =====================================================
   單一體質
===================================================== */

.constitution-result {

    padding: 18px 8px;

    border-top:
        1px solid #E1D8D0;
}


.constitution-result:first-child {

    border-top: none;
}


.constitution-name {

    font-size: 20px;

    font-weight: 700;

    color: #806F62;

    margin-bottom: 8px;
}


.constitution-score {

    color: #8A817A;

    font-size: 15px;

    margin-bottom: 9px;
}


.constitution-status {

    display: inline-block;

    padding: 7px 20px;

    background-color: #B5A293;

    color: white;

    border-radius: 22px;

    font-size: 15px;

    font-weight: 600;
}


.result-note {

    margin-top: 26px;

    padding-top: 20px;

    border-top:
        1px solid #E1D8D0;

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


    .ccmq-title {

        font-size: 27px;
    }


    .constitution-title {

        font-size: 20px;
    }


    .ccmq-result {

        padding:
            28px 20px;
    }

}

</style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 返回首頁
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
<div class="ccmq-title">
    中醫體質分類與判定表
</div>

<div class="ccmq-subtitle">
    請根據近一年的體驗和感覺回答下列問題
</div>
    """
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


    responses = {}


    # =====================================================
    # 九種體質
    # =====================================================

    for (
        constitution,
        qs
    ) in questions.items():


        st.html(
            f"""
<div class="constitution-title">
    {constitution}
</div>
            """
        )


        if constitution == "平和質":

            st.html(
                """
<div class="constitution-caption">
    請依照您近一年的實際感受作答。
</div>
                """
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


    # =====================================================
    # 漏答
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
            "請完成所有題目後再送出。"
        )


    # =====================================================
    # 正式計算
    # =====================================================

    else:


        current_data = {

            "姓名":
                name.strip(),

            "手機號碼":
                phone.strip()
        }


        raw_scores_by_constitution = {}


        # =================================================
        # 原始回答
        # =================================================

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
        # 計算分數
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
        # 體質判定
        # =================================================

        constitution_results = (
            determine_constitution(
                transformed_scores
            )
        )


        # =================================================
        # 加進 CSV Data
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
        # 填寫時間
        # =================================================

        filled_time = (
            datetime.now()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )


        current_data[
            "填寫時間"
        ] = filled_time


        # =================================================
        # ★ 先顯示結果
        #
        # 不管 GitHub 有沒有成功
        # 都會先顯示
        # =================================================

        constitution_html = ""


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


            constitution_html += f"""
<div class="constitution-result">

    <div class="constitution-name">
        {constitution}
    </div>

    <div class="constitution-score">
        轉化分：{score}
    </div>

    <div class="constitution-status">
        {result_text}
    </div>

</div>
"""


        result_html = f"""
<div class="ccmq-result">

    <div class="result-label">
        CCMQ
    </div>

    <div class="result-main-title">
        體質評估結果
    </div>

    {constitution_html}

    <div class="result-note">
        此結果僅供問卷評估參考，
        實際狀況仍需由專業醫療人員判斷。
    </div>

</div>
"""


        st.html(
            result_html
        )


        # =================================================
        # 再寫入 GitHub
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
        # GitHub 成功
        # =================================================

        if success:


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


            saved_confirmed = (
                verify_saved_data(
                    name.strip(),
                    phone.strip(),
                    filled_time
                )
            )


            if saved_confirmed:


                st.success(
                    "中醫體質問卷送出成功！"
                )


                st.caption(
                    f"資料已寫入："
                    f"{GITHUB_REPO}/"
                    f"{actual_path} "
                    f"（{BRANCH} branch）"
                )


            else:


                st.warning(
                    "體質評估已完成，"
                    "GitHub API 回報寫入成功，"
                    "但目前無法再次確認 CSV 資料。"
                )


        # =================================================
        # GitHub 失敗
        # =================================================

        else:


            st.warning(
                "體質評估已完成，"
                "但資料目前沒有成功寫入 GitHub。"
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
