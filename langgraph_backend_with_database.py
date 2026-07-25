from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, BaseMessage
from typing import TypedDict, Annotated
from dotenv import load_dotenv
import operator
import sqlite3

load_dotenv()

model = ChatGroq(model="llama-3.3-70b-versatile")

#Creating State
class ChatStats(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  #BaseMessage- Inherits all types of message, add_messages- reducer


#Creating Function
def chat_node(state: ChatStats):
    messages = state['messages']
    response = model.invoke(messages)
    return {'messages': [response]}


#Creating Graph
graph = StateGraph(ChatStats)


connection = sqlite3.connect(database='chatbot.db', check_same_thread=False)
#CheckPointer
checkpointer = SqliteSaver(conn=connection)   


#Creating Node
graph.add_node('chat_node', chat_node)


#Creating Edges
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)


#Compiling the graph
chatbot = graph.compile(checkpointer=checkpointer)

#extracting all threads present in database....
def extract_all_threads():
    all_threads = set()    #taking set for extracting only unique thread_id
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)

