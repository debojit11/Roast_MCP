import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from together import Together
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken

load_dotenv()  # Load .env variables

# Environment variables
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER")  # in {country_code}{number} format
AUTH_TOKEN = os.getenv("AUTH_TOKEN")  # For Puch AI authentication

# Together API client
client = Together(api_key=TOGETHER_API_KEY)

# --- Auth Provider ---
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
    auth=SimpleBearerAuthProvider(AUTH_TOKEN)  # ✅ Required for Puch AI
)

@mcp.tool()
def validate() -> str:
    """
    Required by Puch AI - returns your own number in {country_code}{number} format.
    """
    return MY_PHONE_NUMBER

@mcp.tool()
def roast(style: str, message: str) -> str:
    """
    Generate a savage or sarcastic comeback.
    style: 'savage' or 'sarcastic'
    message: The input message to roast.
    """
    style = style.lower()
    if style not in ["savage", "sarcastic"]:
        return "Invalid style. Choose 'savage' or 'sarcastic'."

    if style == "savage":
        tone_instructions = (
            "Respond with a brutally honest, witty, and confident comeback "
            "that will make the other person think twice before replying. "
            "No sugarcoating. Keep it short and punchy."
        )
    else:  # sarcastic
        tone_instructions = (
            "Respond with a dry, ironic, and clever remark dripping with sarcasm. "
            "Make it playful but sharp, like a sitcom burn."
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
    # ✅ Use Railway's PORT if available, otherwise default to 8086
    port = int(os.getenv("PORT", 8086))
    
    mcp.run_async(
        transport="streamable-http",
        host="0.0.0.0",
        port=port
    )