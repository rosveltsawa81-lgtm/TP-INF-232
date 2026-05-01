from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permet les requêtes cross-origin depuis le frontend HTML

DB_PATH = "donnees.db"

# ----- Initialisation de la base de données -----
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS personnes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nom       TEXT    NOT NULL,
            age       INTEGER NOT NULL,
            poids     REAL    NOT NULL,
            taille    REAL    NOT NULL,
            imc       REAL    NOT NULL,
            date_ajout TEXT   NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

# ----- Helpers -----
def calcul_imc(poids_kg, taille_cm):
    taille_m = taille_cm / 100
    return round(poids_kg / (taille_m ** 2), 2)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ----- Routes -----

@app.route("/api/personnes", methods=["POST"])
def ajouter_personne():
    data = request.get_json()

    # Validation
    champs = ["nom", "age", "poids", "taille"]
    for c in champs:
        if c not in data or data[c] == "" or data[c] is None:
            return jsonify({"erreur": f"Le champ '{c}' est requis."}), 400

    try:
        nom    = str(data["nom"]).strip()
        age    = int(data["age"])
        poids  = float(data["poids"])
        taille = float(data["taille"])
    except (ValueError, TypeError):
        return jsonify({"erreur": "Valeurs invalides pour age, poids ou taille."}), 400

    if age <= 0 or age > 130:
        return jsonify({"erreur": "Age invalide."}), 400
    if poids <= 0 or poids > 500:
        return jsonify({"erreur": "Poids invalide."}), 400
    if taille <= 0 or taille > 300:
        return jsonify({"erreur": "Taille invalide."}), 400

    imc = calcul_imc(poids, taille)
    date_ajout = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO personnes (nom, age, poids, taille, imc, date_ajout) VALUES (?,?,?,?,?,?)",
        (nom, age, poids, taille, imc, date_ajout)
    )
    conn.commit()
    new_id = c.lastrowid
    conn.close()

    return jsonify({
        "message": "Données enregistrées avec succès.",
        "id": new_id,
        "imc": imc
    }), 201


@app.route("/api/personnes", methods=["GET"])
def lister_personnes():
    conn = get_db()
    rows = conn.execute("SELECT * FROM personnes ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/api/personnes/<int:pid>", methods=["DELETE"])
def supprimer_personne(pid):
    conn = get_db()
    conn.execute("DELETE FROM personnes WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Entrée {pid} supprimée."}), 200


@app.route("/api/stats", methods=["GET"])
def statistiques():
    conn = get_db()
    row = conn.execute("""
        SELECT
            COUNT(*)        AS total,
            ROUND(AVG(age),1)   AS age_moyen,
            ROUND(AVG(poids),1) AS poids_moyen,
            ROUND(AVG(taille),1) AS taille_moyenne,
            ROUND(AVG(imc),2)   AS imc_moyen
        FROM personnes
    """).fetchone()
    conn.close()
    return jsonify(dict(row)), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"✅  API Flask démarrée sur http://localhost:{port}")
    app.run(debug=False, host="0.0.0.0", port=port)

