import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from tools import search_web

def create_travel_agent(llm, serp_api_key: str):
    """创建并返回一个 LangChain Agent Executor"""
    
    # 1. 将 SerpAPI Key 设置为环境变量，以便工具函数可以访问
    os.environ["SERP_API_KEY"] = serp_api_key

    # 2. 定义 Agent 可以使用的工具列表
    tools = [search_web]

    # 3. 创建一个提示模板，指导 Agent 的行为
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个世界顶级的旅行规划专家。
        你的任务是为用户创建一个详细、个性化且令人兴奋的旅行计划。
        步骤如下：
        1. 首先，使用 `search_web` 工具研究用户的目的地，收集关于必游景点、当地美食、特色活动和交通选择的信息。
        2. 在你认为收集到足够的信息后，停止使用工具。
        3. 最后，根据你收集到的所有信息，为用户生成一份结构清晰、按天组织的详细行程。
        4. 行程应该以 "这是为您规划的...行程：" 开头，并严格按照 "Day 1:", "Day 2:" 的格式组织。"""),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 4. 创建 Agent
    agent = create_tool_calling_agent(llm, tools, prompt)

    # 5. 创建 Agent 执行器
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return agent_executor

def get_langchain_plan(agent_executor, destination, num_days):
    """使用 LangChain Agent 生成行程"""
    prompt = f"请为我规划一个在 {destination} 的 {num_days} 天旅行。请确保行程丰富且合理。"
    response = agent_executor.invoke({"input": prompt})
    return response["output"]
