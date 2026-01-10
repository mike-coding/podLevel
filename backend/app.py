from flask import Flask, jsonify
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)

@app.route('/api/hello')
def hello():
    has_key = 'KEY' in os.environ and bool(os.environ.get('KEY'))
    return jsonify(message='Hello from Flask', hasKey=has_key)

if __name__ == '__main__':
    app.run(debug=True)
