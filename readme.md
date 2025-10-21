A.V.I.O.N. - An Interactive Avionics Digital Twin
Welcome to A.V.I.O.N. (Avionics Visualization, Integration, and Operational Network)! This project is a "digital twin" of a modern aircraft's cockpit, built with Python. It's an interactive simulator that brings the complex world of avionics to your desktop, letting you visualize flight data, simulate system faults, and diagnose issues in a hands-on way.
Whether you're an aviation enthusiast, a student, or a developer, A.V.I.O.N. provides a unique window into the technology that powers modern flight.

What Can It Do?
Fly a Digital Cockpit: Experience a sleek glass cockpit GUI with a dynamic Primary Flight Display (PFD) that shows the aircraft's attitude, airspeed, and altitude.
Choose Your Reality: Switch seamlessly between two modes:

Live API Mode: Track real-world commercial flights in real-time.

Demo Mode: Run a fully-featured offline simulation with pre-loaded flight data—no internet or API key needed!

Break Things (and Fix Them!): Use the Maintenance Panel to trigger a realistic EMI/EMC fault. Watch the GPS signal jitter and the instruments freeze, then apply a "shielding" solution and see the system stabilize and recover.
Become a Systems Engineer: Open the Diagnostics Panel and play with low-level hardware settings. Change the baud rate or signal voltage and see how it affects data link health, with real-time feedback on Signal-to-Noise Ratio (SNR) and Data Integrity based on real engineering formulas.
Simulate Upgrades: Use the "Compatibility Check" to see if a new "AI Weather Module" can be integrated, based on live weather data at the aircraft's current location.

How It Works: Demo vs. Live API
A.V.I.O.N. is designed for flexibility. You can choose how you want to run it right from the main screen.

Demo Mode (The Sandbox)
Perfect for getting started or for offline use. When you check the "Demo Mode" box:
The app loads a set of sample flights.
It simulates flight movement with dynamic, randomized data.
All features—from the PFD to the fault simulations—are fully functional.

Live API Mode (The Real Deal)
For a true digital twin experience, uncheck the "Demo Mode" box.
The app connects to the AviationStack API to fetch data for live commercial flights.
You'll need a free API key from AviationStack to use this mode. Just paste it into the key field, and you're ready to track live air traffic on the interactive map.
The Tech Behind the Twin

This project was brought to life with a few key Python libraries:
PyQt6 & PyQt6-WebEngine: For building the entire user interface and embedding the web-based map.
requests: For talking to the AviationStack and weather APIs to get live data.
numpy: For the math behind the realistic GPS noise simulation and dynamic demo data.
plotly: For creating the beautiful, interactive map on the Multi-Function Display.


Get Started in 3 Steps

  1. Clone the project:
  
    git clone <your-repository-url>
  
  2. Install the good stuff:
  
    pip install -r requirements.txt
  
  3. Launch the project
  
    python avion_main.py

