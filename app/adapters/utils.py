import httpx
import logging

logger = logging.getLogger("adapters.utils")

def split_text_smartly(text: str, max_length: int = 4096) -> list[str]:
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        split_at = max_length
        last_newline = text[:max_length].rfind('\n')
        
        if last_newline > max_length * 0.7:
            split_at = last_newline + 1
        else:
            last_space = text[:max_length].rfind(' ')
            if last_space > max_length * 0.7:
                split_at = last_space + 1

        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    
    return chunks

async def make_meta_request(method: str, url: str, token: str, payload: dict = None) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if method.upper() == "POST":
                resp = await client.post(url, json=payload, headers=headers)
            else:
                resp = await client.get(url, headers=headers)
            
        return {
            "success": resp.is_success,
            "status_code": resp.status_code,
            "data": resp.json() if resp.is_success else resp.text
        }
    except Exception as e:
        logger.error(f"Meta API Request Error: {e}")
        return {"success": False, "error": str(e)}