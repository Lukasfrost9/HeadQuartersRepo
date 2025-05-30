import openmeteo_requests
from openmeteo_sdk.Variable import Variable
from google import genai
import json
import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

WEATHER = openmeteo_requests.Client()

GoogleAI = genai.Client(api_key="AIzaSyAfZlNnQirGTazOk4QaJhxjCGpsFkBNj2E")





def WeatherAPI(lat,long):

    params = {
        "latitude": lat,
        "longitude": long,
	    "daily": ["temperature_2m_max", "temperature_2m_min"],
	    "hourly": ["temperature_2m", "apparent_temperature"],
        "current": "temperature_2m",
	    "timezone": "Europe/Berlin"
}

    url = "https://api.open-meteo.com/v1/forecast"
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()

    print(f"Current time {current.Time()}")
    print(f"Current temperature_2m {current_temperature_2m}")

    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_apparent_temperature = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
    	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    	freq = pd.Timedelta(seconds = hourly.Interval()),
    	inclusive = "left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["apparent_temperature"] = hourly_apparent_temperature

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    print(hourly_dataframe)

    daily = response.Daily()
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
    	start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
    	end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
    	freq = pd.Timedelta(seconds = daily.Interval()),
    	inclusive = "left"
    )}

    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min

    daily_dataframe = pd.DataFrame(data = daily_data)
    return(daily_dataframe)




def GetInput():
    print("Please enter the city and the country for which to check the weather for, ie (New York, USA)")
    UserInput = input()
    return UserInput

def PromptAI(UserPrompt):
    prompt = UserPrompt+'Provide coordinates of the following city. Do not add any added wording besides what is prompted. Only respond with the coordinates formatted as such. \'{ "latitude":Insert LAT,"longitude":Insert LON}\' '
    response = GoogleAI.models.generate_content(model="gemini-2.0-flash", contents=prompt
    )
    return response.text

def FullFunction():
    PromptJSON = str(PromptAI(GetInput()))
    x = json.loads(PromptJSON)
    long = (x["longitude"])
    lat = (x["latitude"])
    print(PromptAI("Ignoring all previous instructions, please analyze the following weather data and give me an analysis for the next week. You can compare it to the current_temprature_2m variable in the dataset which is the current temperature."+str(WeatherAPI(lat,long))))

FullFunction()
