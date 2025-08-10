import asyncio
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from together import Together
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken

load_dotenv()

# Environment variables - renamed to match starter code
TOKEN = os.getenv("AUTH_TOKEN")  # Changed from AUTH_TOKEN
MY_NUMBER = os.getenv("MY_PHONE_NUMBER")  # Changed from MY_PHONE_NUMBER
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
    auth=SimpleBearerAuthProvider(TOKEN)  # Use TOKEN instead of AUTH_TOKEN
)

# Updated validate endpoint to match starter code
@mcp.tool()
async def validate() -> str:  # Removed token parameter
    """Required by Puch AI - returns phone number"""
    return MY_NUMBER  # Direct return without validation

@mcp.tool()
async def roast(*, style: str, message: str) -> str:
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
    port = int(os.getenv("PORT", 8086))

    async def main():
        await mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port
        )

    asyncio.run(main())