"""
Daily Challenge Survival Simulation
A Solara web app for running multi-day AI agent challenges with 6-level games
"""

import solara
import solara.lab
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.patches as mpatches
import io
import threading
import time
from model import SurvivalModel, ObstacleAgent, GameNodeAgent, SurvivorAgent

matplotlib.use('Agg')

# ===================================================================
# ### MODEL & VISUALIZATION ###
# ===================================================================

def create_model(steps_per_day):
    return SurvivalModel(width=10, height=10, num_obstacles=5, steps_per_day=steps_per_day)

def get_grid_data(model):
    """Extracts visualization data from the model grid."""
    if not model:
        return np.zeros((10, 10)), []

    grid_data = np.zeros((model.height, model.width))
    path_data = []

    for cell in model.grid.coord_iter():
        content, (x, y) = cell
        # Correct y-coordinate for visualization (numpy array is y,x)
        vis_y = model.height - 1 - y

        if not model.grid.is_cell_empty((x,y)):
            for agent in content:
                if isinstance(agent, SurvivorAgent):
                    grid_data[vis_y, x] = 1 # Agent
                    if agent.path:
                        path_data = [(px, model.height - 1 - py) for px, py in agent.path]
                elif isinstance(agent, GameNodeAgent):
                    grid_data[vis_y, x] = 2 if agent.active else 4 # Active/Inactive Goal
                elif isinstance(agent, ObstacleAgent):
                    grid_data[vis_y, x] = 3 # Obstacle
    return grid_data, path_data

@solara.component
def ModelViewer(model, update_trigger):
    """Main model viewer using Matplotlib for a richer visualization."""
    if model is None:
        # CORRECTED: The correct component for an indeterminate circular progress is solara.Progress(value=False)
        with solara.Column(align="center"):
            solara.progress(value=False)
            solara.Text("Initializing Simulation...")
        return

    grid_data, path_data = get_grid_data(model)

    fig, ax = plt.subplots(figsize=(6, 6))
    colors = ['#FFFFFF', '#FF6347', '#32CD32', '#363636', '#FFD700']
    cmap = matplotlib.colors.ListedColormap(colors)
    ax.imshow(grid_data, cmap=cmap, vmin=0, vmax=4)

    # Plot the agent's path
    if path_data:
        path_x, path_y = zip(*path_data)
        ax.plot(path_x, path_y, color='#FF6347', linewidth=2, alpha=0.7, linestyle='--', marker='o', markersize=4)

    legend_elements = [
        mpatches.Patch(color='#FF6347', label='🤖 Agent'),
        mpatches.Patch(color='#32CD32', label='🎯 Active Goal'),
        mpatches.Patch(color='#FFD700', label='🎮 Inactive Goal'),
        mpatches.Patch(color='#363636', label='🚧 Obstacle'),
        mpatches.Patch(color='#FFFFFF', label='⬜ Empty'),
        mpatches.Patch(color='#FF6347', label='📈 Agent Path', alpha=0.5)
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
    ax.set_title(f"Day {model.current_day} - Step {model.steps_today}/{model.steps_per_day}", fontsize=14)
    ax.set_xticks([]), ax.set_yticks([])
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    solara.Image(buf.getvalue())
    plt.close(fig)

# ===================================================================
# ### UI COMPONENTS ###
# ===================================================================

@solara.component
def Controls(is_running, total_days, steps_per_day, on_start, on_stop, on_reset, on_step, on_days_change, on_steps_change):
    with solara.Card("🎮 Controls & Settings", margin=0):
        with solara.Column():
            with solara.Row(justify="space-around"):
                solara.Button("▶️ Start", on_click=on_start, color="primary", disabled=is_running)
                solara.Button("⏹️ Stop", on_click=on_stop, color="error", disabled=not is_running)
                solara.Button("🔄 Reset", on_click=on_reset, color="secondary", disabled=is_running)
                solara.Button("➡️ Step", on_click=on_step, color="info", disabled=is_running)

            solara.InputInt("Total Days:", value=total_days, on_value=on_days_change, disabled=is_running)
            solara.InputInt("Steps per Day:", value=steps_per_day, on_value=on_steps_change, disabled=is_running)

@solara.component
def AgentStatus(model):
    if not model:
        return
    survivor = model.survivor
    with solara.Card("🤖 Agent Status", margin=0, classes=["mt-4"]):
        solara.Markdown(f"""
        - **Current Score:** `{survivor.score}`
        - **Mode:** `{survivor.mode}`
        - **Epsilon (Exploration):** `{survivor.epsilon:.2f}`
        - **Current Position:** `{survivor.pos}`
        - **Path Length:** `{len(survivor.path)}`
        """)

@solara.component
def ResultsChart(model):
    if model is None or not model.daily_scores:
        with solara.Card("📈 Results", classes=["mt-4"]):
            solara.Info("Complete at least one day to see the charts!")
        return

    days, daily_scores, cumulative_scores = model.get_daily_stats()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.plot(days, daily_scores, 'b-o', label='Daily Score')
    ax1.set_title('Daily Scores')
    ax1.set_xlabel('Day'), ax1.set_ylabel('Score'), ax1.grid(True, alpha=0.4)
    ax2.plot(days, cumulative_scores, 'r-o', label='Cumulative Score')
    ax2.set_title('Cumulative Progress')
    ax2.set_xlabel('Day'), ax2.grid(True, alpha=0.4)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    with solara.Card("📈 Progress Charts", classes=["mt-4"]):
        solara.Image(buf.getvalue())
        summary_md = f"""
        - **Total Score:** `{sum(daily_scores)}`
        - **Average Daily Score:** `{np.mean(daily_scores):.1f}`
        - **Best Day Score:** `{max(daily_scores)}`
        """
        solara.Markdown(summary_md)
    plt.close(fig)

# ===================================================================
# ### MAIN PAGE LAYOUT ###
# ===================================================================

@solara.component
def Page():
    model, set_model = solara.use_state(None)
    total_days, set_total_days = solara.use_state(5)
    steps_per_day, set_steps_per_day = solara.use_state(50)
    sim_control = solara.use_ref({"running": False})
    update_trigger, set_update_trigger = solara.use_state(0)

    def initialize_model():
        set_model(create_model(steps_per_day))
    solara.use_effect(initialize_model, [steps_per_day])

    def run_simulation_thread():
        m = model
        while sim_control.current["running"] and m and m.current_day <= total_days:
            m.step()
            set_update_trigger(lambda x: x + 1)
            time.sleep(0.2) # Control simulation speed
        sim_control.current["running"] = False
        set_update_trigger(lambda x: x + 1)

    def start_simulation():
        if not sim_control.current["running"]:
            sim_control.current["running"] = True
            threading.Thread(target=run_simulation_thread, daemon=True).start()

    def stop_simulation():
        sim_control.current["running"] = False

    def reset_simulation():
        stop_simulation()
        set_model(create_model(steps_per_day))
        set_update_trigger(lambda x: x + 1)

    def step_simulation():
        if model and not sim_control.current["running"]:
            model.step()
            set_update_trigger(lambda x: x + 1)

    with solara.Head():
        solara.Title("Daily Challenge Survival Simulation")

    solara.Markdown("# 🤖 Daily Challenge Survival Simulation")
    solara.Markdown(
        "An AI agent navigates a grid to complete daily challenges. "
        "Each day presents new games with varying difficulty. The agent learns and adapts, trying to maximize its score."
    )

    with solara.Columns([2, 1]):
        with solara.Card("🗺️ Simulation Grid", margin=0):
            ModelViewer(model, update_trigger)

        with solara.Column():
            Controls(
                is_running=sim_control.current["running"],
                total_days=total_days,
                steps_per_day=steps_per_day,
                on_start=start_simulation,
                on_stop=stop_simulation,
                on_reset=reset_simulation,
                on_step=step_simulation,
                on_days_change=set_total_days,
                on_steps_change=set_steps_per_day
            )
            AgentStatus(model)

    ResultsChart(model)

# Running the app
Page()
