from flask import Flask, render_template, request, redirect, jsonify
import requests
import json
import random
import os

app = Flask(__name__)

# Load config
with open('config.json') as f:
    config = json.load(f)

DEFAULT_EVENT_ID = config['event_id']
TBA_AUTH_KEY = os.getenv('TBA_AUTH_KEY')  # Make sure you have this set!

TBA_API_BASE = 'https://www.thebluealliance.com/api/v3'


def tba_get(endpoint):
    headers = {"X-TBA-Auth-Key": TBA_AUTH_KEY}
    response = requests.get(f"{TBA_API_BASE}/{endpoint}", headers=headers)
    response.raise_for_status()
    return response.json()


@app.route('/', methods=['GET'])
def scout():
    event_name = get_event_name(DEFAULT_EVENT_ID)
    return render_template('scout.html', event_id=DEFAULT_EVENT_ID, event_name=event_name)


@app.route('/get_event_name/<event_id>')
def get_event_name_route(event_id):
    return jsonify({'event_name': get_event_name(event_id)})


def get_event_name(event_id):
    try:
        event = tba_get(f"event/{event_id}")
        return event['name']
    except:
        return "Unknown Event"


@app.route('/get_matches/<event_id>')
def get_matches(event_id):
    try:
        matches = tba_get(f"event/{event_id}/matches/simple")
        match_numbers = sorted({m['match_number'] for m in matches})
        return jsonify(match_numbers)
    except:
        return jsonify([])


@app.route('/get_teams/<event_id>/<int:match_number>')
def get_teams(event_id, match_number):
    try:
        matches = tba_get(f"event/{event_id}/matches/simple")
        match = next((m for m in matches if m['match_number'] == match_number), None)
        if not match:
            return jsonify([])

        teams = match['alliances']['red']['team_keys'] + match['alliances']['blue']['team_keys']
        team_numbers = [team.replace('frc', '') for team in teams]
        return jsonify(team_numbers)
    except:
        return jsonify([])


@app.route('/submit', methods=['POST'])
def submit():
    form_data = request.form.to_dict()

    if os.path.exists('scouting_data.json'):
        with open('scouting_data.json', 'r') as f:
            scouting_data = json.load(f)
    else:
        scouting_data = []

    scouting_data.append(form_data)

    with open('scouting_data.json', 'w') as f:
        json.dump(scouting_data, f, indent=2)

    return redirect('/')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
