import time
import os
from dotenv import load_dotenv
import google.generativeai as genai

# 1. 載入 .env 檔案中的設定
load_dotenv()

# 2. 從環境變數讀取 Key (如果沒讀到會回傳 None)
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("找不到 API Key，請檢查 .env 檔案！")

# 3. 設定 Gemini
genai.configure(api_key=api_key)

def analyze_audio_with_gemini(audio_file_path):
    print(f"正在處理檔案: {audio_file_path} ...")

    # 2. 上傳檔案
    audio_file = genai.upload_file(path=audio_file_path)
    print(f"檔案上傳完成: {audio_file.uri}")
    print("等待檔案處理中...")

    # 3. 等待處理
    while audio_file.state.name == "PROCESSING":
        time.sleep(2)
        audio_file = genai.get_file(audio_file.name)

    if audio_file.state.name == "FAILED":
        raise ValueError("檔案處理失敗。")

    print("檔案處理完成，開始分析...")

    # 4. 初始化模型
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")

    # ================= 修改點 1：修改 Prompt 要求 CSV 格式 =================
    prompt = """
    你是一位專業的會議記錄專家。請分析這份錄音檔：
    這是一個活動的錄音檔，請依據發言順序逐字整理內容，除了語氣詞與贅詞之外，請不要刪減內容。
    發言順序為：陳致澄教授、01-臺北市木柵國民中學、02-彰化縣大城國民中學、03-臺南市白河國民中學、
                04-臺東縣關山國民中學、05-高雄市燕巢國民中學、06-彰化縣大村國民中學、07-基隆市明德國民中學、
                08-基隆市成功國民中學、09-桃園市平鎮國民中學、10-雲林縣西螺國民中學、11-屏東縣林邊國民中學、
                12-屏東縣竹田國民中學、13-花蓮縣國風國民中學、14-屏東縣東新國民中學、盧昭雯老師、蘇恭弘研究教師、
                沈明勳教授、林盈甄教授、李韶瀛教授、陳致澄教授。
    1. **語者區隔**：辨識發言者並給予標籤）。
    2. **時間軸**：標註精確的「開始時間-結束時間」。
    
    請嚴格遵守以下輸出規則：
    1. **直接輸出 CSV 格式**內容，不要包含 Markdown 標記（如 ```csv），不要有任何開場白或結尾文字。
    2. 使用逗號 (,) 分隔，若內容包含逗號請用雙引號包覆。
    3. 第一行為標題列：
    時間範圍,發言者,內容摘要,聲音特徵
    """
    # ====================================================================

    # 6. 發送請求
    response = model.generate_content(
        [audio_file, prompt],
        request_options={"timeout": 600}
    )

    # ================= 修改點 2：輸出成 CSV 檔案 =================
    # 設定輸出的檔名 (您可以依需求修改)
    output_filename = "meeting_analysis.csv"

    # 清理可能殘留的 Markdown 標記 (以防 AI 還是加了 ```)
    csv_text = response.text.replace("```csv", "").replace("```", "").strip()

    try:
        # 使用 utf-8-sig 編碼，讓 Excel 開啟時中文不會亂碼
        with open(output_filename, "w", encoding="utf-8-sig") as f:
            f.write(csv_text)
        
        print("\n" + "="*30 + " 完成 " + "="*30)
        print(f"分析成功！結果已儲存至檔案：{output_filename}")
        print("您現在可以用 Excel 開啟這個檔案了。")
        
    except Exception as e:
        print(f"存檔時發生錯誤: {e}")
        # 如果存檔失敗，還是印出來以防資料遺失
        print(response.text)
    # ==========================================================
    
    # (選用) 分析結束後刪除雲端暫存檔，節省空間
    genai.delete_file(audio_file.name)

# --- 執行程式 ---
# 請將這裡換成您電腦中錄音檔的實際路徑
file_path = r"G:\115.01.30 課中增置寒假場次-上午\01\115.01.30 課中增置寒假場次-上午-01.wav" 

try:
    analyze_audio_with_gemini(file_path)
except Exception as e:
    print(f"發生錯誤: {e}")