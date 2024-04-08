"""Weather Plugin."""
from datetime import datetime
from typing import Self

import requests
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter


class WeatherPlugin:
    """A plugin to get the weather for a location using OpenMeteo APIs, e.g. get the current temperature, wind speed etc. for in a given location."""

    __open_meteo_api_url = "https://api.open-meteo.com/v1/forecast"

    @sk_function(
        description="Get the current weather in a location. Response contains the current temperature, wind speed, humidity, and more.",
        name="get_current_weather_for_location",
    )
    @sk_function_context_parameter(
        name="latitude", description="The latitude of the location", default_value=""
    )
    @sk_function_context_parameter(
        name="longitude", description="The longitude of the location", default_value=""
    )
    def get_current_weather_for_location(self: Self, context: SKContext) -> str:
        try:
            if context["latitude"] == "":
                raise ValueError("arg 'latitude' was empty.")

            if context["longitude"] == "":
                raise ValueError("arg 'longitude' was empty.")

            params = {
                "latitude": context["latitude"],
                "longitude": context["longitude"],
                "current_weather": True,
            }

            result = self._call_meteo_api(params)
        except Exception as e:
            result = f"error: {e}"

        return result

    @sk_function(
        description="Get the weather forecast for a location for a given time period. The response contains the temperature, wind speed, humidity, and more.",
        name="get_future_weather_for_location",
    )
    @sk_function_context_parameter(
        name="latitude", description="The latitude of the location", default_value=""
    )
    @sk_function_context_parameter(
        name="longitude", description="The longitude of the location", default_value=""
    )
    @sk_function_context_parameter(
        name="start_date",
        description="The start date of the forecast in the format YYYY-MM-DD",
        default_value="",
    )
    @sk_function_context_parameter(
        name="end_date",
        description="The end date of the forecast in the format YYYY-MM-DD",
        default_value="",
    )
    def get_future_weather_for_location(self: Self, context: SKContext) -> str:
        """Get the weather forecast for a location for a given time period. Reponse containers the temperature, wind speed, humidity, and more."""
        result = ""
        def validate_date(date_string):
            try:
                datetime.strptime(date_string, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Incorrect data format, should be YYYY-MM-DD") from e

        try:
            if context["latitude"] == "":
                raise ValueError("arg 'latitude' was empty.")

            if context["longitude"] == "":
                raise ValueError("arg 'longitude' was empty.")

            validate_date(context["start_date"])
            validate_date(context["end_date"])


            params = {
                "latitude": context["latitude"],
                "longitude": context["longitude"],
                "start_date": context["start_date"],
                "end_date": context["end_date"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,daylight_duration,sunshine_duration,precipitation_sum,rain_sum,showers_sum,snowfall_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max"
            }

            result = self._call_meteo_api(params)
        except Exception as e:
            result = f"error: {e}"

        return result

    def _call_meteo_api(self: Self, params: dict) -> str:
        response = requests.get(self.__open_meteo_api_url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.text
        else:
            data = "error: An error occurred while getting the weather data for the OpenMeteo API."

        return data

    @sk_function(
        description="Get the weather code descriptions for the WMO weather codes.",
        name="wmo_weather_code_descriptions",
    )
    def wmo_weather_code_descriptions(self: Self, context: SKContext) -> str:
        """Get the weather code descriptions for the WMO weather codes."""
        data = """
        code  description
        0  Clear sky
        1  Mainly clear
        2  partly cloudy
        3  overcast
        45  Fog
        48  depositing rime fog
        51  Drizzle: light intensity
        53  Drizzle: moderate intensity
        55  Drizzle: dense intensity
        56  Freezing Drizzle: light intensity
        57	Freezing Drizzle: dense intensity
        61  Rain: Slight intensity 
        63  Rain: moderate intensity
        65	Rain: heavy intensity
        66  Freezing Rain: Light intensity
        67	Freezing Rain: heavy intensity
        71  Snow fall: Slight intensity
        73  Snow fall: moderate intensity
        75	Snow fall: heavy intensity
        77	Snow grains
        80	Rain showers: Slight
        81	Rain showers: moderate
        82	Rain showers: violent
        85  Snow showers slight
        86	Snow showers heavy
        95 *  Thunderstorm: Slight or moderate
        96 *  Thunderstorm with slight hail
        99 *  Thunderstorm with heavy hail
        (*) Thunderstorm forecast with hail is only available in Central Europe
        """

        return data

