from heapq import heappop, heappush

class Grid:
    def __init__(self, grid):
        self.grid = grid
        self.m = len(grid)
        self.n = len(grid[0])
        self.tile_info = [[(1, False) if tile==0 else (2, False) if tile==1 else (1, True) for tile in row] for row in grid]
    
    def in_bounds(self, tile):
        x, y = tile
        return 0 <= x < self.m and 0 <= y < self.n
    
    def cost(self, tile):
        x, y = tile
        return self.tile_info[y][x][0]

    def is_fire(self, tile):
        x, y = tile
        return self.tile_info[y][x][1]

def find_best_path(grid, agent_location, target_location):
    grid = Grid(grid)
    queue = []
    visited = set()
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up
    cost_to_reach = {agent_location: 0}
    parents = {agent_location: None}

    def heuristic(tile):  # Manhattan distance to the target adjusted by remaining movement points
        return (abs(tile[0] - target_location[0]) + abs(tile[1] - target_location[1])) * (5 - cost_to_reach[tile])
        
    heappush(queue, (0, agent_location))
    
    while queue:
        _, current_location = heappop(queue)

        if current_location in visited:
            continue
        visited.add(current_location)

        total_cost = cost_to_reach[current_location]
        
        if current_location == target_location:  # if target is reached, reconstruct the path
            path = []
            while current_location is not None:
                path.append(current_location)
                current_location = parents[current_location]
            return path[::-1]

        for dx, dy in directions:
            next_tile = (current_location[0] + dx, current_location[1] + dy)
            if grid.in_bounds(next_tile):  # within grid
                next_cost = total_cost + grid.cost(next_tile)
                if next_cost <= 5 and (next_tile not in cost_to_reach or next_cost < cost_to_reach[next_tile]):  # won't exceed movement range and is a better path
                    cost_to_reach[next_tile] = next_cost
                    parents[next_tile] = current_location
                    priority = next_cost + heuristic(next_tile) if not grid.is_fire(next_tile) else float('inf')  # set high priority to fire tiles
                    heappush(queue, (priority, next_tile))

    return None  # return None if no path found

# Test Case 1:
grid1 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 2, 2, 2, 2, 2, 2],
    [0, 0, 0, 0, 2, 0, 0, 0, 0, 2],
    [0, 0, 0, 0, 2, 2, 2, 2, 0, 2],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]
agent_location1 = (9, 9)
target_location1 = (7, 9)

# Test Case 2:
grid2 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 2, 2, 2, 2, 2, 0],
    [0, 0, 0, 0, 2, 0, 0, 0, 2, 0],
    [0, 0, 0, 0, 2, 0, 0, 0, 2, 0],
    [0, 0, 0, 0, 2, 2, 2, 2, 2, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]
agent_location2 = (4, 4)
target_location2 = (5, 5)

# Test Case 3:
grid3 = [
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
]
agent_location3 = (5, 5)
target_location3 = (1, 1)

print(find_best_path(grid1, agent_location1, target_location1))
print(find_best_path(grid2, agent_location2, target_location2))
print(find_best_path(grid3, agent_location3, target_location3))