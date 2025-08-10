import asyncio
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from together import Together
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken

load_dotenv()

# Environment variables
TOKEN = os.getenv("AUTH_TOKEN")
MY_NUMBER = os.getenv("MY_PHONE_NUMBER")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Together API client
client = Together(api_key=TOGETHER_API_KEY)

class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="puch-client",
                scopes=["*"],
                expires_at=None,
            )
        return None

# MCP app
mcp = FastMCP(
    "RoastMaster",
    "Savage & Sarcastic comeback generator",
    auth=SimpleBearerAuthProvider(TOKEN)
)

@mcp.tool()
async def validate() -> str:
    """Required by Puch AI - returns phone number"""
    return MY_NUMBER  # Format: {country_code}{number}

@mcp.tool()
async def roast(style: str, message: str) -> str:
    """
    Generate a savage or sarcastic comeback.
    style: 'savage' or 'sarcastic'
    message: The input to roast
    """
    style = style.lower()
    if style not in ["savage", "sarcastic"]:
        return "Invalid style. Choose 'savage' or 'sarcastic'."

    prompt = f"""Someone said: "{message}"
    Your job: {"Respond with a brutally savage comeback" if style == "savage" else "Respond with sarcastic remark"}
    Only reply with the comeback, no commentary."""

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # Use 10000 for Render
    
    async def main():
        await mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port
        )
    
    asyncio.run(main())