from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from config import anthropic_client
from query import embed_ques, get_related_from_graph, get_searched_chunks_from_chroma, get_related_from_graph, get_ans_from_claud


class EduMindState(TypedDict):
    question: str
    intent: str     # "answer", "quiz", "summarize"
    chunks: List[str]
    related_concepts: List[str]
    answer: str
    quiz_questions: List[str]
    summary: str


def orchestrator_node(state: EduMindState):
    response = anthropic_client.messages.create(
        model="claude-opus-4-5",
        max_tokens=50,
        system="Classify the user's intent as exactly one word: 'answer', 'quiz', or 'summarize'.",
        messages=[{"role": "user", "content": state["question"]}]
    )
    intent = response.content[0].text.strip().lower()
    return {"intent": intent}


def retrieval_node(state: EduMindState):
    question = state["question"]
    embedding = embed_ques(question)
    chunks = get_searched_chunks_from_chroma(embedding)
    related_concepts = get_related_from_graph(question)
    return {"chunks": chunks, "related_concepts": related_concepts}


def answer_node(state: EduMindState):
    response = get_ans_from_claud(
        state["question"],
        state["chunks"],
        state["related_concepts"]
    )
    return {"answer": response.content[0].text}


def quiz_node(state: EduMindState):
    context = "\n\n".join(state["chunks"])
    response = anthropic_client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system="Generate 3 quiz questions based on the context. Return as a numbered list.",
        messages=[{"role": "user", "content": f"Context:\n{context}"}]
    )
    return {"quiz_questions": [response.content[0].text]}


def summarizer_node(state: EduMindState):
    context = "\n\n".join(state["chunks"])
    response = anthropic_client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system="Summarize the context into concise study notes with key points.",
        messages=[{"role": "user", "content": f"Context:\n{context}"}]
    )
    return {"summary": response.content[0].text}


def route(state: EduMindState):
    return state["intent"]


def build_graph():
    graph = StateGraph(EduMindState)

    # Add nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("answer", answer_node)
    graph.add_node("quiz", quiz_node)
    graph.add_node("summarize", summarizer_node)

    # Entry point
    graph.set_entry_point("orchestrator")

    # Orchestrator routes to retrieval always
    graph.add_edge("orchestrator", "retrieval")

    # Retrieval routes based on intent
    graph.add_conditional_edges("retrieval", route, {
        "answer": "answer",
        "quiz": "quiz",
        "summarize": "summarize"
    })

    # All agents end after their node
    graph.add_edge("answer", END)
    graph.add_edge("quiz", END)
    graph.add_edge("summarize", END)

    return graph.compile()

agent = build_graph()

