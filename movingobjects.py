class Grid:
    def __init__(self, size, objects):
        self.size = size
        self.grid = [[0]*size for _ in range(size)]
        for object, position in objects.items():
            x, y = position
            self.grid[x][y] = object

    def print_grid(self):
        for row in self.grid:
            print(' '.join(str(i) for i in row))
        print("\n---------------------\n")

    def move_objects(self, moves):
        object_positions = {self.grid[i][j]: (i, j) for i in range(self.size) for j in range(self.size) if self.grid[i][j] != 0}
        
        next_grid = [row[:] for row in self.grid]
        planned_moves = {}

        for object, (dx, dy) in moves.items():
            if object not in object_positions:
                raise ValueError(f"Object {object} not found in the grid")
            if abs(dx) > 1 or abs(dy) > 1:
                raise ValueError("Invalid move size")

            x, y = object_positions[object]
            dest_x, dest_y = x + dx, y + dy

            if dest_x < 0 or dest_x >= self.size or dest_y < 0 or dest_y >= self.size:
                continue

            planned_moves[(dest_x, dest_y)] = planned_moves.get((dest_x, dest_y), []) + [object]

        successful_moves = []
        blocked_moves = []
        for (dest_x, dest_y), objects in planned_moves.items():
            if len(objects) > 1 or self.grid[dest_x][dest_y] != 0:
                blocked_moves.extend(objects)
                continue

            object = objects[0]
            x, y = object_positions[object]
            next_grid[dest_x][dest_y] = object
            next_grid[x][y] = 0
            successful_moves.append(object)

        self.grid = next_grid
        self.print_grid()
        return successful_moves, blocked_moves

    def perform_moves(self, rounds_of_moves):
        for moves in rounds_of_moves:
            successful_moves, blocked_moves = self.move_objects(moves)
            print("Successful Moves:", successful_moves, "\nBlocked Moves:", blocked_moves)


# Case studies

# Case 1: Basic movement
grid = Grid(5, {1: (2, 2)})
grid.perform_moves([{1: (0, 1)}])

# Case 2: Moving to an occupied spot
grid = Grid(5, {1: (2, 2), 2: (2, 3)})
grid.perform_moves([{1: (0, 1), 2: (0, -1)}])
