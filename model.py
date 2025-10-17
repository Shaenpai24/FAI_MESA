from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agent import SurvivorAgent, GameNodeAgent, ObstacleAgent
import collections
import random

def is_connected(model, start_pos, goal_pos):
    """
    Checks if a path exists from start to goal using Breadth-First Search (BFS).
    It avoids cells that contain an ObstacleAgent.
    """
    queue = collections.deque([start_pos])
    visited = {start_pos}
    width, height = model.grid.width, model.grid.height

    while queue:
        current_pos = queue.popleft()
        if current_pos == goal_pos:
            return True

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            if model.grid.out_of_bounds(next_pos):
                continue
            if next_pos not in visited:
                cell_contents = model.grid.get_cell_list_contents([next_pos])
                is_obstacle = any(isinstance(agent, ObstacleAgent) for agent in cell_contents)
                if not is_obstacle:
                    visited.add(next_pos)
                    queue.append(next_pos)
    return False

class SurvivalModel(Model):
    def __init__(self, width=10, height=10, num_obstacles=5, steps_per_day=50, total_days=10, seed=None, q_table=None):
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.steps_per_day = steps_per_day
        self.grid = MultiGrid(width, height, torus=False)
        self.running = True
        self.agent_list = []
        self._last_id = -1
        self.total_days = total_days
        self.last_game_name = ""
        self.last_game_result = ""
        self.current_day = 1
        self.daily_scores = []
        self.steps_today = 0
        self.total_score_history = [0]

        all_cells = [(x, y) for x in range(self.width) for y in range(self.height)]
        self.random.shuffle(all_cells)

        start_pos = all_cells.pop()
        # CORRECTED: Pass the q_table from the model to the agent
        self.survivor = SurvivorAgent(self.get_next_id(), self, q_table=q_table)
        self.agent_list.append(self.survivor)
        self.grid.place_agent(self.survivor, start_pos)

        goal_pos = all_cells.pop()
        initial_node = GameNodeAgent(self.get_next_id(), self, difficulty=1)
        self.agent_list.append(initial_node)
        self.grid.place_agent(initial_node, goal_pos)

        obstacles_placed = 0
        while obstacles_placed < num_obstacles and all_cells:
            pos = all_cells.pop()
            obstacle = ObstacleAgent(self.get_next_id(), self)
            self.grid.place_agent(obstacle, pos)
            if is_connected(self, start_pos, goal_pos):
                self.agent_list.append(obstacle)
                obstacles_placed += 1
            else:
                self.grid.remove_agent(obstacle)

        self.start_day()

        self.datacollector = DataCollector(
            model_reporters={
                "Score": lambda m: m.survivor.score if m.survivor else 0,
                "Day": lambda m: m.current_day,
                "StepsToday": lambda m: m.steps_today,
            }
        )

    def get_next_id(self):
        self._last_id += 1
        return self._last_id

    def start_day(self):
        self.steps_today = 0
        if self.survivor:
            self.survivor.path = []

        agents_to_remove = [a for a in self.agent_list if isinstance(a, GameNodeAgent)]
        for agent in agents_to_remove:
            if agent.pos: self.grid.remove_agent(agent)
            self.agent_list.remove(agent)

        num_games_today = self.random.choice([2, 3])
        for _ in range(num_games_today):
            difficulty = self.random.randint(1, 3)
            node = GameNodeAgent(self.get_next_id(), self, difficulty)
            self.agent_list.append(node)
            while True:
                x, y = self.random.randrange(self.width), self.random.randrange(self.height)
                if self.grid.is_cell_empty((x, y)):
                    self.grid.place_agent(node, (x, y))
                    break
        self.activate_random_game_node()

    def activate_random_game_node(self):
        inactive_nodes = [a for a in self.agent_list if isinstance(a, GameNodeAgent) and not a.active]
        if inactive_nodes:
            node_to_activate = self.random.choice(inactive_nodes)
            node_to_activate.active = True

    def complete_game_node(self, node, success):
        if node:
            node.active = False
        if success:
            self.activate_random_game_node()

    def record_game_result(self, game_type, success):
        self.last_game_name = game_type.replace('_', ' ').title()
        self.last_game_result = "Won" if success else "Lost"

    def step(self):
        if self.current_day > self.total_days:
            self.running = False
            return
        if self.steps_today >= self.steps_per_day:
            self.end_day()
            return
        for agent in list(self.agent_list):
            agent.step()
        self.steps_today += 1
        self.datacollector.collect(self)

    def end_day(self):
        current_total_score = self.survivor.score
        previous_total_score = sum(self.daily_scores)
        self.daily_scores.append(current_total_score - previous_total_score)
        self.total_score_history.append(self.survivor.score)
        self.current_day += 1
        if self.current_day <= self.total_days:
            self.start_day()
        else:
            self.running = False

    def get_daily_stats(self):
        days = list(range(1, len(self.daily_scores) + 1))
        return days, self.daily_scores, self.total_score_history[1:]
