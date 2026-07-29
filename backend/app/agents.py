"""Specialist agent workflow with deterministic validation-friendly fallbacks.

Production deployments can add OpenAI Responses calls inside individual nodes.
The graph deliberately keeps memory reads/writes outside model prompts so personal
data can be minimized before any provider request.
"""
from typing import TypedDict
from langgraph.graph import END, StateGraph
from .services import assessment_result, correction, daily_lesson, mentor_reply

class CoachState(TypedDict, total=False):
    intent: str
    text: str
    answers: dict[str, str]
    scenario: str
    profile: object
    industry: str
    result: dict

def assessment_agent(state: CoachState): return {"result": assessment_result(state["answers"])}
def grammar_agent(state: CoachState): return {"result": correction(state["text"])}
def writing_agent(state: CoachState): return {"result": correction(state["text"])}
def conversation_agent(state: CoachState): return {"result": mentor_reply(state["text"], state.get("scenario", "professional communication"))}
def vocabulary_agent(state: CoachState): return {"result": daily_lesson(state["profile"], state.get("industry", "Technology"))["vocabulary"]}
def planner_agent(state: CoachState): return {"result": daily_lesson(state["profile"], state.get("industry", "Technology"))}

def route(state: CoachState):
    return {"assessment":"assessment", "grammar":"grammar", "writing":"writing", "conversation":"conversation", "vocabulary":"vocabulary", "plan":"planner"}.get(state["intent"], "grammar")

workflow = StateGraph(CoachState)
workflow.add_node("assessment", assessment_agent)
workflow.add_node("grammar", grammar_agent)
workflow.add_node("writing", writing_agent)
workflow.add_node("conversation", conversation_agent)
workflow.add_node("vocabulary", vocabulary_agent)
workflow.add_node("planner", planner_agent)
workflow.set_conditional_entry_point(route, {"assessment":"assessment", "grammar":"grammar", "writing":"writing", "conversation":"conversation", "vocabulary":"vocabulary", "planner":"planner"})
for name in ("assessment", "grammar", "writing", "conversation", "vocabulary", "planner"): workflow.add_edge(name, END)
supervisor = workflow.compile()

def run_agent(intent: str, **state):
    """Execute the supervisor graph and return the specialist's structured output."""
    return supervisor.invoke({"intent": intent, **state})["result"]
