from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, BaseMessage
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from typing import Literal
import operator
import requests
import sqlite3

load_dotenv()

model = ChatGroq(model="llama-3.3-70b-versatile", streaming=False)

# Tools
search = DuckDuckGoSearchRun(region="us-en")

@tool
def web_search(query: str) -> str:
    """Search the web for the given query and return relevant results."""
    try:
        return search.run(query)
    except Exception as e:
        return f"Search failed: {str(e)}"

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    r = requests.get(url)
    return r.json()


tools = [web_search, get_stock_price, calculator]
model_with_tools = model.bind_tools(tools)

#Creating State
class ChatStats(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  #BaseMessage- Inherits all types of message, add_messages- reducer


#Creating Function
def chat_node(state: ChatStats):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools, handle_tool_errors=True)


#Creating Graph
graph = StateGraph(ChatStats)


connection = sqlite3.connect(database='chatbot.db', check_same_thread=False)
#CheckPointer
checkpointer = SqliteSaver(conn=connection)   


#Creating Node
graph.add_node('chat_node', chat_node)
graph.add_node("tools", tool_node)


#Creating Edges
graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')


#Compiling the graph
chatbot = graph.compile(checkpointer=checkpointer)

#extracting all threads present in database....
def extract_all_threads():
    all_threads = set()    #taking set for extracting only unique thread_id
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)

