import heapq
from typing import List, Tuple, Optional
from ftl_cli.models.base import Room, Ship

def get_neighbors(room: Room, all_rooms: List[Room]) -> List[Room]:
    """
    In a 2D grid of rooms, neighbors are rooms that share a wall.
    """
    neighbors = []
    for other in all_rooms:
        if other == room:
            continue

        # Check if rooms are adjacent
        # Simple adjacency: bounding boxes are adjacent
        # Horizontal adjacency
        if (room.x + room.w == other.x or other.x + other.w == room.x) and \
           (max(room.y, other.y) < min(room.y + room.h, other.y + other.h)):
            neighbors.append(other)
        # Vertical adjacency
        elif (room.y + room.h == other.y or other.y + other.h == room.y) and \
             (max(room.x, other.x) < min(room.x + room.w, other.x + other.w)):
            neighbors.append(other)

    return neighbors

def find_path(start: Room, goal: Room, all_rooms: List[Room]) -> Optional[List[Room]]:
    """
    A* algorithm to find path between rooms.
    """
    if start == goal:
        return [goal]

    frontier = []
    heapq.heappush(frontier, (0, id(start), start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while frontier:
        _, _, current = heapq.heappop(frontier)

        if current == goal:
            break

        for next_room in get_neighbors(current, all_rooms):
            new_cost = cost_so_far[current] + 1
            if next_room not in cost_so_far or new_cost < cost_so_far[next_room]:
                cost_so_far[next_room] = new_cost
                priority = new_cost + heuristic(goal, next_room)
                heapq.heappush(frontier, (priority, id(next_room), next_room))
                came_from[next_room] = current

    if goal not in came_from:
        return None

    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

def heuristic(a: Room, b: Room) -> float:
    (x1, y1) = a.center
    (x2, y2) = b.center
    return abs(x1 - x2) + abs(y1 - y2)
