import openai
import os
from dotenv import load_dotenv
import maps_api
from openai import AzureOpenAI
from openai.types.beta.tools import FunctionTool

load_dotenv()

# 初始化 Azure OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

GPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

# 註冊 maps_api 裡所有函數作為 tools
tools = [
    FunctionTool.from_function(maps_api.maps_geocode),
    FunctionTool.from_function(maps_api.maps_reverse_geocode),
    FunctionTool.from_function(maps_api.maps_search_places),
    FunctionTool.from_function(maps_api.maps_place_details),
    FunctionTool.from_function(maps_api.maps_distance_matrix),
    FunctionTool.from_function(maps_api.maps_elevation),
    FunctionTool.from_function(maps_api.maps_directions)
]

def ask_gpt_with_tool_call(question: str):
    # 第一次提問，等待 GPT 回傳 tool call 指令
    initial_response = client.chat.completions.create(
        model=GPT_DEPLOYMENT,
        tools=tools,
        messages=[
            {"role": "system", "content": "你是一個幫助使用者查詢地理資訊的助理"},
            {"role": "user", "content": question}
        ],
        tool_choice="auto"
    )

    choice = initial_response.choices[0]
    if not choice.message.tool_calls:
        print("🤖 GPT 回答：", choice.message.content)
        return

    tool_call = choice.message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = eval(tool_call.function.arguments)
    tool_func = getattr(maps_api, tool_name)
    tool_result = tool_func(**tool_args)

    # 將 tool 的結果傳回給 GPT
    followup_response = client.chat.completions.create(
        model=GPT_DEPLOYMENT,
        tools=tools,
        messages=[
            {"role": "system", "content": "你是一個幫助使用者查詢地理資訊的助理"},
            {"role": "user", "content": question},
            {"role": "assistant", "tool_calls": [tool_call]},
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": str(tool_result)
            }
        ]
    )

    print("\n🧠 GPT 回答：\n", followup_response.choices[0].message.content)

# --------------------------
# 📥 啟動互動式查詢
# --------------------------

if __name__ == "__main__":
    print("🌏 啟動 GPT 地圖助理，輸入自然語言問題（輸入 'exit' 離開）")
    while True:
        question = input("\n🧑 請輸入問題： ")
        if question.lower() in ["exit", "quit"]:
            break
        ask_gpt_with_tool_call(question)
