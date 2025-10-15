# Daily Challenge Survival Simulation

A Mesa-based AI agent simulation with Q-learning for daily survival challenges featuring 6-level games.

## 🎯 Features

- **Daily Challenge System**: Limited steps per day, multiple days of gameplay
- **6-Level Games**: Each goal node has 6 increasing difficulty levels
- **Smart AI Agent**: Uses advanced Q-learning with obstacle avoidance and anti-loop systems
- **Progress Tracking**: Visual charts showing improvement over time
- **Web Interface**: Beautiful Solara-based visualization

## 📁 Project Structure

Only 3 files total:
- `agent.py`: AI agents with Q-learning and game logic
- `model.py`: Simulation model with daily tracking
- `daily_challenge_app.py`: Main web application

## 🚀 Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the web app:**
```bash
solara run daily_challenge_app.py
```

3. **Open your browser to:** http://localhost:8765

## 🎮 How It Works

### Daily Challenge System
- Each day has limited steps (configurable 50-200 steps)
- Agent must reach goal nodes and complete 6 levels of games
- Higher difficulty = more points per level
- Track progress across multiple days

### AI Learning Features
- **Smart Navigation**: Avoids obstacles, learns optimal paths
- **Anti-Loop System**: Prevents getting stuck in repetitive movements
- **Progressive Learning**: Epsilon decay for exploration vs exploitation
- **Rich State Representation**: Detailed environment understanding

### Scoring System
- **Level Points**: `current_level × difficulty × 10`
- **Example**: Level 3, Difficulty 4 = 120 points
- **Daily Tracking**: Monitor improvement over time

## 📊 Visualization Features

- **Live Grid**: Real-time agent movement and environment
- **Progress Charts**: Daily scores and cumulative progress
- **Performance Stats**: Epsilon, score, mode tracking
- **Interactive Controls**: Start/stop, reset, step-by-step

## ⚙️ Configuration

Adjust settings in the web interface:
- **Total Days**: 1-20 days of simulation
- **Steps per Day**: 50-200 steps challenge
- **Grid Size**: 15x15 with 8 obstacles and 3 game nodes

## 🧠 AI Agent Details

The survivor agent uses advanced Q-learning:
- **State Space**: Direction, distance, obstacles, loop detection
- **Actions**: Smart navigation with obstacle avoidance
- **Rewards**: +2 for progress, +50 for reaching goals, penalties for loops
- **Learning**: Adaptive exploration with memory systems