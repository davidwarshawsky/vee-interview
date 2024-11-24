from langchain_core.language_models import BaseChatModel
# The thought process behind this is that each web page usually link to all relevant pages.
# You can navigate the entire website by getting the links that each webpage links to starting
# with the homepage. Then for each one of the webpages, see how well they do for each targeted audience.
from langchain_openai import ChatOpenAI
from typing import Annotated
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import Literal


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


def route_tools(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

def bind_llm_to_tools(llm:BaseChatModel,tools:list):
    return llm.bind_tools(tools)



def add(a,b):
    """
    Adds two integers together and returns the result.

    :param a: The first integer to be added.
    :param b: The second integer to be added.
    :return: The sum of the two integers.
    """
    print("add called")
    return a + b

load_dotenv()

# def main(llm,webpage_contents:dict):
    # all_content = "\n".join([f"{url}:\n{content}" for url,content in webpage_contents.items()])
def main(llm):
    tools = [add]
    llm_with_tools = bind_llm_to_tools(llm, tools)
    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}
    # def assistant(state: MessagesState):
    #     sys_msg = SystemMessage(content="You are a helpful assistant tasked with performing arithmetic on a set of inputs.")
    #     return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}


    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    # graph_builder.add_edge("chatbot", END)


    graph_builder.add_node("tools", ToolNode(tools))
    graph_builder.add_conditional_edges(
        "chatbot",
        route_tools,
        # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
        # It defaults to the identity function, but if you
        # want to use a node named something else apart from "tools",
        # You can update the value of the dictionary to something else
        # e.g., "tools": "my_tools"
        {"tools": "tools", END: END},
    )
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")

    graph = graph_builder.compile()

    # System message
    graph.get_graph().draw_mermaid_png(output_file_path="graph_2.png")

    def stream_graph_updates(graph,user_input: str):
        for event in graph.stream({"messages": [("user", user_input)]}):
            for value in event.values():
                print("Assistant:", value["messages"][-1].content)

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(graph,user_input)
        except:
            # fallback if input() is not available
            user_input = "What do you know about LangGraph?"
            print("User: " + user_input)
            stream_graph_updates(graph, user_input)
            break

if __name__ == "__main__":
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    main(llm)