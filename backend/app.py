from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from utils import Requester

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)

@app.route('/api/channel/<channel_id>/videos')
def channel_videos(channel_id):
    data = Requester.get_channel_videos_request(channel_id)
    return jsonify(items=data)

if __name__ == '__main__':
    Requester.store_key_from_env()
    app.run(debug=True)
