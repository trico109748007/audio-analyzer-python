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

    # 2. 上傳檔案到 Google File API (這是處理長音檔的關鍵！)
    # 這樣做可以讓 AI 讀取長達數小時的音檔，而不會被截斷
    audio_file = genai.upload_file(path=audio_file_path)
    
    print(f"檔案上傳完成: {audio_file.uri}")
    print("等待檔案處理中 (通常需要幾秒鐘)...")

    # 3. 等待檔案狀態轉為 'ACTIVE' (可用狀態)
    while audio_file.state.name == "PROCESSING":
        time.sleep(2)
        audio_file = genai.get_file(audio_file.name)

    if audio_file.state.name == "FAILED":
        raise ValueError("檔案處理失敗，請檢查格式是否支援。")

    print("檔案處理完成，開始呼叫 Gemini 進行分析...")

    # 4. 初始化模型 (gemini-2.5-flash)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")

    # 5. 設定精確的 Prompt (提示詞)
    # 這裡明確要求「時間軸」與「語者辨識」
    prompt = """
    你是一位專業的會議記錄與語音分析專家。請仔細聆聽這份錄音檔，並完成以下任務：

    1. **語者區隔 (Speaker Diarization)**：辨識有多少位不同的發言者，並根據聲音特徵給予標籤（例如：主持人、講者A、講者B...）。如果他們有自我介紹，請標註真實姓名或身份。
    2. **時間軸紀錄 (Timestamps)**：請依序列出對話內容，並標註精確的「開始時間」與「結束時間」。
    3. **逐字摘要**：摘要該段發言的重點。

    請以 Markdown 表格格式輸出，欄位包含：
    | 時間範圍 | 發言者 | 內容摘要/重點逐字 | 聲音特徵備註 |
    """

    # 6. 發送請求
    response = model.generate_content(
        [audio_file, prompt],
        request_options={"timeout": 600} # 設定較長的超時時間，避免分析到一半斷線
    )

    # 7. 輸出結果
    print("\n" + "="*30 + " 分析結果 " + "="*30 + "\n")
    print(response.text)
    
    # (選用) 分析結束後刪除雲端暫存檔，節省空間
    # genai.delete_file(audio_file.name)

# --- 執行程式 ---
# 請將這裡換成您電腦中錄音檔的實際路徑
file_path = r"G:\115.01.30 課中增置寒假場次-上午\01\115.01.30 課中增置寒假場次-上午-01.wav" 

try:
    analyze_audio_with_gemini(file_path)
except Exception as e:
    print(f"發生錯誤: {e}")