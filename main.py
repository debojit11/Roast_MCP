import asyncio
import os
from fastapi.middleware.cors import CORSMiddleware  # Add this import
from dotenv import load_dotenv
from fastmcp import FastMCP
from together import Together
from fastmcp.server.auth.providers.jwt import JWTVerifier  # Updated import
from mcp.server.auth.provider import AccessToken

load_dotenv()

client = Together()

TOKEN = os.getenv("AUTH_TOKEN")  # Make sure this matches .env
MY_NUMBER = os.getenv("MY_PHONE_NUMBER")  # Format: 917636086117 (no +)

# Updated auth provider
class SimpleAuthProvider(JWTVerifier):
    def __init__(self, token: str):
        super().__init__(issuer="roast-master")
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
    """Must return only the phone number string"""
    return MY_NUMBER  # Example: "917636086117"

@mcp.tool()
async def roast(style: str, message: str) -> str:
    """
    Generate a savage or sarcastic comeback.
    style: 'savage' or 'sarcastic'
    message: The input message to roast.
    """
    style = style.lower()
    if style not in ["savage", "sarcastic"]:
        return "Invalid style. Choose 'savage' or 'sarcastic'."

    tone_instructions = (
        "Respond with a brutally savage and unapologetically harsh comeback. "
        "Make it sting and cut deep. No niceties, no sugarcoating. Short, sharp, and savage."
        if style == "savage" else
        "Respond with a dry, ironic, and clever remark dripping with sarcasm. "
        "Make it playful but sharp, like a twitter burn."
    )

    prompt = f"""
    Someone said: "{message}"
    Your job: {tone_instructions}
    Only reply with the comeback, no extra commentary.
    """

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))

    async def main():
        await mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port
        )

    asyncio.run(main())