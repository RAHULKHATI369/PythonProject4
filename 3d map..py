import phonenumbers
import geocoder
import folium
import webbrowser
from phonenumbers import geocoder as phone_geocoder, carrier
from opencage.geocoder import OpenCageGeocode

# OpenCage API Key
OPENCAGE_API_KEY = "56ad04481db1431aa77386781c9398bc"

# Function to get a full address from latitude & longitude
def get_full_address(lat, lng):
    geocoder_service = OpenCageGeocode(OPENCAGE_API_KEY)
    results = geocoder_service.reverse_geocode(lat, lng)
    if results:
        return results[0]['formatted']
    return "Unknown Address"

# Start the loop for multiple number tracking
while True:
    # 👉 Step 1: Take Phone Number Input
    number = input("\n📞 Enter phone number with country code (e.g., +14155552671) or type 'exit' to stop: ").strip()

    # Exit condition
    if number.lower() == "exit":
        print("👋 Exiting the program. Have a great day!")
        break

    # ✅ Ensure the number starts with '+'
    if not number.startswith("+"):
        print("❌ Error: Please enter a valid phone number with a country code (e.g., +1 for USA).")
        continue

    try:
        # 👉 Step 2: Parse the Phone Number
        parsed_number = phonenumbers.parse(number, None)

        # 👉 Step 3: Get Number Location & Carrier
        location = phone_geocoder.description_for_number(parsed_number, "en")
        service_provider = carrier.name_for_number(parsed_number, "en")

        print(f"📍 Number's General Location: {location}")
        print(f"📡 Service Provider: {service_provider}")

        # 👉 Step 4: Get Latitude and Longitude (More Accurate)
        geocoder_service = OpenCageGeocode(OPENCAGE_API_KEY)
        results = geocoder_service.geocode(location)

        if results:
            phone_lat = results[0]['geometry']['lat']
            phone_lng = results[0]['geometry']['lng']
            phone_address = get_full_address(phone_lat, phone_lng)  # Get full address

            print(f"🌍 Phone Number Coordinates: {phone_lat}, {phone_lng}")
            print(f"🏠 Phone Number Address: {phone_address}")

            # 👉 Step 5: Get Live Location (More Accurate)
            live_location = geocoder.ip('me')

            if live_location.latlng:
                live_lat, live_lng = live_location.latlng
                live_address = get_full_address(live_lat, live_lng)  # Get full address

                print(f"📡 Your Live Location: {live_lat}, {live_lng}")
                print(f"🏠 Your Current Address: {live_address}")

                # 👉 Step 6: Create a Better Map with Folium (Satellite View for 3D Effect)
                my_map = folium.Map(location=[live_lat, live_lng], zoom_start=15, tiles="Stamen Terrain")

                # Mark phone number's location
                folium.Marker(
                    [phone_lat, phone_lng],
                    popup=f"📍 Phone Number Location: {phone_address}",
                    icon=folium.Icon(color="blue"),
                ).add_to(my_map)

                # Mark live location
                folium.Marker(
                    [live_lat, live_lng],
                    popup=f"📡 Your Live Location: {live_address}",
                    icon=folium.Icon(color="red"),
                ).add_to(my_map)

                # 👉 Step 7: Save & Open Map
                map_file = "live_location.html"
                my_map.save(map_file)
                webbrowser.open(map_file)

                print(f"✅ Map saved as live_location.html. Open it in a browser.")

                # 👉 Step 8: Provide Google Maps Link for More Accuracy
                google_maps_link = f"https://www.google.com/maps/search/?api=1&query={live_lat},{live_lng}"
                print(f"🔗 Open Live Location in Google Maps: {google_maps_link}")
                webbrowser.open(google_maps_link)

            else:
                print("❌ Error: Could not retrieve live location.")
        else:
            print("❌ Error: Could not find phone number location.")

    except phonenumbers.phonenumberutil.NumberParseException as e:
        print(f"❌ Error: {e}")
