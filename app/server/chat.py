import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from databricks.sdk import WorkspaceClient

router = APIRouter()

IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))
SUPERVISOR_ENDPOINT = "mas-979cea15-endpoint"


def get_client() -> WorkspaceClient:
    if IS_DATABRICKS_APP:
        host = os.environ.get("DATABRICKS_HOST", "")
        if host and not host.startswith("https://"):
            host = f"https://{host}"
        return WorkspaceClient(host=host)
    else:
        return WorkspaceClient(profile="fe-vm-bevbot-demo")


def extract_text(data: dict) -> str:
    """Extract assistant text from Agent Bricks Supervisor Agent response.

    Response shape:
    {"output": [{"type": "message", "role": "assistant",
                 "content": [{"type": "output_text", "text": "..."}]}]}
    """
    if "output" in data:
        output = data["output"]
        if isinstance(output, list):
            for item in reversed(output):
                if not isinstance(item, dict):
                    continue
                if item.get("role") == "assistant" or item.get("type") == "message":
                    content = item.get("content", [])
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "output_text":
                                return c.get("text", "")
                    elif isinstance(content, str):
                        return content
        elif isinstance(output, str):
            return output
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    return str(data)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class ChatResponse(BaseModel):
    message: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        client = get_client()

        input_messages = []
        for h in req.history:
            input_messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        input_messages.append({"role": "user", "content": req.message})

        # Agent Bricks Supervisor Agent endpoints use {"input": [...]} format.
        # api_client.do() handles auth automatically via service principal in both
        # local (CLI profile) and app (OAuth M2M) environments.
        data = client.api_client.do(
            "POST",
            f"/serving-endpoints/{SUPERVISOR_ENDPOINT}/invocations",
            body={"input": input_messages},
        )

        return ChatResponse(message=extract_text(data))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
