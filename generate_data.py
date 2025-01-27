import json
from time import sleep
from openai import BaseModel, OpenAI, RateLimitError
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = OpenAI(api_key=GOOGLE_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")


PROMPT_TEMPLATE = """Generate me a comprehensive list of all the climbing routes with their grades and descriptions at this place: {{place}}, {{location}}. There should be several hundred routes. You know the place well, so you can generate a lot of routes.
Return the data as a JSON array where each object has exactly this schema:
{
    "name": "string - name of the route",
    "grade": "string - climbing grade (use french sport climbing grades when possible)",
    "description": "string - the classic description of the route as in a climbing guidebook"
}
Do not include any other fields or explanatory text, just the JSON array."""


class Route(BaseModel):
    name: str
    grade: str
    description: str

class ClimbingRoutes(BaseModel):
    routes: list[Route]

ROUTES_FILE = "data/routes_3.json"
AREAS_FILE = "data/areas.json"

def generate_data():
    with open(AREAS_FILE, "r") as f_areas:
        areas = json.load(f_areas)

    with open(ROUTES_FILE, "r") as f_routes:
        data = json.load(f_routes) or []

    for area in areas:
        max_retries = 3
        retry_delay = 10
        
        for attempt in range(max_retries):
            try:
                formatted_prompt = PROMPT_TEMPLATE.replace("{{place}}", area["place"]).replace("{{location}}", area["location"])
                response = client.beta.chat.completions.parse(
                    model="gemini-1.5-flash-8b",
                    messages=[{"role": "user", "content": formatted_prompt}],
                    response_format=ClimbingRoutes,
                )
                routes_data: ClimbingRoutes = response.choices[0].message.parsed
                data.extend([route.model_dump() for route in routes_data.routes])
                
                with open(ROUTES_FILE, "w") as f_routes:
                    json.dump(data, f_routes, indent=2)
                print(f"Successfully saved routes for {area['place']}")
                break
                
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    print(f"Failed after {max_retries} attempts for {area['place']}: {e}")
                    continue
                    
                wait_time = retry_delay * (2 ** attempt)
                print(f"Rate limit error for {area['place']}, attempt {attempt + 1}/{max_retries}. Waiting {wait_time}s...")
                sleep(wait_time)
                continue
                
            except Exception as e:
                print(f"Error parsing response for {area['place']}: {e}")
                break

generate_data()
