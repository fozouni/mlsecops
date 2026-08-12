from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/predict")
def predict():
    return jsonify({"prediction": "malicious", "confidence": 0.93})

# Admin is now on a different route
@app.route("/admin")
def admin():
    return jsonify({"warning": "this should NOT be public"})

# Run both on same port (5000)
app.run(host="0.0.0.0", port=5000)
