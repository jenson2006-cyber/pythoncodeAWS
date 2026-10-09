
import os
import boto3
import pymysql
from flask import Flask, render_template, request

app = Flask(__name__)

bucket_name = os.environ.get("S3_BUCKET_NAME")


def get_db_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "studentdb"),
        connect_timeout=10
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

    if not bucket_name:
        return "S3 bucket configuration is missing.", 500

    connection = None
    cursor = None

    try:
        s3 = boto3.client("s3")
        s3.upload_fileobj(
            photo,
            bucket_name,
            photo.filename
        )

        photo_url = (
            f"https://{bucket_name}.s3."
            f"{os.environ.get('AWS_REGION', 'ap-southeast-2')}"
            f".amazonaws.com/{photo.filename}"
        )

        connection = get_db_connection()
        cursor = connection.cursor()

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

        return "Student Registered Successfully"

    except Exception:
        app.logger.exception("Student registration failed")

        if connection:
            connection.rollback()

        return "Registration failed. Please check the server logs.", 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

