from flask import Flask, render_template, request, redirect, jsonify
import requests
import json
import random
import os

app = Flask(__name__)

# Load config
with open('config.json') as f:
    config = json.load(f)

EVENT_ID = config['event_id']
TBA_AUTH_KEY = os.getenv('TBA_AUTH_KEY')  # You'll need your Blue Alliance API key as an environment variable

TBA_API_BASE = 'https://www.thebluealliance.com/api/v3'


def get_event_name(event_id):
    headers = {"X-TBA-Auth-Key": TBA_AUTH_KEY}
    response = requests.get(f"{TBA_API_BASE}/event/{event_id}", headers=headers)
    if response.status_code == 200:
        return response.json()['name']
    return "Unknown Event"


def get_current_match(event_id):
    headers = {"X-TBA-Auth-Key": TBA_AUTH_KEY}
    response = requests.get(f"{TBA_API_BASE}/event/{event_id}/matches/simple", headers=headers)
    if response.status_code != 200:
        return None

    matches = response.json()
    # Filter out matches that haven't been played yet (no score posted)
    played_matches = [m for m in matches if m['alliances']['red']['score'] != -1]
    
    if not played_matches:
        return None
    
    # Get the next match that hasn't been played
    next_match = matches[len(played_matches)]
    
    teams = next_match['alliances']['red']['team_keys'] + next_match['alliances']['blue']['team_keys']
    match_number = next_match['match_number']

    # Clean team numbers (remove 'frc' prefix)
    team_numbers = [team.replace('frc', '') for team in teams]
    
    return {
        'match_number': match_number,
        'team_numbers': team_numbers
    }


@app.route('/', methods=['GET', 'POST'])
def scout():
    event_name = get_event_name(EVENT_ID)
    current_match = get_current_match(EVENT_ID)

    if not current_match:
        return "No upcoming matches found!"

    assigned_team = random.choice(current_match['team_numbers'])

    if request.method == 'POST':
        # Handle form submission
        data = request.form.to_dict()
        data['assigned_team'] = request.form.get('assigned_team')
        data['match_number'] = request.form.get('match_number')

        # Save scouting data
        if os.path.exists('scouting_data.json'):
            with open('scouting_data.json', 'r') as f:
                scouting_data = json.load(f)
        else:
            scouting_data = []

        scouting_data.append(data)

        with open('scouting_data.json', 'w') as f:
            json.dump(scouting_data, f, indent=2)

        return redirect('/')

    return render_template('scout.html', event_name=event_name, current_match=current_match, assigned_team=assigned_team)


if __name__ == "__main__":
    app.run(debug=True)
