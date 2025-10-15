from flask import Flask, jsonify, render_template
from model import SurvivalModel
from agent import SurvivorAgent, GameNodeAgent, ObstacleAgent

app = Flask(__name__)
model = SurvivalModel()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/step', methods=['POST'])
def step():
    model.step()
    agent_data = []
    for agent in model.agents:
        agent_type = 'survivor' # Default type
        if isinstance(agent, SurvivorAgent):
            agent_type = 'survivor'
        elif isinstance(agent, GameNodeAgent):
            agent_type = 'game_node'
        elif isinstance(agent, ObstacleAgent):
            agent_type = 'obstacle'

        agent_data.append({
            'id': agent.unique_id,
            'x': agent.pos[0] if agent.pos else None,
            'y': agent.pos[1] if agent.pos else None,
            'type': agent_type,
            'active': getattr(agent, 'active', None) # Send active status for game nodes
        })

    return jsonify({
        'day': model.current_day,
        'steps_today': model.steps_today,
        'grid': agent_data,
        'path': model.survivor.path # Send the survivor's current path
    })

@app.route('/api/reset', methods=['POST'])
def reset():
    global model
    model = SurvivalModel()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True)
