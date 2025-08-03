# backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from dotenv import load_dotenv # Import load_dotenv
from datetime import datetime # Import datetime to get current year
from serpapi import GoogleSearch # Import GoogleSearch from serpapi library

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Enable CORS for all origins, allowing your frontend to connect
CORS(app)

# Function to clean markdown characters from the text
def clean_markdown(text):
    """
    Removes common Markdown formatting characters from a given string.
    """
    if not isinstance(text, str): # Ensure input is a string
        return text
    text = text.replace('***', '').replace('**', '').replace('*', '') # Bold/italic
    text = text.replace('##', '').replace('#', '') # Headings
    text = text.replace('- ', '') # List item markers
    text = ' '.join(text.split()).strip() # Replace multiple spaces with single space and trim
    return text

@app.route('/generate_plan', methods=['POST'])
def generate_plan():
    """
    Receives detailed travel information, calls the Gemini API to generate a travel plan,
    cleans the markdown, and returns the plan.
    """
    data = request.get_json()

    # Extract all new and existing parameters
    origin = data.get('origin')
    destination = data.get('destination')
    cities_to_visit = data.get('cities_to_visit')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    budget = data.get('budget')
    num_adults = data.get('num_adults')
    num_children = data.get('num_children')
    children_ages = data.get('children_ages')
    food_preference = data.get('food_preference')
    hotel_preference = data.get('hotel_preference')
    additional_services = data.get('additional_services', []) # Default to empty list if not provided
    travel_method = data.get('travel_method') # New parameter
    flight_class = data.get('flight_class') # New parameter
    cruise_details = data.get('cruise_details') # New parameter for cruise trips
    current_currency_rate = data.get('current_currency_rate') # Live currency rate from frontend

    # Basic validation for essential fields
    if not all([origin, destination, start_date, end_date, budget, num_adults]):
        return jsonify({"error": "Missing essential travel details (origin, destination, dates, budget, number of adults)."}), 400

    # Construct a highly detailed prompt for the Gemini API
    prompt = f"Create a comprehensive and engaging travel plan for a trip from {origin} to {destination}."
    prompt += f" The trip is planned from {start_date} to {end_date}."
    prompt += f" The approximate budget for the entire trip is {budget}."
    prompt += f" There will be {num_adults} adult travelers."

    if num_children and int(num_children) > 0:
        prompt += f" And {num_children} children, with ages: {children_ages}."
        prompt += " Please ensure all suggestions are kid-friendly."
    else:
        prompt += " No children are included in this trip."

    if cities_to_visit:
        prompt += f" The cities/areas to visit within the destination include: {cities_to_visit}."

    if food_preference:
        prompt += f" The travelers prefer food options like: {food_preference}."

    if hotel_preference:
        prompt += f" For accommodation, suggest hotels that are {hotel_preference}."

    if travel_method:
        prompt += f" The preferred method of travel is {travel_method}."
        if travel_method.lower() == 'flight' and flight_class:
            prompt += f" Preferred flight class: {flight_class}."
        elif travel_method.lower() == 'cruise' and cruise_details:
            prompt += f" With cruise details: {cruise_details}."

    if additional_services:
        services_str = ", ".join(additional_services)
        prompt += f" Additionally, please include information or suggestions regarding: {services_str}."

    # Instruct Gemini to use the provided rate and avoid adding dates
    if current_currency_rate:
        prompt += f" For currency conversion tips, use this exact rate: '{current_currency_rate}'. Do NOT add any 'as of' dates or specific dates to the currency conversion tip, just state the rate as provided."


    prompt += " The plan should cover daily activities, recommended hotels close to tourist places, specific food recommendations (including restaurants if possible), approximate local taxi costs, currency conversion tips, and any other relevant factors like local customs, safety advice, or best travel tips for the specified dates."
    prompt += " Structure the output as a JSON object. The JSON should have a 'general_info' object and a 'days' array."
    prompt += " The 'general_info' object should contain 'currency_conversion', 'travel_insurance_tips', 'approx_taxi_costs', and 'other_tips' (e.g., local customs, safety, best time to visit)."
    prompt += " The 'days' array should contain objects, each with 'day_number' (integer), 'title' (e.g., 'Arrival in Bali & Kuta Exploration'), 'activities' (array of strings), 'accommodation' (string), and 'food' (string)."
    prompt += " Ensure all string values within the JSON are plain text, without markdown characters."


    chat_history = [{"role": "user", "parts": [{"text": prompt}]}]
    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "general_info": {
                        "type": "OBJECT",
                        "properties": {
                            "currency_conversion": {"type": "STRING"},
                            "travel_insurance_tips": {"type": "STRING"},
                            "approx_taxi_costs": {"type": "STRING"},
                            "other_tips": {"type": "STRING"}
                        }
                    },
                    "days": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "day_number": {"type": "NUMBER"},
                                "title": {"type": "STRING"},
                                "activities": {
                                    "type": "ARRAY",
                                    "items": {"type": "STRING"}
                                },
                                "accommodation": {"type": "STRING"},
                                "food": {"type": "STRING"}
                            },
                            "required": ["day_number", "title", "activities", "accommodation", "food"]
                        }
                    }
                },
                "required": ["general_info", "days"]
            }
        }
    }

    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not set. Please ensure it's in your .env file or set in your environment.")

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()

        if result.get('candidates') and len(result['candidates']) > 0 and \
           result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts') and \
           len(result['candidates'][0]['content']['parts']) > 0:
            # Gemini returns JSON string, parse it
            json_response_str = result['candidates'][0]['content']['parts'][0]['text']
            parsed_plan = json.loads(json_response_str)

            # Apply clean_markdown to all string values in the parsed JSON
            # This is a recursive function to clean nested structures
            def recursive_clean(obj):
                if isinstance(obj, dict):
                    return {k: recursive_clean(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [recursive_clean(elem) for elem in obj]
                elif isinstance(obj, str):
                    return clean_markdown(obj)
                else:
                    return obj

            cleaned_parsed_plan = recursive_clean(parsed_plan)

            # Return the structured and cleaned JSON
            return jsonify({"plan": cleaned_parsed_plan}), 200
        else:
            return jsonify({"error": "Failed to generate structured plan from AI model or no candidates found."}), 500

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return jsonify({"error": f"Network or API error: {str(e)}"}), 500
    except json.JSONDecodeError as e:
        print(f"JSON decoding error from Gemini response: {e}")
        print(f"Raw Gemini response: {result}")
        return jsonify({"error": "Invalid JSON response from Gemini API. Check Gemini's output format."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

@app.route('/search_flights', methods=['POST'])
def search_flights():
    """
    Searches for flights using SerpAPI based on provided details.
    Requires IATA codes for origin and destination and YYYY-MM-DD dates.
    """
    data = request.get_json()
    origin_iata = data.get('origin_iata') # Expecting IATA code
    destination_iata = data.get('destination_iata') # Expecting IATA code
    outbound_date = data.get('outbound_date') # Expecting YYYY-MM-DD
    return_date = data.get('return_date') # Expecting YYYY-MM-DD
    currency = data.get('currency', 'USD') # Get currency, default to USD

    if not all([origin_iata, destination_iata, outbound_date, return_date]):
        return jsonify({"error": "Missing flight search details (origin IATA, destination IATA, outbound_date, return_date)."}), 400

    serpapi_api_key = os.getenv("SERPAPI_API_KEY", "xyz") # Use 'xyz' as placeholder if not set

    if serpapi_api_key == "xyz":
        print("Warning: SERPAPI_API_KEY environment variable not set. Flight search will not work.")
        return jsonify({"error": "SerpAPI key not configured on the backend."}), 500


    # SerpAPI Google Flights parameters - using GoogleSearch client library
    params = {
        "engine": "google_flights",
        "departure_id": origin_iata,
        "arrival_id": destination_iata,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": currency,
        "hl": "en",
        "api_key": serpapi_api_key
    }

    try:
        # Using the serpapi Python client library for GET request
        search = GoogleSearch(params)
        results = search.get_dict() # This performs the GET request

        # Extracting the cheapest flight
        cheapest_flight = None
        if 'best_flights' in results and results['best_flights']:
            cheapest_flight = results['best_flights'][0] # Assuming the first one is often the best/cheapest
        elif 'other_flights' in results and results['other_flights']:
            # If best_flights isn't available, look at other_flights and try to find the cheapest
            cheapest_flight = min(results['other_flights'], key=lambda x: x.get('price', float('inf')))

        if cheapest_flight:
            # Robust extraction with default values and formatting
            departure_airport_name = cheapest_flight.get('departure_airport', {}).get('name', origin_iata)
            arrival_airport_name = cheapest_flight.get('arrival_airport', {}).get('name', destination_iata)
            
            # Format total_duration from minutes to Hh Mmin
            total_duration_minutes = cheapest_flight.get('total_duration')
            if isinstance(total_duration_minutes, (int, float)):
                hours = total_duration_minutes // 60
                minutes = total_duration_minutes % 60
                total_duration_formatted = f"{hours}h {minutes}min"
            else:
                total_duration_formatted = 'N/A'

            # Price extraction: check for 'price' and 'price_currency' or just 'price'
            price_raw = cheapest_flight.get('price')
            price_currency_symbol = cheapest_flight.get('price_currency', currency) # Use response currency or requested currency
            
            price_formatted = 'N/A'
            if price_raw is not None:
                price_formatted = f"{price_currency_symbol} {price_raw} (per person)" # Added "per person"
            
            # Airline name extraction: check 'airline' directly, then 'flights' if available
            airline_name = cheapest_flight.get('airline_name')
            if not airline_name and cheapest_flight.get('flights') and cheapest_flight['flights'][0].get('airline'):
                airline_name = cheapest_flight['flights'][0]['airline']
            if not airline_name:
                airline_name = 'N/A' # Final fallback

            # Extract stops from extensions
            stops = "Direct"
            extensions = cheapest_flight.get('extensions', [])
            for ext in extensions:
                if "stop" in ext.lower(): # Check for 'stop' in lowercased extension
                    stops = ext
                    break

            flight_details = {
                "departure_airport": departure_airport_name,
                "arrival_airport": arrival_airport_name,
                "total_duration": total_duration_formatted, # Formatted duration
                "price": price_formatted, # Formatted price with currency
                "airline": airline_name,
                "stops": stops
            }
            return jsonify({"status": "success", "flight": flight_details}), 200
        else:
            return jsonify({"status": "no_flights", "message": "Could not find flight information for the given criteria."}), 404

    except Exception as e:
        print(f"SerpAPI client error: {e}")
        return jsonify({"error": f"An error occurred during flight search: {str(e)}"}), 500

@app.route('/suggest_travel_methods', methods=['POST'])
def suggest_travel_methods():
    """
    Uses Gemini to intelligently suggest travel methods (flight, cruise, train, car)
    based on origin and destination.
    """
    data = request.get_json()
    origin = data.get('origin')
    destination = data.get('destination')

    if not all([origin, destination]):
        return jsonify({"error": "Missing origin or destination for travel method suggestion."}), 400

    # Prompt Gemini to determine appropriate travel methods
    prompt = f"Given a trip from {origin} to {destination}, what are the most common and logical methods of travel? Consider if it's international, domestic, or coastal. Respond with a comma-separated list of methods (e.g., 'flight, train, car' or 'flight, cruise')."

    chat_history = [{"role": "user", "parts": [{"text": prompt}]}]
    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "methods": {
                        "type": "ARRAY",
                        "items": { "type": "STRING" }
                    }
                }
            }
        }
    }

    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not set. Travel method suggestion will not work.")
        return jsonify({"error": "Gemini API key not configured for travel method suggestion."}), 500

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if result.get('candidates') and len(result['candidates']) > 0 and \
           result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts') and \
           len(result['candidates'][0]['content']['parts']) > 0:
            # Gemini returns JSON string, parse it
            json_response_str = result['candidates'][0]['content']['parts'][0]['text']
            parsed_response = json.loads(json_response_str)
            suggested_methods = parsed_response.get('methods', [])
            return jsonify({"status": "success", "suggested_methods": suggested_methods}), 200
        else:
            return jsonify({"status": "failed", "message": "Could not suggest travel methods."}), 500

    except requests.exceptions.RequestException as e:
        print(f"Gemini API error for travel method suggestion: {e}")
        return jsonify({"error": f"Network or API error for method suggestion: {str(e)}"}), 500
    except json.JSONDecodeError as e:
        print(f"JSON decoding error from Gemini response: {e}")
        print(f"Raw Gemini response: {result}")
        return jsonify({"error": "Invalid JSON response from Gemini API."}), 500
    except Exception as e:
        print(f"An unexpected error occurred during method suggestion: {e}")
        return jsonify({"error": f"An internal server error occurred for method suggestion: {str(e)}"}), 500

@app.route('/get_iata_code', methods=['POST'])
def get_iata_code():
    """
    Uses Gemini to get the 3-letter IATA airport code for a given city name.
    """
    data = request.get_json()
    city_name = data.get('city_name')

    if not city_name:
        return jsonify({"error": "Missing city_name for IATA code lookup."}), 400

    prompt = f"What is the 3-letter IATA airport code for '{city_name}'? Respond with only the 3-letter code (e.g., 'BOM', 'LAX', 'DPS'). If no specific airport code is commonly associated, respond with 'N/A'."

    chat_history = [{"role": "user", "parts": [{"text": prompt}]}]
    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "iata_code": {"type": "STRING"}
                }
            }
        }
    }

    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not set. IATA lookup will not work.")
        return jsonify({"error": "Gemini API key not configured for IATA lookup."}), 500

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if result.get('candidates') and len(result['candidates']) > 0 and \
           result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts') and \
           len(result['candidates'][0]['content']['parts']) > 0:
            json_response_str = result['candidates'][0]['content']['parts'][0]['text']
            parsed_response = json.loads(json_response_str)
            iata_code = parsed_response.get('iata_code', 'N/A').upper() # Ensure uppercase
            return jsonify({"status": "success", "iata_code": iata_code}), 200
        else:
            return jsonify({"status": "failed", "message": "Could not retrieve IATA code."}), 500

    except requests.exceptions.RequestException as e:
        print(f"Gemini API error for IATA lookup: {e}")
        return jsonify({"error": f"Network or API error for IATA lookup: {str(e)}"}), 500
    except json.JSONDecodeError as e:
        print(f"JSON decoding error from Gemini IATA response: {e}")
        print(f"Raw Gemini IATA response: {result}")
        return jsonify({"error": "Invalid JSON response from Gemini API for IATA lookup."}), 500
    except Exception as e:
        print(f"An unexpected error occurred during IATA lookup: {e}")
        return jsonify({"error": f"An internal server error occurred for IATA lookup: {str(e)}"}), 500

@app.route('/get_live_currency_rate', methods=['POST'])
def get_live_currency_rate():
    """
    Fetches a live currency exchange rate using ExchangeRate-API.
    Requires an API key from exchangerate-api.com.
    """
    data = request.get_json()
    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')

    if not all([from_currency, to_currency]):
        return jsonify({"error": "Missing from_currency or to_currency for rate lookup."}), 400

    exchangerate_api_key = os.getenv("EXCHANGERATE_API_KEY", "xyz") # Environment variable for ExchangeRate-API

    if exchangerate_api_key == "xyz":
        print("Warning: EXCHANGERATE_API_KEY environment variable not set. Live currency rates will not work.")
        return jsonify({"error": "ExchangeRate-API key not configured on the backend."}), 500

    # Ensure currencies are uppercase for API call
    from_currency_upper = from_currency.upper()
    to_currency_upper = to_currency.upper()

    # Using the /latest/{BASE_CURRENCY} format as requested
    currency_api_url = f"https://v6.exchangerate-api.com/v6/{exchangerate_api_key}/latest/{from_currency_upper}"

    try:
        response = requests.get(currency_api_url)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data.get('result') == 'success':
            conversion_rates = data.get('conversion_rates', {})
            if to_currency_upper in conversion_rates:
                conversion_rate = conversion_rates[to_currency_upper]
                # Format to 3 decimal places for consistency
                current_rate_message = f"1 {from_currency_upper} is approximately {conversion_rate:.3f} {to_currency_upper}."
                return jsonify({"status": "success", "rate_message": current_rate_message}), 200
            else:
                return jsonify({"status": "failed", "message": f"Conversion rate for {to_currency_upper} not found in response."}), 500
        else:
            error_type = data.get('error-type', 'unknown error')
            return jsonify({"status": "failed", "message": f"Currency API error: {error_type}"}), 500

    except requests.exceptions.RequestException as e:
        print(f"ExchangeRate-API request error: {e}")
        return jsonify({"error": f"Network or API error for currency lookup: {str(e)}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred during currency lookup: {e}")
        return jsonify({"error": f"An internal server error occurred for currency lookup: {str(e)}"}), 500


if __name__ == '__main__':
    # Run the Flask app on port 5000
    # In a production environment, use a WSGI server like Gunicorn
    app.run(debug=True, port=5000)
