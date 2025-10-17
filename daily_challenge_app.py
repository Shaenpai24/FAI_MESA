import streamlit as st
import pandas as pd
import random
from model import SurvivalModel
from collections import defaultdict
# ====================================================================
# ### AGENT VISUALIZATION ###
# ====================================================================

def agent_portrayal(agent):
    """Determines the appearance of each agent in the grid."""
    from agent import SurvivorAgent, GameNodeAgent, ObstacleAgent

    if isinstance(agent, SurvivorAgent):
        return {"Shape": "circle", "Color": "blue", "Filled": "true", "Layer": 1, "r": 0.8}
    elif isinstance(agent, GameNodeAgent):
        color = "lightgreen" if agent.active else "white"
        return {"Shape": "rect", "Color": color, "Filled": "true", "Layer": 0, "w": 1, "h": 1}
    elif isinstance(agent, ObstacleAgent):
        return {"Shape": "rect", "Color": "grey", "Filled": "true", "Layer": 0, "w": 1, "h": 1}
    return {}

# ====================================================================
# ### SESSION STATE MANAGEMENT ###
# ====================================================================

def initialize_session_state():
    """Initializes Streamlit session state variables if they don't exist."""
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'daily_scores_df' not in st.session_state:
        st.session_state.daily_scores_df = pd.DataFrame(columns=["Day", "Score"])
    # --- ADD THIS LINE ---
    if 'q_table' not in st.session_state:
        st.session_state.q_table = defaultdict(lambda: defaultdict(float))

def start_simulation(total_days, num_obstacles):
    """Creates a new model and starts the simulation."""
    # --- PASS THE Q_TABLE TO THE MODEL ---
    st.session_state.model = SurvivalModel(
        total_days=total_days,
        num_obstacles=num_obstacles,
        seed=random.randint(0, 10000),
        q_table=st.session_state.q_table  # Pass the persistent brain
    )
    st.session_state.simulation_running = True
    st.session_state.daily_scores_df = pd.DataFrame(columns=["Day", "Score"])

# ... (rest of app.py) ...
# Don't forget to call initialize_session_state() at the start!

def stop_simulation():
    """Stops the simulation."""
    st.session_state.simulation_running = False

def run_simulation_step():
    """Runs one step of the model and updates the graph data."""
    if st.session_state.model and st.session_state.simulation_running:
        st.session_state.model.step()
        if not st.session_state.model.running:
            st.session_state.simulation_running = False

        days, scores, _ = st.session_state.model.get_daily_stats()
        if days and scores:
            df = pd.DataFrame({"Day": days, "Score": scores})
            st.session_state.daily_scores_df = df

# ====================================================================
# ### STREAMLIT UI ###
# ====================================================================

st.set_page_config(layout="wide", page_title="Daily Challenge Survivor")
initialize_session_state()

st.title("Daily Challenge Survivor Simulation")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Simulation Controls")

    total_days = st.number_input("Total Days", min_value=1, value=10, key="total_days_input")
    num_obstacles = st.slider("Number of Obstacles", min_value=0, max_value=50, value=10, key="obstacle_slider")

    if not st.session_state.simulation_running:
        if st.button("Start Simulation"):
            start_simulation(total_days, num_obstacles)
            st.rerun()
    else:
        if st.button("Stop Simulation"):
            stop_simulation()
            st.rerun()

# --- Main Content Area ---
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Agent Grid")
    grid_canvas = st.empty()

with col2:
    st.header("Status & Scores")
    score_display = st.empty()
    game_status_display = st.empty()
    chart_display = st.empty()

# --- Main Loop ---
if st.session_state.simulation_running:
    run_simulation_step()

if st.session_state.model:
    # NEW, ROBUST VISUALIZATION LOGIC
    grid_state = []
    for agent in st.session_state.model.agent_list:
        if agent.pos is not None:
            portrayal = agent_portrayal(agent)
            portrayal['x'] = agent.pos[0]
            portrayal['y'] = agent.pos[1]
            grid_state.append(portrayal)

    # Represent the grid with a Pandas DataFrame for text-based visualization
    grid_df = pd.DataFrame([['.' for _ in range(st.session_state.model.width)] for _ in range(st.session_state.model.height)])
    for item in grid_state:
        char = '.'
        if item['Shape'] == 'circle': char = 'S' # Survivor
        elif item['Shape'] == 'rect' and item['Color'] == 'grey': char = "\U0001F480" # Obstacle
        elif item['Shape'] == 'rect' and item['Color'] == 'lightgreen': char = "\U00002B50" # Game
        if 0 <= item['y'] < len(grid_df.index) and 0 <= item['x'] < len(grid_df.columns):
            grid_df.iloc[item['y'], item['x']] = char

    with grid_canvas.container():
        st.dataframe(grid_df, use_container_width=True)

    # Update Status Display
    score = st.session_state.model.survivor.score if st.session_state.model.survivor else 0
    game_name = st.session_state.model.last_game_name
    game_result = st.session_state.model.last_game_result

    with score_display.container():
        st.metric("Total Score", score)

    with game_status_display.container():
        if game_name:
            st.write(f"**Last Game:** {game_name}")
            st.write(f"**Result:** {game_result}")
        else:
            st.write("Survivor is navigating...")

    # Update Chart Display
    with chart_display.container():
        st.write("**Daily Scores**")
        if not st.session_state.daily_scores_df.empty:
            st.bar_chart(st.session_state.daily_scores_df.set_index('Day'))
        else:
            st.write("No data yet.")

    # Rerun to create animation loop
    if st.session_state.simulation_running:
        st.rerun()
else:
    with grid_canvas.container():
        st.write("Simulation not started. Configure settings in the sidebar and click 'Start Simulation'.")
initialize_session_state()
