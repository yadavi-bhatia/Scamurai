from langgraph.graph import StateGraph, START, END
from state import CallState
from consensus import consensus_node
from audit_log import log_node

def voice_node(state: CallState):
    return {}

def transcript_node(state: CallState):
    return {}

builder = StateGraph(CallState)

builder.add_node("voice_node", voice_node)
builder.add_node("transcript_node", transcript_node)
builder.add_node("consensus_node", consensus_node)
builder.add_node("log_node", log_node)

builder.add_edge(START, "voice_node")
builder.add_edge(START, "transcript_node")
builder.add_edge("voice_node", "consensus_node")
builder.add_edge("transcript_node", "consensus_node")
builder.add_edge("consensus_node", "log_node")
builder.add_edge("log_node", END)

graph = builder.compile()