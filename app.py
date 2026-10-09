from flask import Flask, render_template, jsonify, send_file, request
import requests
import random
import sqlite3
import os
import qrcode
import io
from datetime import datetime

app = Flask(__name__)

# Pushbullet Token configured on backend
PUSHBULLET_ACCESS_TOKEN = "o.wxLz4xoT36eCul5tvQFO916mdpxrLMrX" 
DATABASE = "smartcity.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # EV Charging Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ev_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id TEXT NOT NULL,
            station TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            vehicle_number TEXT NOT NULL,
            mobile TEXT NOT NULL,
            hours REAL NOT NULL,
            total_cost REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # EB Records Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eb_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumer_no TEXT NOT NULL,
            mobile TEXT NOT NULL,
            units REAL NOT NULL,
            amount_payable REAL NOT NULL,
            warning_sent INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # Smart Parking Bookings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            location TEXT NOT NULL,
            vehicle_number TEXT NOT NULL,
            mobile TEXT NOT NULL,
            hours INTEGER NOT NULL,
            amount_paid REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # Urban Company Service Bookings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urban_company_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id TEXT NOT NULL,
            service_name TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            address TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

OFFICIAL_LINKS = {
    "gcc_property_tax": "https://chennaicorporation.gov.in/gcc/online-payment/property-tax/",
    "tangedco_eb": "https://www.tnebnet.org/",
    "cmrl_metro": "https://chennaimetrorail.org/",
    "mtc_bus": "https://mtcbus.tn.gov.in/",
    "urban_company": "https://www.urbancompany.com/"
}

# --- Page Routes ---
@app.route('/bus')
def live_bus():
    return render_template('bus.html')

@app.route('/')
def index():
    return render_template('index.html', official_links=OFFICIAL_LINKS)

@app.route('/parking')
def parking():
    return render_template('parking.html')

@app.route('/urban_company')
def urban_company():
    return render_template('urban_company.html')

@app.route('/traffic_simulator')
def traffic_simulator():
    return render_template('traffic_simulator.html')

@app.route('/satellite_map')
def satellite_map():
    return render_template('satellite_map.html')

@app.route('/sos')
def sos():
    return render_template('sos.html')

@app.route('/ev_charging')
def ev_charging():
    return render_template('ev_charging.html')

@app.route('/electricity')
def electricity():
    return render_template('electricity.html', official_link=OFFICIAL_LINKS["tangedco_eb"])

@app.route('/tax')
def tax_page():
    return render_template('tax.html')

@app.route('/api/tax_bill', methods=['POST'])
def generate_tax_bill():
    data = request.json or {}
    zone = data.get('zone', 'Zone 14 - Perungudi')
    property_id = data.get('property_id', 'GCC-TAX-10492')
    owner = data.get('owner', 'Property Owner')
    sqft = float(data.get('sqft', 1000))
    
    # GCC Property Tax Calculation (Base rate ₹1.50 per sq.ft / half-year)
    half_yearly_tax = sqft * 1.50
    library_cess = half_yearly_tax * 0.10
    total_payable = half_yearly_tax + library_cess

    return jsonify({
        "status": "success",
        "bill_no": f"GCC-BILL-{random.randint(10000, 99999)}",
        "property_id": property_id,
        "owner": owner,
        "zone": zone,
        "sqft": sqft,
        "tax_amount": round(half_yearly_tax, 2),
        "cess": round(library_cess, 2),
        "total_payable": round(total_payable, 2),
        "date": datetime.now().strftime("%d-%b-%Y")
    })

@app.route('/metro')
def metro():
    return render_template('metro.html')

@app.route('/flood_route')
def flood_route():
    return render_template('flood_route.html')

# --- API Endpoints ---

@app.route('/api/parking_reserve', methods=['POST'])
def reserve_parking():
    """Reserves a parking slot with Vehicle No & Mobile and generates a Bill"""
    data = request.json or {}
    location = data.get('location', 'Pondy Bazaar Pedestrian Plaza')
    vehicle_number = data.get('vehicle_number', '').strip().upper()
    mobile = data.get('mobile', '').strip()
    hours = int(data.get('hours', 1))

    if not vehicle_number or not mobile:
        return jsonify({"status": "error", "message": "Vehicle Number and Mobile Number are required!"}), 400

    rate_per_hr = 20 if "Pondy" in location or "Marina" in location else 30
    total_cost = hours * rate_per_hr
    ticket_id = f"PRK-CHN-{random.randint(10000, 99999)}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Store in SQLite
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO parking_bookings (ticket_id, location, vehicle_number, mobile, hours, amount_paid, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ticket_id, location, vehicle_number, mobile, hours, total_cost, now_str))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "ticket_id": ticket_id,
        "location": location,
        "vehicle_number": vehicle_number,
        "mobile": mobile,
        "hours": hours,
        "rate_per_hr": rate_per_hr,
        "total_cost": total_cost,
        "issued_at": now_str
    })

@app.route('/api/speed_monitor')
def speed_monitor():
    """Live Speed Radar Monitoring for Subramanya Nagar St, Thoraipakkam"""
    # Simulated vehicle speeds
    detected_vehicles = [
        {"vehicle_no": "TN 07 CA 9012", "type": "Car", "speed": 52, "road": "Subramanya Nagar St, Thoraipakkam", "limit": 40},
        {"vehicle_no": "TN 10 BD 4410", "type": "Bike", "speed": 48, "road": "Subramanya Nagar St, Thoraipakkam", "limit": 40},
        {"vehicle_no": "TN 01 AZ 1120", "type": "Auto", "speed": 34, "road": "Subramanya Nagar St, Thoraipakkam", "limit": 40},
        {"vehicle_no": "TN 09 ER 8890", "type": "Car", "speed": 61, "road": "Subramanya Nagar St, Thoraipakkam", "limit": 40}
    ]
    violations = [v for v in detected_vehicles if v["speed"] > 40]
    return jsonify({
        "road": "Subramanya Nagar St, Thoraipakkam",
        "speed_limit_kmh": 40,
        "total_scanned": len(detected_vehicles),
        "violations_detected": len(violations),
        "violations": violations
    })

@app.route('/api/urban_company_book', methods=['POST'])
def book_urban_company():
    """Books Urban Company Service and saves to DB"""
    data = request.json or {}
    service_name = data.get('service_name')
    customer_name = data.get('customer_name')
    mobile = data.get('mobile')
    address = data.get('address')
    time_slot = data.get('time_slot')

    booking_id = f"UC-CHN-{random.randint(10000, 99999)}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO urban_company_bookings (booking_id, service_name, customer_name, mobile, address, time_slot, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (booking_id, service_name, customer_name, mobile, address, time_slot, 'Assigned Partner', now_str))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "booking_id": booking_id,
        "service_name": service_name,
        "time_slot": time_slot,
        "message": f"Partner assigned! Technician will visit {address}."
    })

@app.route('/api/dispatch_sos', methods=['POST'])
def dispatch_sos():
    """Dispatches Emergency SOS to Near Police Station (J9 Thoraipakkam) & Pink Patrol"""
    data = request.json or {}
    lat = data.get('lat', 12.9623)
    lng = data.get('lng', 80.2432)
    mobile = data.get('mobile', 'Emergency Contact')

    sos_ref = f"SOS-THORAIPAKKAM-{random.randint(1000, 9999)}"
    
    return jsonify({
        "status": "success",
        "sos_ref": sos_ref,
        "nearest_police": "J9 Thoraipakkam Police Station (0.8 km)",
        "pink_patrol_unit": "Pink Patrol Unit Vehicle #4 - OMR Signal (0.3 km away)",
        "eta": "3 mins",
        "dispatched_lat": lat,
        "dispatched_lng": lng
    })

@app.route('/api/eb_bill', methods=['POST'])
def calculate_eb_bill():
    data = request.json or {}
    consumer_no = data.get('consumer_no', '').strip()
    mobile = data.get('mobile', '').strip()
    units = float(data.get('units', 0))

    if not consumer_no or not mobile:
        return jsonify({"status": "error", "message": "Consumer Number and Mobile are required!"}), 400

    # Tiered Domestic Tariff Calculation (TANGEDCO Slabs)
    if units <= 100:
        amount = 0.0
    elif units <= 200:
        amount = (units - 100) * 2.25
    elif units <= 400:
        amount = (100 * 2.25) + ((units - 200) * 4.50)
    elif units <= 500:
        amount = (100 * 2.25) + (200 * 4.50) + ((units - 400) * 6.00)
    else:
        amount = (100 * 2.25) + (200 * 4.50) + (100 * 6.00) + ((units - 500) * 8.00)

    warning_sent = False

    # Send Pushbullet Notification if consumption exceeds 450 units
    if units > 450:
        # Replace with your actual Pushbullet API Token from pushbullet.com
        token = "o.wxLz4xoT36eCul5tvQFO916mdpxrLMrX" 
        headers = {
            'Access-Token': token,
            'Content-Type': 'application/json'
        }
        payload = {
            "type": "note",
            "title": "⚡ TANGEDCO High Electricity Consumption Alert",
            "body": f"Consumer No: {consumer_no}\nHigh Usage Detected: {units} Units.\nEstimated Bill: ₹{amount:.2f}\nPlease reduce usage to avoid higher tariffs."
        }
        try:
            resp = requests.post('https://api.pushbullet.com/v2/pushes', json=payload, headers=headers)
            if resp.status_code == 200:
                warning_sent = True
        except Exception as e:
            print("Pushbullet Error:", e)

    # Save to SQLite Database
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO eb_records (consumer_no, mobile, units, amount_payable, warning_sent, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (consumer_no, mobile, units, amount, 1 if warning_sent else 0, now_str))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "consumer_no": consumer_no,
        "units": units,
        "amount_payable": round(amount, 2),
        "warning_sent": warning_sent,
        "issued_at": now_str
    })

# Dynamic QR Code Route
@app.route('/qrcode')
def generate_qr():
    portal_url = request.host_url.rstrip('/')
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(portal_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
