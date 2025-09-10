import re
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import requests
import os
from langchain_core.tools import tool

# ==================== ICS 生成函数 ====================
def generate_ics_content(plan_text: str, start_date: datetime = None) -> bytes:
    """
    根据行程文本生成 iCalendar (.ics) 文件内容。
    """
    cal = Calendar()
    cal.add('prodid', '-//AI 旅行计划器//github.com//')
    cal.add('version', '2.0')

    if start_date is None:
        start_date = datetime.today()

    # 匹配 Day X
    day_pattern = re.compile(r'Day (\d+)[:\s]+(.*?)(?=Day \d+|$)', re.DOTALL)
    days = day_pattern.findall(plan_text)

    if not days:
        # 如果没有 Day X 格式，则将整个文本作为单个事件
        event = Event()
        event.add('summary', "旅行行程")
        event.add('description', plan_text)
        event.add('dtstart', start_date.date())
        event.add('dtend', start_date.date())
        event.add("dtstamp", datetime.now())
        cal.add_component(event)
    else:
        for day_num, day_content in days:
            day_num = int(day_num)
            current_date = start_date + timedelta(days=day_num - 1)
            
            event = Event()
            event.add('summary', f"第 {day_num} 天行程")
            event.add('description', day_content.strip())
            event.add('dtstart', current_date.date())
            event.add('dtend', current_date.date())
            event.add("dtstamp", datetime.now())
            cal.add_component(event)

    return cal.to_ical()

# ==================== 搜索工具 ====================
@tool
def search_web(query: str) -> str:
    """
    当你需要回答关于实时事件、地点、活动或任何需要最新信息的问题时，使用此工具进行网络搜索。
    它会返回一个包含搜索结果的字符串。
    """
    api_key = os.environ.get("SERP_API_KEY")
    if not api_key:
        return "错误: SerpAPI Key 未设置。"

    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google",
    }
    url = "https://serpapi.com/search"
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()
        
        snippets = []
        if "organic_results" in results:
            for result in results.get("organic_results", [])[:5]:
                snippet = result.get("snippet", "No snippet available.")
                title = result.get("title", "No title")
                link = result.get("link", "#")
                snippets.append(f"标题: {title}\n链接: {link}\n摘要: {snippet}\n---")
        
        if not snippets:
            return "未找到相关信息。"
            
        return "\n".join(snippets)

    except requests.exceptions.RequestException as e:
        return f"搜索请求失败: {e}"
    except Exception as e:
        return f"处理搜索结果时出错: {e}"