"""Built-in skills for DocQ agents."""

import os
from typing import List

from .datamodels import Skill

## For commercial use a license is required.
weather_skill = Skill(title="get_weather_openmeteo", file_name="get_weather_openmeteo.py", description="This skill get the weather for any city in any country in the world using Open Meteo API. A city or place is identified by a longitude and latitude.", content="""import requests\n
import json\n
def meteo_weather(latitude:str, longitude: str) -> dict:\n
  url = "https://api.open-meteo.com/v1/forecast"\n
  params = {\n
      "latitude": latitude,\n
      "longitude": longitude,\n
      "current_weather": True,\n
  }\n
  response = requests.get(url, params=params)\n
  if response.status_code == 200:\n
      data = json.loads(response.text)\n
        # Sample of json response to expect:
        #{
        # current_weather: {
        # time: "2023-12-27T16:15",
        # interval: 900,
        # temperature: 11.9,
        # windspeed: 27.1,
        # winddirection: 203,
        # is_day: 0,
        # weathercode: 61
        # },
        # current_weather: {
        # time: "2023-12-27T16:15",
        # interval: 900,
        # temperature: 11.9,
        # windspeed: 27.1,
        # winddirection: 203,
        # is_day: 0,
        # weathercode: 61
        # }
        #}
      return data\n

  else:\n
      return {"error": "An error occurred while getting the weather data."}"""
)




skills = [weather_skill]



def generate_prompt_from_skills(skills: List[Skill]) -> str:
    """Get prompt from skill."""
    instruction = """

    While solving the task you may use functions below which will be available in a file called skills.py .
    To use a function from skill.py in code, IMPORT THE FUNCTION FROM skills.py  and then use the function.
    If you need to install python packages, write shell code to
    install via pip and use --quiet option.

            """

    prompt = ""  # filename:  skills.py
    for skill in skills:
        prompt += f"""

##### Begin of {skill.title} #####

{skill.content}

#### End of {skill.title} ####

"""

    return instruction + prompt

def generate_skills_python_file(skills: List[Skill], scratch_dir: str) -> None:
    """Generate skills file."""
    prompt = ""  # filename:  skills.py
    for skill in skills:
        prompt += f"""

##### Begin of {skill.title} #####

{skill.content}

#### End of {skill.title} ####

"""
    with open(os.path.join(scratch_dir,"skills.py"), "w") as f:
        f.write(prompt)


