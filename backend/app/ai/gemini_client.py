# app/ai/gemini_client.py

import os
import google.generativeai as genai
from app.ai.ai_suggestion_client import AISuggestionClient

class GeminiAISuggestionClient(AISuggestionClient):
    def __init__(self, api_key: str|None = None, model_name: str|None = None):
        self.api_key = api_key or os.environ["GOOGLE_API_KEY"]
        self.model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
        print(f"[GeminiClient] Api Key: {self.api_key}")
        print(f"[GeminiClient] Using model: {self.model_name}")
        genai.configure(api_key=self.api_key)
        #models = self.list_models()  # 利用可能なモデルを確認
        self.model = genai.GenerativeModel(self.model_name)  # または "gemini-pro"

    def call_api(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[GeminiClient ERROR] {e}")
            raise RuntimeError(f"Gemini API 呼び出し中にエラーが発生しました: {str(e)}")


    def list_models(self) -> list:
        # 利用可能なモデルの一覧を取得して表示する例
        models = []
        for m in genai.list_models():
            if 'gemini' in m.name:
                models.append(m.name)
        return models
