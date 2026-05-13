import pygame

class Point:
    def __init__(self, x, y, data=None):
        self.x = x
        self.y = y
        self.data = data

class Rect:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, point):
        return (self.x - self.w <= point.x <= self.x + self.w and
                self.y - self.h <= point.y <= self.y + self.h)

    def intersects(self, range_rect):
        return not (range_rect.x - range_rect.w > self.x + self.w or
                    range_rect.x + range_rect.w < self.x - self.w or
                    range_rect.y - range_rect.h > self.y + self.h or
                    range_rect.y + range_rect.h < self.y - self.h)

class QuadTree:
    """
    Quadtree data structure for spatial partitioning.
    Used to optimize collision detection and spatial queries.
    """
    def __init__(self, boundary, capacity):
        self.boundary = boundary
        self.capacity = capacity
        self.points = []
        self.divided = False

    def subdivide(self):
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.w / 2
        h = self.boundary.h / 2

        ne = Rect(x + w, y - h, w, h)
        self.northeast = QuadTree(ne, self.capacity)
        nw = Rect(x - w, y - h, w, h)
        self.northwest = QuadTree(nw, self.capacity)
        se = Rect(x + w, y + h, w, h)
        self.southeast = QuadTree(se, self.capacity)
        sw = Rect(x - w, y + h, w, h)
        self.southwest = QuadTree(sw, self.capacity)

        self.divided = True

    def insert(self, point):
        if not self.boundary.contains(point):
            return False

        if len(self.points) < self.capacity:
            self.points.append(point)
            return True
        else:
            if not self.divided:
                self.subdivide()

            if self.northeast.insert(point): return True
            elif self.northwest.insert(point): return True
            elif self.southeast.insert(point): return True
            elif self.southwest.insert(point): return True

        return False

    def query(self, range_rect, found=None):
        if found is None:
            found = []

        if not self.boundary.intersects(range_rect):
            return found

        for p in self.points:
            if range_rect.contains(p):
                found.append(p)

        if self.divided:
            self.northwest.query(range_rect, found)
            self.northeast.query(range_rect, found)
            self.southwest.query(range_rect, found)
            self.southeast.query(range_rect, found)

        return found

    def render(self, screen, scale):
        """Draws the quadtree boundaries for visualization (minimap)."""
        x = (self.boundary.x - self.boundary.w) * scale
        y = (self.boundary.y - self.boundary.h) * scale
        w = (self.boundary.w * 2) * scale
        h = (self.boundary.h * 2) * scale
        pygame.draw.rect(screen, (100, 100, 100), (x, y, w, h), 1)

        if self.divided:
            self.northwest.render(screen, scale)
            self.northeast.render(screen, scale)
            self.southwest.render(screen, scale)
            self.southeast.render(screen, scale)
