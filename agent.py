from mesa import Agent
import random
from collections import defaultdict
import heapq

# ===================================================================
# ### A* PATHFINDING UTILITY ###
# ===================================================================

def heuristic(a, b):
    """Calculates the Manhattan distance between two points."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def find_path_astar(model, start, goal):
    if not start or not goal:
        return None

    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor = (current[0] + dx, current[1] + dy)

            if not (0 <= neighbor[0] < model.grid.width and 0 <= neighbor[1] < model.grid.height):
                continue

            cell_contents = model.grid.get_cell_list_contents([neighbor])
            if any(isinstance(agent, ObstacleAgent) for agent in cell_contents):
                continue

            tentative_g_score = g_score.get(current, float('inf')) + 1
            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                if neighbor not in [i[1] for i in open_set]:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None

# ===================================================================
# ### AGENT CLASSES ###
# ===================================================================

def make_hashable_state(s):
    """Recursively converts a dictionary state into a hashable tuple."""
    if s is None: return None
    # This handles lists inside the dictionary's values, making the state fully hashable
    return tuple(sorted([(k, tuple(v) if isinstance(v, list) else v) for k, v in s.items()]))

class ObstacleAgent(Agent):
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.pos = None

    def step(self):
        pass

class SurvivorAgent(Agent):
    def __init__(self, unique_id, model, learning_rate=0.1, discount_factor=0.9, exploration_rate=1.0, q_table=None):
        self.unique_id = unique_id
        self.model = model
        self.pos = None
        self.score = 0
        self.mode = "NAVIGATING"
        self.path = []
        self.path_index = 0
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.epsilon_decay = 0.99
        self.epsilon_min = 0.05
        self.current_game_node = None
        self.game_state = None

        if q_table is not None:
            self.q_games = q_table
        else:
            self.q_games = defaultdict(lambda: defaultdict(float))

    def step(self):
        if self.mode == "NAVIGATING":
            self.navigate()
        elif self.mode == "PLAYING_GAME":
            self.play_game()

    def navigate(self):
        if self.pos:
            current_pos_contents = self.model.grid.get_cell_list_contents([self.pos])
            for agent in current_pos_contents:
                if isinstance(agent, GameNodeAgent) and agent.active:
                    self.start_game(agent)
                    return

        if not self.path or self.path_index >= len(self.path):
            self.find_new_path()

        if self.path and self.path_index < len(self.path):
            next_pos = self.path[self.path_index]
            self.model.grid.move_agent(self, next_pos)
            self.path_index += 1
        else:
            self.find_new_path()

    def find_new_path(self):
        self.path = []
        self.path_index = 0
        active_nodes = [agent for agent in self.model.agent_list if isinstance(agent, GameNodeAgent) and agent.active]

        if not active_nodes or not self.pos:
            self.wander()
            return

        nearest_node = min(active_nodes, key=lambda node: heuristic(self.pos, node.pos))
        path_to_node = find_path_astar(self.model, self.pos, nearest_node.pos)

        if path_to_node and len(path_to_node) > 1:
            self.path = path_to_node
            self.path_index = 1
        else:
            self.wander()

    def wander(self):
        if not self.pos: return
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        valid_neighbors = [n for n in neighbors if not any(isinstance(agent, (ObstacleAgent, GameNodeAgent)) for agent in self.model.grid.get_cell_list_contents(n))]
        if valid_neighbors:
            new_pos = self.model.random.choice(valid_neighbors)
            self.model.grid.move_agent(self, new_pos)

    def play_game(self):
        if not self.current_game_node or not self.game_state:
            self.mode = "NAVIGATING"
            return

        action = self.choose_game_action(self.game_state)
        result = self.current_game_node.submit_action(action)

        reward = result.get('reward', -1)
        self.score += reward

        next_state = self.current_game_node.get_game_state()
        self.learn_game(self.game_state, action, reward, next_state)
        self.game_state = next_state

        if result.get('complete', False):
            self.end_game(result.get('success', False))

    def choose_game_action(self, state):
        actions = self.current_game_node.get_possible_actions(state)
        if not actions: return None

        if self.model.random.random() < self.epsilon:
            return self.model.random.choice(actions)
        else:
            # CORRECTED: Use the same hashable state key for reading from the Q-table.
            state_key = make_hashable_state(state)
            q_values = {action: self.q_games[state_key][action] for action in actions}
            return max(q_values, key=q_values.get)

    def learn_game(self, state, action, reward, next_state):
        if action is None: return

        state_key = make_hashable_state(state)
        next_state_key = make_hashable_state(next_state)

        current_q = self.q_games[state_key][action]
        max_next_q = 0

        if next_state_key:
            next_actions = self.current_game_node.get_possible_actions(next_state)
            if next_actions:
                max_next_q = max(self.q_games[next_state_key].get(next_action, 0) for next_action in next_actions)

        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_games[state_key][action] = new_q

    def start_game(self, game_node):
        self.mode = "PLAYING_GAME"
        self.current_game_node = game_node
        self.game_state = game_node.start_game()
        self.model.last_game_name = ""
        self.model.last_game_result = ""

    def end_game(self, success):
        # CORRECTED: Fixed typo `current_game__node` to `current_game_node`
        self.model.record_game_result(self.current_game_node.game_type, success)
        self.model.complete_game_node(self.current_game_node, success)
        self.mode = "NAVIGATING"
        self.current_game_node = None
        self.game_state = None
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

class GameNodeAgent(Agent):
    GAME_TYPES = ['color_match', 'simon_says', 'sequence_memory', 'pattern_recognition']
    COLORS = ['red', 'green', 'blue', 'yellow', 'purple', 'orange']

    def __init__(self, unique_id, model, difficulty=1):
        self.unique_id = unique_id
        self.model = model
        self.pos = None
        self.active = False
        self.difficulty = max(1, min(difficulty, 3))
        self.game_type = self.model.random.choice(self.GAME_TYPES)
        self.game_state = {}

    def step(self):
        pass

    def start_game(self):
        self.active = True
        self.game_state = {'type': self.game_type}
        if self.game_type == 'color_match':
            self.game_state['target_color'] = self.model.random.choice(self.COLORS[:self.difficulty+1])
        elif self.game_type == 'simon_says':
            self.game_state['sequence'] = [self.model.random.choice(self.COLORS[:self.difficulty+1]) for _ in range(self.difficulty)]
            self.game_state['player_index'] = 0
        elif self.game_type == 'sequence_memory':
            self.game_state['sequence'] = [self.model.random.choice(self.COLORS[:self.difficulty+1]) for _ in range(self.difficulty + 1)]
            self.game_state['player_index'] = 0
        elif self.game_type == 'pattern_recognition':
            base_pattern = [self.model.random.choice(self.COLORS[:2]) for _ in range(2)]
            multiplier = (self.difficulty // 2) + 1
            self.game_state['sequence'] = base_pattern * multiplier
            if self.game_state['sequence']:
                self.game_state['correct_next'] = self.game_state['sequence'][0]
            else:
                self.game_state['sequence'] = base_pattern
                self.game_state['correct_next'] = self.game_state['sequence'][0]
        return self.get_game_state()

    def get_game_state(self):
        return self.game_state if self.active else None

    def get_possible_actions(self, game_state):
        if not game_state: return []
        return self.COLORS[:self.difficulty+1]

    def submit_action(self, action):
        if not self.active: return {'complete': True, 'success': False, 'reward': -10}
        reward = 0
        success = False
        complete = False

        if self.game_type == 'color_match':
            success = (action == self.game_state['target_color'])
            reward = self.difficulty * 5 if success else -self.difficulty * 2
            complete = True
        elif self.game_type == 'simon_says':
            seq = self.game_state['sequence']
            idx = self.game_state['player_index']
            if idx < len(seq) and action == seq[idx]:
                self.game_state['player_index'] += 1
                success = True
                if self.game_state['player_index'] >= len(seq):
                    reward = self.difficulty * 8
                    complete = True
                else:
                    reward = 2
            else:
                reward = -self.difficulty * 3
                complete = True
        elif self.game_type == 'sequence_memory':
            seq = self.game_state['sequence']
            idx = self.game_state['player_index']
            if idx < len(seq) and action == seq[idx]:
                self.game_state['player_index'] += 1
                success = True
                if self.game_state['player_index'] >= len(seq):
                    reward = self.difficulty * 10
                    complete = True
                else:
                    reward = 3
            else:
                reward = -self.difficulty * 4
                complete = True
        elif self.game_type == 'pattern_recognition':
            success = (action == self.game_state['correct_next'])
            reward = self.difficulty * 12 if success else -self.difficulty * 5
            complete = True

        return {'complete': complete, 'success': success, 'reward': reward}
