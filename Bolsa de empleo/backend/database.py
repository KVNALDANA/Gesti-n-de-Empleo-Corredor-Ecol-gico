import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "bolsa.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        token TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ofertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        empresa TEXT,
        contacto TEXT,
        salario TEXT,
        descripcion TEXT,
        creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
        publicado_por INTEGER,
        FOREIGN KEY(publicado_por) REFERENCES usuarios(id)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS postulaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        oferta_id INTEGER,
        mensaje TEXT,
        fecha TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY(oferta_id) REFERENCES ofertas(id)
    )""")
    conn.commit()
    conn.close()
    print("Base de datos inicializada en:", DB_PATH)

if __name__ == "__main__":
    init_db()
