from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import json
import uuid

app = Flask(__name__)
app.secret_key = "avika-secret-key-keep-it-safe"

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
PRODUCT_FILE = os.path.join(BASE_DIR, "products.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Create products.json if not exists
if not os.path.exists(PRODUCT_FILE):
    with open(PRODUCT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def load_products():
    if not os.path.exists(PRODUCT_FILE):
        return []
    try:
        with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []

def save_products(products):
    with open(PRODUCT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=4)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/catalog")
def catalog():
    products = load_products()
    
    # Fix missing id + convert price to float safely
    for p in products:
        if "id" not in p:
            p["id"] = str(uuid.uuid4())
        
        if isinstance(p.get("price"), str):
            try:
                p["price"] = float(p["price"])
            except (ValueError, TypeError):
                p["price"] = 0.0
    
    products.sort(key=lambda x: x["id"], reverse=True)
    save_products(products)
    
    return render_template("catalog.html", products=products)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price_str = request.form.get("price", "").strip()
        files = request.files.getlist("file")

        if not name or not price_str:
            flash("Product name and price are required!")
            return redirect(request.url)

        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError
        except ValueError:
            flash("Price must be a positive number!")
            return redirect(request.url)

        if not files or all(f.filename == "" for f in files):
            flash("Please select at least one image!")
            return redirect(request.url)

        saved_files = []
        for file in files:
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                file.save(file_path)
                saved_files.append(unique_name)

        if not saved_files:
            flash("No valid image files selected (only png, jpg, jpeg, gif, webp allowed)")
            return redirect(request.url)

        products = load_products()
        new_product = {
            "id": str(uuid.uuid4()),
            "name": name,
            "price": price,
            "images": saved_files
        }
        products.append(new_product)
        save_products(products)

        flash("Product added successfully! ✅")
        return redirect(url_for("catalog"))

    return render_template("upload.html")

@app.route("/product/<string:pid>")
def product_detail(pid):
    products = load_products()
    product = next((p for p in products if p.get("id") == pid), None)
    
    if not product:
        flash("Product not found!")
        return redirect(url_for("catalog"))

    return render_template("product_detail.html", product=product)

if __name__ == "__main__":
    app.run(debug=True)
