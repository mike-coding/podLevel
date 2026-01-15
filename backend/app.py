from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from utils import Requester, Formatter, ML_Tools

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)

@app.route('/api/channel/<channel_id>/videos')
def channel_videos(channel_id):
    data = Requester.get_channel_videos_request(channel_id)
    features = Formatter.videos_to_dataframe(data)
    features_std = ML_Tools.standardize_features(features)
    lr_result = ML_Tools.run_linear_regression(
        features_std,
        target_column='viewCount',
        trend_df=features,
        trend_time_column='daysSinceOrigination',
    )
    # Return JSON-safe result (exclude non-serializable model)
    lr_json = {k: v for k, v in lr_result.items() if k != 'model'}
    return jsonify(items=data, data_ml=lr_json)

if __name__ == '__main__':
    Requester.store_key_from_env()
    app.run(debug=True)
