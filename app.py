from flask  import Flask, render_template, request,g, redirect, url_for, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
app = Flask(__name__)
DATABASE = "contract_farming.db"
app.secret_key = "pasta"  

def get_db():
    if not hasattr(g, "_database"):
        g._database = sqlite3.connect(DATABASE)
        g._database.row_factory = sqlite3.Row
    return g._database

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def execute_query(query, params=(), fetch=False, single=False):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone() if single else cursor.fetchall() if fetch else None
    conn.commit()
    return result

def init_db():
    execute_query("""
    CREATE TABLE IF NOT EXISTS farmers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        mobile TEXT NOT NULL,
        dob date NOT NULL,
        registration_date TEXT NOT NULL,
        address TEXT NOT NULL,
        password TEXT NOT NULL)""")
    execute_query('''CREATE TABLE IF NOT EXISTS crops (
                        farmer_id INTEGER NOT NULL,
                        crop_name TEXT NOT NULL,
                        price REAL NOT NULL,
                        quantity REAL NOT NULL,
                        fertilizers TEXT,
                        grade TEXT,
                        FOREIGN KEY (farmer_id) REFERENCES farmers(id))''')
@app.route("/")
def home():
    return render_template("homepage.html")
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/deals")
def Deals():
    return render_template("deal.html")
@app.route('/inventory')
def inventory():
    if "farmer_id" not in session:
        return redirect(url_for("home"))  
    farmer_id = session["farmer_id"]
    crops = execute_query("SELECT * FROM crops WHERE farmer_id = ?", (farmer_id,), fetch=True)
    return render_template("inventory.html", crops=crops)

@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/farmer/<int:farmer_id>")
def farmer_dashboard(farmer_id):
    farmer = execute_query("SELECT * FROM farmers WHERE id = ?", (farmer_id,), fetch=True)
    return render_template("farmer.html", farmer=farmer[0]) if farmer else ("Farmer not found", 404)

@app.route('/register_farmer', methods=["POST"])
def register_farmer():
    try:
        data = request.get_json()
        existing_farmer = execute_query("SELECT id FROM farmers WHERE username = ?", (data["username"],), fetch=True, single=True)
        if existing_farmer:
            return jsonify({"success": False, "error": "Username already exists"}), 400
        
        hashed_password = generate_password_hash(data["password"])
        execute_query("INSERT INTO farmers (full_name, username, mobile, dob, address, password, registration_date) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                      (data["full_name"], data["username"], data["mobile"], data["dob"], data["address"], hashed_password, datetime.datetime.now().strftime("%Y-%m-%d")))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/login_farmer', methods=['POST'])
def login_farmer():
    try:
        data = request.get_json()
        username = data["username"]
        password = data["password"]
        farmer = execute_query("SELECT id, password FROM farmers WHERE username = ?", 
                               (username,), fetch=True, single=True)
        if farmer:
            stored_hash = str(farmer["password"])
            if check_password_hash(stored_hash, password):
                session["farmer_id"] = farmer["id"]
                print("Login Successful")
                return jsonify({"success": True, "farmer_id": farmer["id"]})
            else:
                print("Password verification failed")
                return jsonify({"success": False, "error": "Invalid credentials"})
        else:
            print("User not found")
            return jsonify({"success": False, "error": "User not found"})
    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "error": str(e)})

@app.route("/add_crop", methods=["POST"])
def add_crop():
    if "farmer_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401  
    try:
        data = request.get_json()
        required_fields = ["crop_name", "price", "quantity", "fertilizers", "grade"]
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        execute_query("""INSERT INTO crops (farmer_id, crop_name, price, quantity, fertilizers, grade)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                      (session["farmer_id"], data["crop_name"], data["price"], data["quantity"], data["fertilizers"], data["grade"]))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("home")), 302

if __name__ == '__main__':
    init_db
    app.run(debug = True)