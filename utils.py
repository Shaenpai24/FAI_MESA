# Add this to agent.py or a new utils.py file
import heapq

def find_path_astar(model, start, goal):
    """
    Finds the shortest path from start to goal using the A* algorithm.
    The grid is accessed via the model to check for obstacles.
    """
    def heuristic(a, b):
        # Manhattan distance heuristic
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # The set of discovered nodes that may need to be (re-)expanded.
    # Initially, only the start node is known.
    # This is implemented as a priority queue.
    open_set = [(0, start)]  # (f_score, position)
    
    # For node n, came_from[n] is the node immediately preceding it on the cheapest path from start to n.
    came_from = {}
    
    # For node n, g_score[n] is the cost of the cheapest path from start to n.
    g_score = {start: 0}
    
    # For node n, f_score[n] = g_score[n] + heuristic(n, goal).
    f_score = {start: heuristic(start, goal)}

    while open_set:
        # Get the node in open_set having the lowest f_score value
        _, current = heapq.heappop(open_set)

        if current == goal:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]  # Return reversed path

        # Get neighbors
        x, y = current
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor = (x + dx, y + dy)
            
            # Check if neighbor is valid
            if not (0 <= neighbor[0] < model.grid.width and 0 <= neighbor[1] < model.grid.height):
                continue
            
            # Check for obstacles
            cell_contents = model.grid.get_cell_list_contents([neighbor])
            if any(isinstance(agent, ObstacleAgent) for agent in cell_contents):
                continue

            # tentative_g_score is the distance from start to the neighbor through current
            tentative_g_score = g_score[current] + 1
            
            if tentative_g_score < g_score.get(neighbor, float('inf')):
                # This path to neighbor is better than any previous one. Record it!
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                if neighbor not in [i[1] for i in open_set]:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return None # Path not found