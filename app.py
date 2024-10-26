# app.py

from flask import Flask, render_template, request
import pymongo

app = Flask(__name__)
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.pdf_manager

@app.route("/", methods=["GET"])
def index():
    query = {}
    keywords_filter = request.args.get('keywords')
    status_filter = request.args.get('status')

    if keywords_filter:
        query["keywords"] = {"$in": [keywords_filter]}
    if status_filter:
        query["status"] = status_filter

    documents = db.documents.find(query)
    return render_template("index.html", documents=documents)

if __name__ == "__main__":
    app.run(debug=True)
