import random

class Leaf:
    """
    Represents a space partition in the Binary Space Partitioning (BSP) algorithm.
    Used to generate rooms and hallways in a random but logical manner.
    """

    def __init__(self, x, y, width, height):
        """Initializes a leaf node with specific coordinates and dimensions."""
        self.x, self.y, self.width, self.height = x, y, width, height
        self.MIN_LEAF_SIZE = 6
        self.leftChild, self.rightChild, self.room = None, None, None
        self.halls = []

    def split(self):
        """Performs a binary split of the leaf into two child nodes (left and right)."""
        if self.leftChild is not None or self.rightChild is not None: return False
        splitH = random.random() > 0.5
        if self.width > self.height and self.width / self.height >= 1.25: splitH = False
        elif self.height > self.width and self.height / self.width >= 1.25: splitH = True

        max_size = (self.height if splitH else self.width) - self.MIN_LEAF_SIZE
        if max_size <= self.MIN_LEAF_SIZE: return False

        split = random.randint(self.MIN_LEAF_SIZE, max_size)        
        if splitH:
            self.leftChild = Leaf(self.x, self.y, self.width, split)
            self.rightChild = Leaf(self.x, self.y + split, self.width, self.height - split)
        else:
            self.leftChild = Leaf(self.x, self.y, split, self.height)
            self.rightChild = Leaf(self.x + split, self.y, self.width - split, self.height)
        return True

    def create_rooms(self):
        """Generates rooms within leaf boundaries and connects them via hallways."""
        if self.leftChild is not None or self.rightChild is not None:
            if self.leftChild is not None: self.leftChild.create_rooms()
            if self.rightChild is not None: self.rightChild.create_rooms()
            if self.leftChild is not None and self.rightChild is not None:
                self.create_hall(self.leftChild.get_room(), self.rightChild.get_room())
        else:
            roomSize = (random.randint(3, self.width - 2), random.randint(3, self.height - 2))
            roomPos = (random.randint(1, self.width - roomSize[0] - 1), random.randint(1, self.height - roomSize[1] - 1))
            self.room = (self.x + roomPos[0], self.y + roomPos[1], roomSize[0], roomSize[1])

    def get_room(self):
        """Retrieves room data from the current leaf or its descendants."""
        if self.room is not None: return self.room
        lRoom = self.leftChild.get_room() if self.leftChild else None
        rRoom = self.rightChild.get_room() if self.rightChild else None
        if not lRoom and not rRoom: return None
        if not rRoom: return lRoom
        if not lRoom: return rRoom
        return lRoom if random.random() > 0.5 else rRoom

    def create_hall(self, l, r):
        """Creates a hallway connecting two rooms l and r."""
        point1 = (random.randint(l[0], l[0] + l[2] - 1), random.randint(l[1], l[1] + l[3] - 1))
        point2 = (random.randint(r[0], r[0] + r[2] - 1), random.randint(r[1], r[1] + r[3] - 1))
        if random.random() > 0.5:
            self.halls.append((point1[0], point1[1], abs(point2[0] - point1[0]) + 1, 1) if point2[0] > point1[0] else (point2[0], point1[1], abs(point2[0] - point1[0]) + 1, 1))
            self.halls.append((point2[0], point1[1], 1, abs(point2[1] - point1[1]) + 1) if point2[1] > point1[1] else (point2[0], point2[1], 1, abs(point2[1] - point1[1]) + 1))
        else:
            self.halls.append((point1[0], point1[1], 1, abs(point2[1] - point1[1]) + 1) if point2[1] > point1[1] else (point1[0], point2[1], 1, abs(point2[1] - point1[1]) + 1))
            self.halls.append((point1[0], point2[1], abs(point2[0] - point1[0]) + 1, 1) if point2[0] > point1[0] else (point2[0], point2[1], abs(point2[0] - point1[0]) + 1, 1))

def generate_dungeon(rows, cols):
    """
    Main function to generate a random dungeon using the BSP algorithm.
    Returns:
        tuple: (grid, spawn_room, all_rooms)
    """
    grid = [[1 for _ in range(cols)] for _ in range(rows)]
    leaves = []
    root = Leaf(0, 0, cols, rows)
    leaves.append(root)

    did_split = True
    while did_split:
        did_split = False
        for l in leaves:
            if l.leftChild is None and l.rightChild is None:        
                if l.width > 10 or l.height > 10 or random.random() > 0.25:
                    if l.split():
                        leaves.append(l.leftChild); leaves.append(l.rightChild)
                        did_split = True
    root.create_rooms()

    def fill_grid(leaf):
        if leaf.room is not None:
            x, y, w, h = leaf.room
            for i in range(y, y + h):
                for j in range(x, x + w): grid[i][j] = 0
        for h_x, h_y, h_w, h_h in leaf.halls:
            for i in range(h_y, h_y + h_h):
                for j in range(h_x, h_x + h_w):
                    if 0 <= i < rows and 0 <= j < cols: grid[i][j] = 0
        if leaf.leftChild: fill_grid(leaf.leftChild)
        if leaf.rightChild: fill_grid(leaf.rightChild)

    fill_grid(root)
    all_rooms = []
    def get_all_rooms(leaf):
        if leaf.room: all_rooms.append(leaf.room)
        if leaf.leftChild: get_all_rooms(leaf.leftChild)
        if leaf.rightChild: get_all_rooms(leaf.rightChild)
    get_all_rooms(root)
    return grid, root.get_room(), all_rooms
