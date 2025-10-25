from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from database import get_conn, init_db

app = Flask(__name__)
CORS(app)

# Inicializar base de datos
init_db()

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "OK", "message": "Servidor funcionando ✅"}), 200


@app.route("/api/ofertas", methods=["GET"])
def obtener_ofertas():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ofertas")
    ofertas = cur.fetchall()
    conn.close()

    return jsonify([dict(o) for o in ofertas]), 200


@app.route("/api/ofertas", methods=["POST"])
def crear_oferta():
    data = request.json
    empresa = data.get("empresa")
    titulo = data.get("titulo")
    contacto = data.get("contacto")

    if not empresa or not titulo or not contacto:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ofertas (empresa, titulo, contacto)
        VALUES (?, ?, ?)
    """, (empresa, titulo, contacto))
    conn.commit()
    conn.close()

    return jsonify({"message": "Oferta creada correctamente ✅"}), 201

@app.route("/", methods=["GET"])
def index():
    # Redirige la raíz a la ruta de salud de la API
    return redirect("/api/health")

@app.route("/ofertas", methods=["GET", "POST"])
def ofertas():
    conn = get_conn()
    cur = conn.cursor()

    if request.method == "POST":
        data = request.json
        titulo = data.get("titulo")
        empresa = data.get("empresa")
        contacto = data.get("contacto")

        cur.execute(
            "INSERT INTO ofertas (titulo, empresa, contacto) VALUES (?, ?, ?)",
            (titulo, empresa, contacto)
        )
        conn.commit()

        return jsonify({"mensaje": "Oferta registrada correctamente"}), 201

    # Si es GET, devolver todas las ofertas
    cur.execute("SELECT * FROM ofertas")
    rows = cur.fetchall()

    ofertas_list = []
    for row in rows:
        ofertas_list.append({
            "id": row["id"],
            "titulo": row["titulo"],
            "empresa": row["empresa"],
            "contacto": row["contacto"]
        })

    return jsonify(ofertas_list)


if __name__ == "__main__":
    app.run(debug=True)
