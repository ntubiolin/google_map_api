import os
import json
from dotenv import load_dotenv
import maps_api
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

GPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

tools = [
    {
        "type": "function",
        "function": {
            "name": "maps_geocode",
            "description": "Convert address to geographic coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {"type": "string", "description": "The address to geocode"}
                },
                "required": ["address"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "maps_reverse_geocode",
            "description": "Convert coordinates to a human-readable address",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Latitude of the location"},
                    "longitude": {"type": "number", "description": "Longitude of the location"}
                },
                "required": ["latitude", "longitude"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "maps_search_places",
            "description": "Search for places using a text query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Text query to search for places"},
                    "latitude": {"type": "number", "description": "Latitude for location-based search (optional)"},
                    "longitude": {"type": "number", "description": "Longitude for location-based search (optional)"},
                    "radius": {"type": "integer", "description": "Search radius in meters (optional)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "maps_place_details",
            "description": "Get detailed information about a place",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_id": {"type": "string", "description": "The place ID"}
                },
                "required": ["place_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "maps_distance_matrix",
            "description": "Calculate distances and times between points",
            "parameters": {
                "type": "object",
                "properties": {
                    "origins": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of origin addresses"
                    },
                    "destinations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of destination addresses"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["driving", "walking", "bicycling", "transit"],
                        "description": "Mode of transportation"
                    }
                },
                "required": ["origins", "destinations"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "maps_elevation",
            "description": "Get elevation data for locations",
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
                        "description": "Array of location objects with latitude and longitude"
                    }
                },
                "required": ["locations"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "maps_directions",
            "description": "Get directions between points",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Start address"},
                    "destination": {"type": "string", "description": "End address"},
                    "mode": {
                        "type": "string",
                        "enum": ["driving", "walking", "bicycling", "transit"],
                        "description": "Mode of transportation"
                    }
                },
                "required": ["origin", "destination"]
            }
        }
    }
]

def ask_gpt_with_tool_call(question: str):
    # 初始化對話訊息
    messages = [
        {"role": "system", "content": "你是一個地圖助理，幫助使用者查詢地理資訊。"},
        {"role": "user", "content": question}
    ]
    
    max_iterations = 10  # 防止無限循環
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n🔄 執行第 {iteration} 步...")
        
        # 呼叫 GPT
        response = client.chat.completions.create(
            model=GPT_DEPLOYMENT,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        choice = response.choices[0]
        
        # 如果沒有工具呼叫，表示 GPT 已經可以回答了
        if not choice.message.tool_calls:
            print("🤖 GPT 回答：", choice.message.content)
            return
        
        # 處理所有工具呼叫（GPT 可能同時呼叫多個工具）
        tool_messages = []
        assistant_message = {
            "role": "assistant",
            "tool_calls": choice.message.tool_calls
        }
        messages.append(assistant_message)
        
        for tool_call in choice.message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                print(f"❌ 無法解析工具參數：{tool_call.function.arguments}")
                continue
            
            print(f"🔧 執行工具：{tool_name}")
            print(f"📝 參數：{tool_args}")
            
            try:
                tool_func = getattr(maps_api, tool_name)
                tool_result = tool_func(**tool_args)
                print(f"✅ 工具結果：{str(tool_result)[:200]}...")
                
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(tool_result)
                }
                tool_messages.append(tool_message)
                
            except Exception as e:
                print(f"❌ 工具執行錯誤：{str(e)}")
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": f"錯誤：{str(e)}"
                }
                tool_messages.append(tool_message)
        
        # 將工具結果加入對話歷史
        messages.extend(tool_messages)
    
    print("⚠️ 已達到最大迭代次數，停止執行。")


if __name__ == "__main__":
    print("🌏 啟動 GPT 地圖助理，支援多步驟函數呼叫（輸入 exit 離開）")
    print("\n📋 範例問題：")
    print("  • 台北101附近有哪些餐廳？然後告訴我到最近的一間要多久？")
    print("  • 找出新北市政府的地址，然後計算從台北車站到那裡的距離")
    print("  • 搜尋台北的咖啡廳，並提供前三間的詳細資訊")
    
    while True:
        user_input = input("\n🧑 請輸入問題： ")
        if user_input.lower() in ("exit", "quit"):
            break
        ask_gpt_with_tool_call(user_input)
