from flask import Flask, render_template, request, redirect, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)

# -------- ABSOLUTE UPLOAD FOLDER (FIXED) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# create uploads folder automatically
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# -------- ALLOWED FILE TYPES --------
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'jpg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------- DATABASE CREATE --------
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # USERS TABLE
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            password TEXT
        )
    ''')

    # MATERIALS TABLE
    cur.execute('''
        CREATE TABLE IF NOT EXISTS materials(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subject TEXT,
            semester TEXT,
            filename TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# -------- HOME PAGE --------
@app.route("/")
def home():
    return render_template("home.html")

# -------- REGISTER PAGE --------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                    (name,email,password))
        conn.commit()
        conn.close()
        return redirect("/login")
    return render_template("register.html")

# -------- LOGIN PAGE --------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?",
                    (email,password))
        user = cur.fetchone()
        conn.close()

        if user:
            return redirect("/upload")
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

# -------- UPLOAD PAGE --------
@app.route("/upload", methods=["GET","POST"])
def upload():
    if request.method == "POST":
        title = request.form["title"]
        subject = request.form["subject"]
        semester = request.form["semester"]
        file = request.files["file"]

        # secure + validation
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            cur.execute("INSERT INTO materials (title,subject,semester,filename) VALUES (?,?,?,?)",
                        (title,subject,semester,filename))
            conn.commit()
            conn.close()

            return "File Uploaded Successfully!"
        else:
            return "Only PDF, DOCX, TXT, JPG, PNG files allowed!"

    return render_template("upload.html")

# -------- VIEW MATERIALS PAGE --------
@app.route("/materials")
def materials():
    subject = request.args.get("subject")
    semester = request.args.get("semester")

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if subject and semester:
        cur.execute("SELECT * FROM materials WHERE subject=? AND semester=?", (subject, semester))
    else:
        cur.execute("SELECT * FROM materials")

    all_materials = cur.fetchall()
    conn.close()

    return render_template("materials.html", materials=all_materials)

# -------- DOWNLOAD FILE --------
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# -------- DELETE MATERIAL --------
@app.route("/delete/<int:id>")
def delete_material(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT filename FROM materials WHERE id=?", (id,))
    file = cur.fetchone()

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file[0])
        if os.path.exists(filepath):
            os.remove(filepath)

    cur.execute("DELETE FROM materials WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/materials")

if __name__ == "__main__":
    app.run(debug=True)