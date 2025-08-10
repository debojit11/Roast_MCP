import asyncio
import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastmcp import FastMCP
from together import Together
from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair
from mcp.server.auth.provider import AccessToken

load_dotenv()

client = Together()

# Environment variables
TOKEN = os.getenv("AUTH_TOKEN")
MY_NUMBER = os.getenv("MY_PHONE_NUMBER")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Generate RSA key pair for JWT verification
key_pair = RSAKeyPair.generate()

class SimpleAuthProvider(JWTVerifier):
    def __init__(self, token: str):
        super().__init__(
            public_key=key_pair.public_key,
            issuer="roast-master",
            audience="puch-ai"
        )
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
    auth=SimpleAuthProvider(TOKEN)
)

# Add CORS middleware
@mcp.on_startup
async def setup_cors():
    mcp.app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"]
    )

@mcp.tool()
async def validate() -> str:
    """Required by Puch AI"""
    return MY_NUMBER  # Must be in {country_code}{number} format

@mcp.tool()
async def roast(style: str, message: str) -> str:
    """Generate savage/sarcastic comebacks"""
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
    port = int(os.getenv("PORT", 10000))  # Must use 10000 for Render
    
    async def main():
        await mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port
        )
    
    asyncio.run(main())