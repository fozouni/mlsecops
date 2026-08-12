# admin.py
from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def admin():
    return jsonify({
        "message": "⚠️ ADMIN PANEL - This should NOT be accessible to the public!",
        "status": "restricted",
        "access_level": "admin_only"
    })

app.run(host="0.0.0.0", port=5001)
