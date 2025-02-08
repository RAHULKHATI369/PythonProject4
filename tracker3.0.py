from flask import Flask, render_template, request, jsonify
import phonenumbers
import geocoder
import sqlite3
import folium
import webbrowser
from phonenumbers import geocoder as phone_geocoder, carrier
from opencage.geocoder import OpenCageGeocode

# Initialize Flask App
app = Flask(__name__)

# OpenCage API Key (Get from https://opencagedata.com/api)
OPENCAGE_API_KEY = "56ad04481db1431aa77386781c9398bc"
geocoder_service = OpenCageGeocode(OPENCAGE_API_KEY)

# Database setup
DB_FILE = "tracker.db"

def init_db():
    """Initialize the database and create a table if not exists"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tracked_numbers
                 (id INTEGER PRIMARY KEY, number TEXT, location TEXT, address TEXT, lat REAL, lng REAL)''')
    conn.commit()
    conn.close()

init_db()

def get_address(lat, lng):
    """Get formatted address from latitude & longitude"""
    results = geocoder_service.reverse_geocode(lat, lng)
    return results[0]['formatted'] if results else "Unknown Location"

@app.route("/", methods=["GET", "POST"])
def index():
    """Main Route"""
    if request.method == "POST":
        number = request.form["phone_number"].strip()

        # Validate phone number
        if not number.startswith("+"):
            return jsonify({"error": "Please enter a valid phone number with a country code."})

        try:
            # Parse phone number
            parsed_number = phonenumbers.parse(number, None)
            location = phone_geocoder.description_for_number(parsed_number, "en")
            service_provider = carrier.name_for_number(parsed_number, "en")

            # Get phone number coordinates
            results = geocoder_service.geocode(location)
            if results:
                phone_lat, phone_lng = results[0]['geometry']['lat'], results[0]['geometry']['lng']
                phone_address = get_address(phone_lat, phone_lng)
            else:
                return jsonify({"error": "Could not retrieve phone number location."})

            # Get user live location
            live_location = geocoder.ip('me')
            if live_location.latlng:
                live_lat, live_lng = live_location.latlng
                live_address = get_address(live_lat, live_lng)
            else:
                return jsonify({"error": "Could not retrieve live location."})

            # Store tracking data in database (keep last 10 records)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO tracked_numbers (number, location, address, lat, lng) VALUES (?, ?, ?, ?, ?)",
                      (number, location, phone_address, phone_lat, phone_lng))
            conn.commit()
            conn.close()

            # Generate Map
            my_map = folium.Map(location=[live_lat, live_lng], zoom_start=14, tiles="OpenStreetMap")
            folium.Marker([phone_lat, phone_lng], popup=f"📍 {phone_address}", icon=folium.Icon(color="blue")).add_to(my_map)
            folium.Marker([live_lat, live_lng], popup=f"📡 {live_address}", icon=folium.Icon(color="red")).add_to(my_map)
            map_file = "static/map.html"
            my_map.save(map_file)

            # Return data to frontend
            return jsonify({
                "phone_number": number,
                "location": location,
                "service_provider": service_provider,
                "phone_address": phone_address,
                "phone_lat": phone_lat,
                "phone_lng": phone_lng,
                "live_address": live_address,
                "live_lat": live_lat,
                "live_lng": live_lng,
                "map_file": map_file
            })

        except phonenumbers.phonenumberutil.NumberParseException:
            return jsonify({"error": "Invalid phone number format."})

    return render_template("index.html")

@app.route("/history")
def history():
    """Retrieve the last 10 tracked numbers"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM tracked_numbers ORDER BY id DESC LIMIT 10")
    history_data = c.fetchall()
    conn.close()
    return jsonify(history_data)

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, jsonify
import sqlite3
import phonenumbers
import geocoder
import folium
import os
import webbrowser
from phonenumbers import geocoder as phone_geocoder, carrier
from opencage.geocoder import OpenCageGeocode

app = Flask(__name__)

# Initialize the DB (SQLite)
def init_db():
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()

    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT NOT NULL,
                    location TEXT,
                    lat REAL,
                    lng REAL,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Create tracked_numbers table
    c.execute('''CREATE TABLE IF NOT EXISTS tracked_numbers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    phone_number TEXT NOT NULL,
                    location TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')

    # Create location_history table
    c.execute('''CREATE TABLE IF NOT EXISTS location_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    phone_number TEXT NOT NULL,
                    location TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')

    conn.commit()
    conn.close()

# Run init_db() to create tables if not exist
init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        phone_number = request.form["phone_number"].strip()
        user_id = request.form["user_id"]

        # Validate phone number
        if not phone_number.startswith("+"):
            return jsonify({"error": "Please enter a valid phone number with a country code."})

        try:
            # Parse phone number
            parsed_number = phonenumbers.parse(phone_number, None)
            location = phone_geocoder.description_for_number(parsed_number, "en")
            service_provider = carrier.name_for_number(parsed_number, "en")

            # Get phone number coordinates
            key = "YOUR_OPENCAGE_API_KEY"  # Use your actual OpenCage API key
            geocoder_service = OpenCageGeocode(key)
            results = geocoder_service.geocode(location)
            if results:
                phone_lat, phone_lng = results[0]['geometry']['lat'], results[0]['geometry']['lng']
                phone_address = f"{location}, {phone_lat}, {phone_lng}"
            else:
                return jsonify({"error": "Could not retrieve phone number location."})

            # Get live location
            live_location = geocoder.ip('me')
            if live_location.latlng:
                live_lat, live_lng = live_location.latlng
                live_address = f"Live location: {live_lat}, {live_lng}"
            else:
                return jsonify({"error": "Could not retrieve live location."})

            # Insert data into DB
            insert_tracked_data(user_id, phone_number, phone_address, phone_lat, phone_lng)

            # Create a map
            my_map = folium.Map(location=[live_lat, live_lng], zoom_start=12)
            folium.Marker([phone_lat, phone_lng], popup=f"Phone Location: {phone_address}", icon=folium.Icon(color="blue")).add_to(my_map)
            folium.Marker([live_lat, live_lng], popup=f"Your Location: {live_address}", icon=folium.Icon(color="red")).add_to(my_map)
            map_file = "static/map.html"
            my_map.save(map_file)

            return jsonify({
                "phone_number": phone_number,
                "location": location,
                "service_provider": service_provider,
                "phone_address": phone_address,
                "phone_lat": phone_lat,
                "phone_lng": phone_lng,
                "live_address": live_address,
                "live_lat": live_lat,
                "live_lng": live_lng,
                "map_file": map_file
            })

        except phonenumbers.phonenumberutil.NumberParseException:
            return jsonify({"error": "Invalid phone number format."})

    return render_template("index.html")


def insert_tracked_data(user_id, phone_number, location, lat, lng):
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()

    # Insert into tracked_numbers table
    c.execute('''INSERT INTO tracked_numbers (user_id, phone_number, location, lat, lng)
                 VALUES (?, ?, ?, ?, ?)''', (user_id, phone_number, location, lat, lng))

    # Insert into location_history table
    c.execute('''INSERT INTO location_history (user_id, phone_number, location, lat, lng)
                 VALUES (?, ?, ?, ?, ?)''', (user_id, phone_number, location, lat, lng))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    app.run(debug=True)
