"""Chat with the producer: content-pilot-agent ["make a short about ..."]"""

import json
import sys
import uuid

from langgraph.types import Command

from .harness import build_agent


def _review(interrupt) -> dict:
    """Ask the person about each pending render and build the resume payload."""
    decisions = []
    for req in interrupt.value["action_requests"]:
        print(f"\n--- Approval needed: {req['name']} {json.dumps(req['args'])}")
        answer = input("[a]pprove / [r]eject with feedback / [e]dit args as JSON: ").strip()
        if answer.lower().startswith("r"):
            note = input("Feedback for the producer: ").strip() or "Rejected."
            decisions.append({"type": "reject", "message": note})
        elif answer.lower().startswith("e"):
            args = json.loads(input("New args JSON: "))
            decisions.append({"type": "edit", "edited_action": {"name": req["name"], "args": args}})
        else:
            decisions.append({"type": "approve"})
    return {"decisions": decisions}


def _run(agent, payload, config) -> None:
    while True:
        result = agent.invoke(payload, config=config, version="v2")
        if not result.interrupts:
            print(f"\nproducer> {result.value['messages'][-1].text}\n")
            return
        payload = Command(resume={i.id: _review(i) for i in result.interrupts})


def main() -> None:
    agent = build_agent()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}, "recursion_limit": 200}
    first = " ".join(sys.argv[1:])
    print("content-pilot producer. Describe a video, or 'quit'.")
    while True:
        msg = first or input("you> ").strip()
        first = ""
        if msg.lower() in {"quit", "exit", "q"}:
            return
        if msg:
            _run(agent, {"messages": [{"role": "user", "content": msg}]}, config)


if __name__ == "__main__":
    main()
