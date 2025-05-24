import requests
import json
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple
from tool import tool


@tool
def get_current_datetime() -> dict:
    """
    Gets the current date and time in ISO format.
    
    Returns:
        dict: Current date and time information
    """
    now = datetime.now()
    return {
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "timestamp": now.timestamp()
    }

@tool
def get_current_year() -> Dict[str, int]:
    """
    Gets the current year.
    
    Returns:
        dict: Current year information
    """
    now = datetime.now()
    return {
        "year": now.year
    }

@tool
def get_current_month() -> Dict[str, str]:
    """
    Gets the current month as both number and name.
    
    Returns:
        dict: Current month information
    """
    now = datetime.now()
    return {
        "month_number": now.strftime("%m"),
        "month_name": now.strftime("%B")
    }



@tool
def calculate_date(base_date: str, days_offset: int) -> dict:
    """
    Calculates a new date by adding or subtracting days from a base date.
    
    Args:
        base_date: Base date in YYYY-MM-DD format (e.g., "2025-05-22")
        days_offset: Number of days to add (positive) or subtract (negative) (e.g., -3 for 3 days earlier)
        
    Returns:
        dict: Calculated date information
    """
    try:
        base = datetime.strptime(base_date, "%Y-%m-%d")
        target_date = base + timedelta(days=days_offset)
        
        return {
            "original_date": base_date,
            "days_offset": days_offset,
            "calculated_date": target_date.strftime("%Y-%m-%d"),
            "day_of_week": target_date.strftime("%A"),
            "success": True
        }
    except Exception as e:
        return {
            "original_date": base_date,
            "days_offset": days_offset,
            "calculated_date": None,
            "success": False,
            "error": f"Error calculating date: {str(e)}"
        }



@tool
def parse_date_time(query: str) -> dict:
    """
    Parses SIMPLE date and time references from natural language text, including partial dates with the current year.
    
    SUPPORTED PATTERNS:
    - Simple references: "today", "now", "current", "this moment", "tomorrow", "next day", "yesterday", "last day"
    - Week references: "this weekend", "saturday", "sunday", "last week", "next week"
    - Days ago: "X days ago" (e.g., "3 days ago")
    - Partial dates: "Month Day" (e.g., "May 1"), "Month Day–Day" (e.g., "May 1–3"), "Month Day to Day" (e.g., "May 1 to 3")
    - Time references: "morning", "afternoon", "evening", "night", "9 AM", "7 PM"
    
    NOT SUPPORTED: Complex date math, specific dates with years (e.g., "May 1, 2024"), arithmetic like "X days earlier"
    
    Args:
        query: Natural language date/time reference (e.g., "tomorrow", "May 1–3", "3 days ago")
        
    Returns:
        dict: Parsed date and time information with start_date, end_date, time_range
    """
    now = datetime.now()
    current_year = now.year
    result = {
        "start_date": None,
        "end_date": None,
        "time_range": None,
        "parsed_references": []
    }
    
    query_lower = query.lower().strip()
    
    # Partial date patterns (e.g., "May 1", "May 1–3", "May 1 to 3")
    month_names = r'(january|february|march|april|may|june|july|august|september|october|november|december)'
    partial_date_pattern = rf'{month_names}\s+(\d{{1,2}})(?:\s*[-–to]\s*(\d{{1,2}}))?'
    date_match = re.search(partial_date_pattern, query_lower, re.IGNORECASE)
    
    if date_match:
        month_str = date_match.group(1).capitalize()
        start_day = int(date_match.group(2))
        end_day = int(date_match.group(3)) if date_match.group(3) else start_day
        
        # Convert month name to number
        month_num = {
            "January": "01", "February": "02", "March": "03", "April": "04",
            "May": "05", "June": "06", "July": "07", "August": "08",
            "September": "09", "October": "10", "November": "11", "December": "12"
        }[month_str]
        
        # Format dates with current year
        result["start_date"] = f"{current_year}-{month_num}-{start_day:02d}"
        result["end_date"] = f"{current_year}-{month_num}-{end_day:02d}"
        result["parsed_references"].append(f"partial_date_{month_str}_{start_day}_{end_day}")
        return result
    
    # X days ago pattern (e.g., "3 days ago", "5 days ago")
    days_ago_match = re.search(r'(\d+)\s+days?\s+ago', query_lower)
    if days_ago_match:
        days_back = int(days_ago_match.group(1))
        target_date = now - timedelta(days=days_back)
        result["start_date"] = target_date.strftime("%Y-%m-%d")
        result["end_date"] = target_date.strftime("%Y-%m-%d")
        result["parsed_references"].append(f"{days_back}_days_ago")
        return result
    
    # Last week references
    if any(phrase in query_lower for phrase in ["last week", "previous week"]):
        last_week = now - timedelta(days=7)
        result["start_date"] = last_week.strftime("%Y-%m-%d")
        result["end_date"] = last_week.strftime("%Y-%m-%d")
        result["parsed_references"].append("last_week")
        return result
    
    # Today references
    if any(word in query_lower for word in ["today", "now", "current", "this moment"]):
        result["start_date"] = now.strftime("%Y-%m-%d")
        result["end_date"] = now.strftime("%Y-%m-%d")
        result["parsed_references"].append("today")
        return result
    
    # Tomorrow references
    if any(word in query_lower for word in ["tomorrow", "next day"]):
        tomorrow = now + timedelta(days=1)
        result["start_date"] = tomorrow.strftime("%Y-%m-%d")
        result["end_date"] = tomorrow.strftime("%Y-%m-%d")
        result["parsed_references"].append("tomorrow")
        return result
    
    # Yesterday references
    if any(word in query_lower for word in ["yesterday", "last day"]):
        yesterday = now - timedelta(days=1)
        result["start_date"] = yesterday.strftime("%Y-%m-%d")
        result["end_date"] = yesterday.strftime("%Y-%m-%d")
        result["parsed_references"].append("yesterday")
        return result
    
    # This week references
    if any(phrase in query_lower for phrase in ["this week", "weekend", "saturday", "sunday"]):
        days_ahead = 5 - now.weekday()  # Saturday is weekday 5
        if days_ahead <= 0:
            days_ahead += 7
        saturday = now + timedelta(days=days_ahead)
        sunday = saturday + timedelta(days=1)
        result["start_date"] = saturday.strftime("%Y-%m-%d")
        result["end_date"] = sunday.strftime("%Y-%m-%d")
        result["parsed_references"].append("weekend")
        return result
    
    # Time-specific references
    time_patterns = {
        "morning": ("06:00", "12:00"),
        "afternoon": ("12:00", "18:00"),
        "evening": ("18:00", "21:00"),
        "night": ("21:00", "06:00"),
        "dawn": ("05:00", "07:00"),
        "dusk": ("17:00", "19:00")
    }
    
    for time_word, (start_time, end_time) in time_patterns.items():
        if time_word in query_lower:
            result["time_range"] = {"start": start_time, "end": end_time}
            result["parsed_references"].append(f"{time_word}_time")
            break
    
    # Specific time mentions (e.g., "9 AM", "7 PM")
    time_match = re.search(r'(\d{1,2})\s*(am|pm|AM|PM)', query)
    if time_match:
        hour = int(time_match.group(1))
        period = time_match.group(2).lower()
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        result["time_range"] = {"specific_hour": f"{hour:02d}:00"}
        result["parsed_references"].append(f"specific_time_{hour}")
    
    # If no specific date found, default to today
    if not result["start_date"]:
        result["start_date"] = now.strftime("%Y-%m-%d")
        result["end_date"] = now.strftime("%Y-%m-%d")
        result["parsed_references"].append("default_today")
    
    return result



@tool
def get_location_coordinates(location: str) -> dict:
    """
    Gets latitude and longitude coordinates for a given location using Open-Meteo geocoding API.
    
    Args:
        location: Location name (city, address, etc.)
        
    Returns:
        dict: Location coordinates and details
    """
    try:
        # Open-Meteo Geocoding API
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("results") and len(data["results"]) > 0:
            result = data["results"][0]
            return {
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "name": result["name"],
                "country": result.get("country", ""),
                "admin1": result.get("admin1", ""),
                "timezone": result.get("timezone", "UTC"),
                "found": True
            }
        else:
            return {
                "latitude": None,
                "longitude": None,
                "name": location,
                "found": False,
                "error": f"Location '{location}' not found"
            }
    except Exception as e:
        return {
            "latitude": None,
            "longitude": None,
            "name": location,
            "found": False,
            "error": f"Error geocoding location: {str(e)}"
        }


@tool
def get_current_location_from_ip() -> dict:
    """
    Gets the current location based on IP address using Geoapify IP info API.
    
    Returns:
        dict: Current location information
    """
    try:
        api_key = "ca7a3406ddf741af8d6a49d9aa2835f5"
        url = f"https://api.geoapify.com/v1/ipinfo?apiKey={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        return {
            "latitude": data.get("location", {}).get("latitude"),
            "longitude": data.get("location", {}).get("longitude"),
            "city": data.get("city", {}).get("name", "Unknown"),
            "country": data.get("country", {}).get("name", "Unknown"),
            "region": data.get("state", {}).get("name", "Unknown"),
            "timezone": data.get("timezone", {}).get("name", "Unknown"),
            "found": True
        }

    except Exception as e:
        # Fallback to Dhaka, Bangladesh coordinates
        return {
            "latitude": 23.8103,
            "longitude": 90.4125,
            "city": "Dhaka",
            "country": "Bangladesh",
            "region": "Dhaka Division",
            "timezone": "Asia/Dhaka",
            "found": False,
            "error": f"Using default location (Dhaka): {str(e)}"
        }

@tool
def get_weather_forecast(latitude: float, longitude: float, start_date: str, end_date: str, variables: str, timezone: str = "auto") -> dict:
    """
    Gets weather forecast data from Open-Meteo API.
    **IMPORTANT**: You must use that current year if not provided in the user query.
    
    Args:
        latitude: Latitude coordinate (e.g., 23.8103 for Dhaka)
        longitude: Longitude coordinate (e.g., 90.4125 for Dhaka)
        start_date: Start date in YYYY-MM-DD format (e.g., "2025-05-22")
        end_date: End date in YYYY-MM-DD format (e.g., "2025-05-25")
        variables: Comma-separated weather variables to retrieve. Choose from:
                  DAILY: temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,wind_speed_10m_max,sunrise,sunset
                  HOURLY: temperature_2m,precipitation_probability,weather_code,wind_speed_10m,relative_humidity_2m
                  CURRENT: temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m,precipitation_probability
                  Example: "temperature_2m,weather_code,precipitation_probability"
        timezone: Timezone (default: "auto" - uses location timezone)
        
    Returns:
        dict: Weather forecast data with success status and weather information
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        
        # Parse variables into categories
        var_dict = _parse_weather_variables(variables)
        
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone
        }
        
        # Add variable categories to params
        if var_dict["daily"]:
            params["daily"] = ",".join(var_dict["daily"])
        if var_dict["hourly"]:
            params["hourly"] = ",".join(var_dict["hourly"])
        if var_dict["current"]:
            params["current"] = ",".join(var_dict["current"])
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "data": data,
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching weather forecast: {str(e)}",
            "data": None
        }


@tool
def get_historical_weather(latitude: float, longitude: float, start_date: str, end_date: str, variables: str, timezone: str = "GMT") -> dict:
    """
    Gets historical weather data from Open-Meteo Archive API.
    
    Args:
        latitude: Latitude coordinate (e.g., 23.8103 for Dhaka)
        longitude: Longitude coordinate (e.g., 90.4125 for Dhaka)
        start_date: Start date in YYYY-MM-DD format (e.g., "2025-05-20")
        end_date: End date in YYYY-MM-DD format (e.g., "2025-05-21") 
        variables: Comma-separated weather variables to retrieve. Choose from:
                  DAILY: temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,weather_code,wind_speed_10m_max
                  HOURLY: temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,cloud_cover
                  Example: "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code"
        timezone: Timezone (default: "auto" - uses location timezone)
        
    Returns:
        dict: Historical weather data with success status and weather information
    """
    try:
        url = "https://archive-api.open-meteo.com/v1/archive"
        
        # Parse variables into categories (no current for historical)
        var_dict = _parse_weather_variables(variables)
        
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone
        }
        
        # Add variable categories to params
        if var_dict["daily"]:
            params["daily"] = ",".join(var_dict["daily"])
        if var_dict["hourly"]:
            params["hourly"] = ",".join(var_dict["hourly"])
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": True,
            "data": data,
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching historical weather: {str(e)}",
            "data": None
        }


def _parse_weather_variables(variables: str) -> dict:
    """Helper function to parse weather variables into categories."""
    
    # Common weather variables categorized
    daily_vars = [
        "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
        "sunrise", "sunset", "daylight_duration", "sunshine_duration",
        "precipitation_sum", "rain_sum", "snowfall_sum", "precipitation_hours",
        "precipitation_probability_max", "wind_speed_10m_max", "wind_gusts_10m_max",
        "wind_direction_10m_dominant", "weather_code"
    ]
    
    hourly_vars = [
        "temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
        "precipitation_probability", "precipitation", "rain", "showers", "snowfall",
        "snow_depth", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
        "weather_code", "cloud_cover", "surface_pressure"
    ]
    
    current_vars = [
        "temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day",
        "precipitation", "rain", "showers", "snowfall", "wind_speed_10m",
        "wind_direction_10m", "wind_gusts_10m", "weather_code"
    ]
    
    # Parse the input variables
    var_list = [v.strip() for v in variables.split(",")]
    
    result = {"daily": [], "hourly": [], "current": []}
    
    for var in var_list:
        if var in daily_vars:
            result["daily"].append(var)
        if var in hourly_vars:
            result["hourly"].append(var)
        if var in current_vars:
            result["current"].append(var)
    
    # If no specific variables provided, use defaults
    if not any(result.values()):
        result["daily"] = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "weather_code"]
        result["hourly"] = ["temperature_2m", "precipitation_probability", "weather_code"]
        result["current"] = ["temperature_2m", "weather_code", "wind_speed_10m"]
    
    return result