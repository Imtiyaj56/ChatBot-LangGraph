from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, BaseMessage
from typing import TypedDict, Annotated
from dotenv import load_dotenv
import operator

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
checkpointer = InMemorySaver()   #CheckPointer


#Creating Node
graph.add_node('chat_node', chat_node)


#Creating Edges
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)


#Compiling the graph
chatbot = graph.compile(checkpointer=checkpointer)