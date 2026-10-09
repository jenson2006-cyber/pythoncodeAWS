
import os
from flask import Flask, render_template, request
import boto3
import pymysql

app = Flask(__name__)

BUCKET_NAME = os.environ.get(
    "S3_BUCKET",
    "jenson-flask-photos-2026"
)

def get_db_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "studentdb"),
        cursorclass=pymysql.cursors.Cursor
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]
    course = request.form["course"]
    photo = request.files.get("photo")

    if not photo or not photo.filename:
        return "Please select a photo.", 400

    s3 = boto3.client("s3")

    s3.upload_fileobj(
        photo,
        BUCKET_NAME,
        photo.filename
    )

    photo_url = (
        f"https://{BUCKET_NAME}.s3."
        f"{os.environ.get('AWS_REGION', 'ap-southeast-2')}"
        f".amazonaws.com/{photo.filename}"
    )

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO students
                (name, email, course, photo_url)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (name, email, course, photo_url)
            )

        connection.commit()
    finally:
        connection.close()

    return "Student Registered Successfully"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
