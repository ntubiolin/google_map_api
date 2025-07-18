import os
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
        "name": "maps_geocode",
        "description": "Convert address to geographic coordinates",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "The address to geocode"}
            },
            "required": ["address"]
        }
    },
    {
        "name": "maps_reverse_geocode",
        "description": "Convert coordinates to a human-readable address",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"}
            },
            "required": ["latitude", "longitude"]
        }
    },
    {
        "name": "maps_search_places",
        "description": "Search for places using a text query",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "location": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"}
                    }
                },
                "radius": {"type": "integer"}
            }
        }
    },
    {
        "name": "maps_place_details",
        "description": "Get detailed information about a place by its ID",
        "parameters": {
            "type": "object",
            "properties": {
                "place_id": {"type": "string"}
            },
            "required": ["place_id"]
        }
    },
    {
        "name": "maps_distance_matrix",
        "description": "Calculate distances and times between points",
        "parameters": {
            "type": "object",
            "properties": {
                "origins": {"type": "array", "items": {"type": "string"}},
                "destinations": {"type": "array", "items": {"type": "string"}},
                "mode": {
                    "type": "string",
                    "enum": ["driving", "walking", "bicycling", "transit"]
                }
            },
            "required": ["origins", "destinations"]
        }
    },
    {
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
                        }
                    }
                }
            },
            "required": ["locations"]
        }
    },
    {
        "name": "maps_directions",
        "description": "Get step-by-step directions between two points",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "mode": {
                    "type": "string",
                    "enum": ["driving", "walking", "bicycling", "transit"]
                }
            },
            "required": ["origin", "destination"]
        }
    }
]

def ask_gpt_with_tool_call(question: str):
    # 初次呼叫 GPT，讓它判斷是否要用工具
    response = client.chat.completions.create(
        model=GPT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "你是一個地圖助理，幫助使用者查詢地理資訊。"},
            {"role": "user", "content": question}
        ],
        tools=tools,
        tool_choice="auto"
    )

    choice = response.choices[0]
    if not choice.message.tool_calls:
        print("🤖 GPT 回答：", choice.message.content)
        return

    tool_call = choice.message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = eval(tool_call.function.arguments)
    tool_func = getattr(maps_api, tool_name)
    tool_result = tool_func(**tool_args)

    # 將工具結果回傳給 GPT 進行最後回答
    followup = client.chat.completions.create(
        model=GPT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "你是一個地圖助理，幫助使用者查詢地理資訊。"},
            {"role": "user", "content": question},
            {"role": "assistant", "tool_calls": [tool_call]},
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": str(tool_result)
            }
        ],
        tools=tools
    )

    print("\n🧠 GPT 回答：\n", followup.choices[0].message.content)


if __name__ == "__main__":
    print("🌏 啟動 GPT 地圖助理，輸入自然語言問題（輸入 exit 離開）")
    while True:
        user_input = input("\n🧑 請輸入問題： ")
        if user_input.lower() in ("exit", "quit"):
            break
        ask_gpt_with_tool_call(user_input)
