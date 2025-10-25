import sqlite3
import hashlib
import uuid
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from database import get_conn, init_db

app = Flask(__name__)
CORS(app)

# Inicializar base de datos
init_db()

# Helper para hashear password
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

# Helper para encontrar usuario por token
def get_user_by_token(token):
    if not token:
        return None
    db = get_conn()
    user = db.execute("SELECT * FROM usuarios WHERE token=?", (token,)).fetchone()
    db.close()
    return user

@app.route("/")
def index():
    return redirect("/api/health")

@app.route("/api/health")
def health():
    return jsonify({"status": "OK", "message": "Servidor funcionando ✅"}), 200

# ------------------------
# AUTH
# ------------------------

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json or {}
    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")

    if not (nombre and email and password):
        return jsonify({"error": "Faltan datos"}), 400

    pw_hash = hash_password(password)
    token = str(uuid.uuid4())

    db = get_conn()
    try:
        db.execute("INSERT INTO usuarios (nombre, email, password_hash, token) VALUES (?,?,?,?)",
                    (nombre, email, pw_hash, token))
        db.commit()
        return jsonify({"message": "Registrado ✅", "token": token, "nombre": nombre}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email ya registrado"}), 409
    finally:
        db.close()

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not (email and password):
        return jsonify({"error": "Faltan datos"}), 400

    pw_hash = hash_password(password)

    db = get_conn()
    user = db.execute("SELECT id,nombre,token,password_hash FROM usuarios WHERE email=?", (email,)).fetchone()
    db.close()

    if not user or user["password_hash"] != pw_hash:
        return jsonify({"error": "Credenciales inválidas"}), 401

    return jsonify({"token": user["token"], "nombre": user["nombre"]}), 200

@app.route("/api/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization", "").replace("Token ", "")
    user = get_user_by_token(token)
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    db = get_conn()
    new_token = str(uuid.uuid4())
    db.execute("UPDATE usuarios SET token=? WHERE id=?", (new_token, user["id"]))
    db.commit()
    db.close()

    return jsonify({"message": "Sesión cerrada ✅"}), 200


# ------------------------
# OFERTAS
# ------------------------

@app.route("/api/ofertas", methods=["GET", "POST"])
def ofertas():
    db = get_conn()

    # GET → Listar ofertas
    if request.method == "GET":
        rows = db.execute(
            "SELECT id,titulo,empresa,contacto,salario,descripcion,creado_en,publicado_por "
            "FROM ofertas ORDER BY id DESC"
        ).fetchall()
        ofertas = [dict(r) for r in rows]
        db.close()
        return jsonify(ofertas), 200

    # POST → Crear oferta (requiere token)
    token = request.headers.get("Authorization", "").replace("Token ", "")
    user = get_user_by_token(token)
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    data = request.json or {}
    titulo = data.get("titulo")
    empresa = data.get("empresa")
    contacto = data.get("contacto")
    salario = data.get("salario")
    descripcion = data.get("descripcion", "")

    if not (titulo and empresa and contacto):
        return jsonify({"error": "Campos obligatorios: título, empresa, contacto"}), 400

    db.execute(
        "INSERT INTO ofertas (titulo, empresa, contacto, salario, descripcion, publicado_por) "
        "VALUES (?,?,?,?,?,?)",
        (titulo, empresa, contacto, salario, descripcion, user["id"])
    )
    db.commit()
    db.close()

    return jsonify({"message": "Oferta creada ✅"}), 201


# ------------------------
# MAIN
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)
