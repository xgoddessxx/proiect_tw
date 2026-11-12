from datetime import datetime
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)


FOLDER_FRONTEND = "frontend"
FOLDER_POSTERE = "posters"


def get_db_connection():
  fisier_secret = "secretraufrate.txt"
  with open(fisier_secret, "r", encoding="utf-8") as f:
    host, database, user, password = f.read().splitlines()

  return pymysql.connect(
      host=host,
      database=database,
      user=user,
      password=password,
      charset="utf8mb4",
      cursorclass=pymysql.cursors.DictCursor,
  )


def format_data_for_json(row):
  if not row:
    return row

  for key, value in row.items():
    if isinstance(value, datetime):
      row[key] = value.strftime("%Y-%m-%d %H:%M:%S")

  if row.get("poster_path") and row["poster_path"] != "NotFound":
    nume_fisier = os.path.basename(row["poster_path"])
    row["poster_path"] = f"http://localhost:5000/posters/{nume_fisier}"

  return row




@app.route("/api/shows", methods=["GET"])
def get_shows():
  conexiune = get_db_connection()
  try:
    with conexiune.cursor() as cursor:
      cursor.execute("SELECT * FROM shows")
      shows = cursor.fetchall()
      shows = [format_data_for_json(s) for s in shows]
      return jsonify(shows)
  finally:
    conexiune.close()


@app.route("/api/shows/<int:show_id>", methods=["GET"])
def get_show_by_id(show_id):
  conexiune = get_db_connection()
  try:
    with conexiune.cursor() as cursor:
      cursor.execute("SELECT * FROM shows WHERE id = %s", (show_id,))
      show = cursor.fetchone()
      if show:
        return jsonify(format_data_for_json(show))
      return jsonify({"error": "Spectacolul nu a fost găsit"}), 404
  finally:
    conexiune.close()


@app.route("/api/schedule", methods=["GET"])
def get_schedule():
  conexiune = get_db_connection()
  try:
    with conexiune.cursor() as cursor:
      cursor.execute("""
                SELECT p.*, s.title as show_title 
                FROM performances p 
                JOIN shows s ON p.show_id = s.id 
                ORDER BY p.start_at ASC
            """)
      schedule = cursor.fetchall()
      schedule = [format_data_for_json(p) for p in schedule]
      return jsonify(schedule)
  finally:
    conexiune.close()



@app.route("/posters/<path:filename>")
def serve_poster(filename):
  return send_from_directory(FOLDER_POSTERE, filename)





@app.route("/")
def serve_index():
  return send_from_directory(FOLDER_FRONTEND, "index.html")


@app.route("/<path:filename>")
def serve_frontend_files(filename):

  if filename.startswith("api/") or filename.startswith("posters/"):
    return "Not found", 404


  if os.path.exists(os.path.join(FOLDER_FRONTEND, filename)):
    return send_from_directory(FOLDER_FRONTEND, filename)



  return send_from_directory(FOLDER_FRONTEND, "index.html")


