### `README.md`

# AI-Powered Travel Agent

This project is a conversational AI-based travel agent that assists users in planning their trips, from choosing a destination and travel method to generating a detailed itinerary and searching for flights. The application features a voice-enabled frontend for natural interaction and a Flask backend that orchestrates calls to various APIs.

-----

## Features

  * **Conversational Interface**: Interact with the AI using a voice-enabled chat interface.
  * **Intelligent Trip Planning**: Generates comprehensive, day-wise travel itineraries based on user inputs.
  * **Dynamic Travel Method Suggestions**: Suggests appropriate travel methods (e.g., flight, train, cruise) based on the origin and destination.
  * **Live Data Integration**: Fetches real-time data for flight searches and currency exchange rates.
  * **Personalized Planning**: Customizes the plan based on budget, number of travelers, food preferences, and hotel preferences.
  * **Booking Simulation**: Simulates a ticket booking process for the generated trip.

-----

## Technologies

### Frontend

  * **HTML, CSS**: For the user interface and styling.
  * **JavaScript**: Manages the conversational flow, speech recognition, speech synthesis, and handles API calls to the backend.

### Backend

  * **Python**: The core programming language.
  * **Flask**: A micro web framework for building the API endpoints.
  * **Gunicorn**: A production-ready WSGI server used for deployment.

### APIs

  * **Gemini API**: Used for AI-powered tasks like generating travel plans, suggesting travel methods, and looking up IATA airport codes.
  * **SerpAPI**: Powers the flight search functionality by querying Google Flights.
  * **ExchangeRate-API**: Provides live currency exchange rates for the currency conversion feature.

-----

## Setup Instructions

### 1\. Backend Setup

1.  Navigate to the `backend/` directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a `.env` file in the `backend/` directory and add your API keys:
    ```env
    GEMINI_API_KEY=your_gemini_api_key
    SERPAPI_API_KEY=your_serpapi_api_key
    EXCHANGERATE_API_KEY=your_exchangerate_api_key
    ```
5.  Run the Flask application:
    ```bash
    gunicorn -w 4 app:app -b 0.0.0.0:5000
    ```

### 2\. Frontend Setup

The frontend is a static HTML file located in the `frontend/` directory.

1.  Open `frontend/index.html` in a web browser.
2.  Update the API endpoint URLs in the `index.html` file to match your backend's host and port if you are deploying it somewhere other than `http://127.0.0.1:5000`.

-----

## Deployment

For production, it is recommended to deploy the backend to a platform like Google App Engine, Heroku, or AWS Elastic Beanstalk and the frontend to a static hosting service like Netlify or Vercel. Ensure all environment variables are securely configured on your chosen platform.

-----

## License

This project is licensed under the MIT License.