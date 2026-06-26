from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('stock.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS articles (id INTEGER PRIMARY KEY, nom TEXT, prix REAL, stock INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS historique (id INTEGER PRIMARY KEY, article TEXT, qte INTEGER, total REAL, date TEXT)')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    articles = conn.execute('SELECT * FROM articles').fetchall()
    ventes = conn.execute('SELECT * FROM historique ORDER BY id DESC').fetchall()
    ca_total = sum(v['total'] for v in ventes)
    conn.close()
    return render_template('index.html', articles=articles, ventes=ventes, ca_total=ca_total)

@app.route('/ajouter', methods=['POST'])
def ajouter():
    nom = request.form.get('nom')
    prix = request.form.get('prix')
    if nom and prix:
        conn = get_db_connection()
        conn.execute('INSERT INTO articles (nom, prix, stock) VALUES (?, ?, 0)', (nom, prix))
        conn.commit()
        conn.close()
    return redirect('/')

@app.route('/ajouter_stock', methods=['POST'])
def ajouter_stock():
    conn = get_db_connection()
    conn.execute('UPDATE articles SET stock = stock + ? WHERE id = ?', (int(request.form.get('qte', 0)), request.form.get('id')))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/vendre', methods=['POST'])
def vendre():
    id_art = request.form.get('id')
    qte = int(request.form.get('qte', 0))
    nom = request.form.get('nom')
    prix = float(request.form.get('prix', 0))
    conn = get_db_connection()
    conn.execute('UPDATE articles SET stock = stock - ? WHERE id = ?', (qte, id_art))
    conn.execute('INSERT INTO historique (article, qte, total, date) VALUES (?, ?, ?, ?)', 
                 (nom, qte, qte * prix, datetime.now().strftime("%d/%m %H:%M")))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/generer_recu', methods=['POST'])
def generer_recu():
    nom = request.form.get('nom')
    qte = request.form.get('qte')
    total = request.form.get('total')
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "--- RECU DE BOUTIQUE ---")
    c.drawString(100, 730, f"Article : {nom}")
    c.drawString(100, 710, f"Quantité : {qte}")
    c.drawString(100, 690, f"Total : {total}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="recu.pdf", mimetype='application/pdf')

@app.route('/supprimer_article', methods=['POST'])
def supprimer_article():
    conn = get_db_connection()
    conn.execute('DELETE FROM articles WHERE id = ?', (request.form.get('id'),))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/supprimer_historique', methods=['POST'])
def supprimer_historique():
    conn = get_db_connection()
    conn.execute('DELETE FROM historique')
    conn.commit()
    conn.close()
    return redirect('/')