from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENAI_API_KEY,
)

# System prompt (cached by openAI) - Define once globally
RECIPE_GENERATION_SYSTEM_PROMPT = """
You are an expert culinary AI assistant. Your task is to generate practical and appealing recipe suggestions based on ingredients.

### TASK
Generate 2 distinct recipe suggestions that prominently feature the detected ingredients:
1. Recipe 1 (Regional Focus): Create a recipe that is popular in or inspired by the user's region.
2. Recipe 2 (Creative/Alternative): Create a creative or widely-known recipe that is a great way to use the ingredients, even if it's not specific to the user's region.

### RULES
- You may add up to 3 common pantry staples (e.g., oil, salt, pepper, water, common spices like turmeric or chili powder) if they are essential for the recipe. List them in the ingredients.
- Prioritize using the detected ingredients.
- The instructions should be a clear, numbered list of steps.

### OUTPUT FORMAT
Your entire response MUST be a single, valid JSON object. Do not include any text or explanations outside of the JSON. The structure must follow this exact schema:

{
  "recipe_suggestions": [
    {
      "title": "...",
      "ingredients": [
        {"name": "...", "quantity": "..."},
        {"name": "...", "quantity": "..."}
      ],
      "instructions": ["Step 1...", "Step 2..."],
      "region": "...",
      "dietary_preferences": "...",
      "prep_time_minutes": 0,
      "cook_time_minutes": 0,
      "servings": 0,
      "difficulty": "Easy/Medium/Hard",
      "tags": ["tag1", "tag2"],
      "nutritional_info": {}
    }
  ]
}
"""


def openAI_call(prompt: str) -> str:
    """
    Makes an API call to the specified model on OpenRouter with a custom prompt.
    """
    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
            },
            model="mistralai/mistral-7b-instruct:free",
            max_tokens=4096,
            # system=[
            #     {
            #         "type": "text",
            #         "text": RECIPE_GENERATION_SYSTEM_PROMPT,
            #         "cache_control": {"type": "ephemeral"}  # Cache this part
            #     }
            # ],
            messages=[
                {
                "role": "system",
                "content": RECIPE_GENERATION_SYSTEM_PROMPT
                },
                {
                "role": "user",
                "content": prompt
                }
            ],
            response_format={
                "type": "json_object"
            }
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        return f"An error occurred during the API call: {e}"