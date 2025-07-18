import os
import json
import openai
from dotenv import load_dotenv
import maps_api

load_dotenv()

# 設定 Azure OpenAI 的參數
openai.api_type = "azure"
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2024-05-01-preview"

# 你在 Azure 上部署的 GPT-4o 模型名稱
MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

# 定義 function calling 所需的 functions（tools）清單
tools = [
    {
        "name": "maps_geocode",
        "description": "Convert address to geographic coordinates.",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "The full address to be converted to coordinates."
                }
            },
            "required": ["address"]
        }
    },
    {
        "name": "maps_reverse_geocode",
        "description": "Convert geographic coordinates to a human-readable address.",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Latitude coordinate."},
                "longitude": {"type": "number", "description": "Longitude coordinate."}
            },
            "required": ["latitude", "longitude"]
        }
    },
    {
        "name": "maps_search_places",
        "description": "Search for places based on a text query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword (e.g., 'coffee')."
                },
                "latitude": {
                    "type": "number",
                    "description": "Optional latitude for search.",
                    "default": None
                },
                "longitude": {
                    "type": "number",
                    "description": "Optional longitude for search.",
                    "default": None
                },
                "radius": {
                    "type": "number",
                    "description": "Search radius in meters (max 50000).",
                    "default": None
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "maps_place_details",
        "description": "Retrieve detailed information about a place using its place id.",
        "parameters": {
            "type": "object",
            "properties": {
                "place_id": {
                    "type": "string",
                    "description": "The unique identifier for the place."
                }
            },
            "required": ["place_id"]
        }
    },
    {
        "name": "maps_distance_matrix",
        "description": "Calculate distances and durations between origins and destinations.",
        "parameters": {
            "type": "object",
            "properties": {
                "origins": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of origin addresses."
                },
                "destinations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of destination addresses."
                },
                "mode": {
                    "type": "string",
                    "enum": ["driving", "walking", "bicycling", "transit"],
                    "description": "Travel mode (default: driving).",
                    "default": "driving"
                }
            },
            "required": ["origins", "destinations"]
        }
    },
    {
        "name": "maps_elevation",
        "description": "Retrieve elevation data for provided coordinates.",
        "parameters": {
            "type": "object",
            "properties": {
                "locations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        },
                        "required": ["latitude", "longitude"]
                    },
                    "description": "List of coordinate objects."
                }
            },
            "required": ["locations"]
        }
    },
    {
        "name": "maps_directions",
        "description": "Get step-by-step directions between two locations.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "The starting location/address."
                },
                "destination": {
                    "type": "string",
                    "description": "The destination location/address."
                },
                "mode": {
                    "type": "string",
                    "enum": ["driving", "walking", "bicycling", "transit"],
                    "description": "Travel mode (default: driving).",
                    "default": "driving"
                }
            },
            "required": ["origin", "destination"]
        }
    }
]

def ask_gpt_with_tool_call(question: str):
    messages = [
        {"role": "system", "content": "你是一個協助使用者查詢地理資訊的助手。"},
        {"role": "user", "content": question}
    ]
    
    # 向 GPT 送出請求，並啟用 function calling
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages,
        functions=tools,
        function_call="auto"  # 系統決定是否調用工具
    )
    
    message = response["choices"][0]["message"]
    if message.get("function_call"):
        function_name = message["function_call"]["name"]
        arguments_str = message["function_call"]["arguments"]
        try:
            arguments = json.loads(arguments_str)
        except Exception as e:
            print("解析 arguments 失敗:", e)
            return
        
        # 調用 maps_api 中對應的函式
        if hasattr(maps_api, function_name):
            func = getattr(maps_api, function_name)
            tool_result = func(**arguments)
        else:
            tool_result = f"無此功能： {function_name}"
        
        # 將工具結果加入訊息列表中
        messages.append(message)
        messages.append({
            "role": "function",
            "name": function_name,
            "content": json.dumps(tool_result, ensure_ascii=False)
        })
        
        # 接續與 GPT 的對話，取得最終回覆
        followup_response = openai.ChatCompletion.create(
            model=MODEL,
            messages=messages,
            functions=tools,
            function_call="none"
        )
        
        final_response = followup_response["choices"][0]["message"]["content"]
        print("\n🧠 GPT 回答：\n", final_response)
    else:
        # 若 GPT 不需要調用工具則直接回答
        print("\n🧠 GPT 回答：\n", message["content"])

if __name__ == "__main__":
    print("🌏 啟動 GPT 地圖助理，請輸入自然語言問題，或輸入 'exit' 離開。")
    while True:
        user_question = input("\n🧑 請輸入問題： ")
        if user_question.lower() in ["exit", "quit"]:
            break
        ask_gpt_with_tool_call(user_question)
