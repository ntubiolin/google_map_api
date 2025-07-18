# google_map_api
# API Example Usage
- python package dependency: `googlemaps`
- example usage: modify `API_KEY` in `google_map_api_example.py`, and then run `python google_map_api_example.py`
# Integration with LLM
- python package dependencies are specified in `requirements.txt`
- edit `.env` and run `python AzureOpenAI_gpt_4o_example.py`, example query: `我要怎麼開車從聯發科到台北101`
- file structure
```
your_project/
├── maps_api.py                     # ✅ 包含所有 Google Maps API function（純邏輯、無互動）
├── AzureOpenAI_gpt_4o_example.py   # ✅ 使用 Azure GPT-4o + Tool Calling + maps_api 做自然語言查詢
├── .env                            # ✅ 儲存 API 金鑰（不應上傳到 GitHub）
├── requirements.txt                # ✅ 安裝所需的 Python 套件
```
# Reference
- how to create google map api key: https://console.cloud.google.com/google/maps-apis/credentials 
- Anthropic MCP server -- Google Map MCP: https://github.com/modelcontextprotocol/servers-archived/tree/main/src/google-maps