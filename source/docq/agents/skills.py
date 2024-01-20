"""Built-in skills for DocQ agents."""


from .datamodels import Skill


## For commercial use a license is required.
weather_skill = Skill(title="get_weather_openmeteo", file_name="get_weather_openmeteo.py", description="This skill get the weather for any city in any country in the world using Open Meteo API. A city or place is identified by a longitude and latitude.", content="")




https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m