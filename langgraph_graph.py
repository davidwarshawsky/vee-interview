# SHOWS MY ABILITY TO USE LANGGRAPH BUT REMOVED FUNCTIONALITY AND MOVED IT ELSEWHERE AS IT WAS NOT NEEDED FOR THE FINAL PROJECT OF 
# SUMMARIZATION

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.constants import START, END
from langgraph.graph import add_messages, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import Annotated, TypedDict

from website_scraper import get_content

load_dotenv()

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


def bind_llm_to_tools(llm:BaseChatModel,tools:list):
    return llm.bind_tools(tools)

llm = ChatOpenAI(model="gpt-4o")
tools = []
llm_with_tools = bind_llm_to_tools(llm, tools)
def assistant(state: MessagesState):
    sys_msg = SystemMessage(content="You are a link extractor")
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}


graph_builder = StateGraph(State)
graph_builder.add_node("assistant", assistant)
graph_builder.add_edge(START, "assistant")
graph_builder.add_edge("assistant", END)
# graph_builder.add_node("tools", ToolNode(tools))
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition
)

graph = graph_builder.compile()

# System message
graph.get_graph().draw_mermaid_png(output_file_path="graph_3.png")


