from __future__ import annotations

import arcade
from dataclasses import dataclass
import random
import math
import shapely

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "RealSim"
NUM_LINES = 3
NUM_CIRCLES = 5

@dataclass
class Point:
    x: int
    y: int


def intersect(l1, l2):
    p1 = l1.a
    p2 = l1.b
    p3 = l2.a
    p4 = l2.b
    x1,y1 = p1.x, p1.y
    x2,y2 = p2.x, p2.y
    x3,y3 = p3.x, p3.y
    x4,y4 = p4.x, p4.y
    denom = (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)
    if denom == 0: # parallel
        return None
    ua = ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) / denom
    if ua < 0 or ua > 1: # out of range
        return None
    ub = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) / denom
    if ub < 0 or ub > 1: # out of range
        return None
    x = x1 + ua * (x2-x1)
    y = y1 + ua * (y2-y1)
    return Point(x,y)


@dataclass
class Line:
    a: Point
    b: Point

    def draw(self, color=arcade.color.DARK_JUNGLE_GREEN) -> None:
        arcade.draw_line(self.a.x, self.a.y, self.b.x, self.b.y, color)

    def check_collision(self, ray: Line) -> Point | None:
        p1 = self.a
        p2 = self.b
        p3 = ray.a
        p4 = ray.b
        x1,y1 = p1.x, p1.y
        x2,y2 = p2.x, p2.y
        x3,y3 = p3.x, p3.y
        x4,y4 = p4.x, p4.y
        denom = (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)
        if denom == 0: # parallel
            return None
        ua = ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) / denom
        if ua < 0 or ua > 1: # out of range
            return None
        ub = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) / denom
        if ub < 0 or ub > 1: # out of range
            return None
        x = x1 + ua * (x2-x1)
        y = y1 + ua * (y2-y1)
        return Point(x,y)


@dataclass
class Circle:
    center: Point
    radius: float

    def draw(self) -> None:
        arcade.draw_circle_outline(
            self.center.x,
            self.center.y,
            self.radius,
            color=arcade.color.DARK_JUNGLE_GREEN
        )

    def check_collision(self, ray: Line) -> list[Point] | None:
        P0 = Point(ray.a.x, ray.a.y)
        D = Point(ray.b.x - ray.a.x, ray.b.y - ray.a.y)
        A = D.x ** 2 + D.y ** 2
        B = 2 * (D.x * (P0.x - self.center.x) + D.y * (P0.y - self.center.y))
        C = (P0.x - self.center.x) ** 2 + (P0.y - self.center.y) ** 2 - self.radius ** 2
        discriminant = B ** 2 - 4 * A * C

        intersections = []

        if A == 0:
            return intersections

        if discriminant == 0:  # One solution
            t = -B / (2*A)
            if t >= 0:
                intersections.append(Point(P0.x + t * D.x, P0.y + t * D.y))
        elif discriminant > 0:
            t1 = (-B + discriminant ** 0.5) / (2 * A)
            t2 = (-B - discriminant ** 0.5) / (2 * A)

            if t1 >= 0:
                intersections.append(Point(P0.x + t1 * D.x, P0.y + t1 * D.y))
                intersections.append(Point(P0.x + t2 * D.x, P0.y + t2 * D.y))

        return intersections


def generate_lines() -> list[Line]:
    lines = []

    for _ in range(NUM_LINES):
        start_x = random.randint(0, SCREEN_WIDTH)
        start_y = random.randint(0, SCREEN_HEIGHT)
        end_x = random.randint(0, SCREEN_WIDTH)
        end_y = random.randint(0, SCREEN_HEIGHT)
        lines.append(Line(Point(start_x, start_y), Point(end_x, end_y)))
    
    return lines


def generate_circles() -> list[Circle]:
    circles = []

    for _ in range(NUM_CIRCLES):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        radius = random.randint(30, 60)
        circles.append(Circle(Point(x, y), radius))
    
    return circles


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)

        arcade.set_background_color(arcade.color.LIGHT_GRAY)

    def setup(self):
        """ Set up the game variables. Call to re-start the game. """
        arcade.enable_timings()

        self.mouse_position = Point(0, 0)
        self.lines = generate_lines()
        self.circles = generate_circles()

        self.ray_hits = []

    def on_draw(self):
        """
        Render the screen.
        """
        self.clear()

        for line in self.lines:
            line.draw()
        
        for circle in self.circles:
            circle.draw()

        for line in self.ray_hits:
            line.draw(arcade.color.ORANGE)
        
        for d in self.debug:
            arcade.draw_circle_filled(d.x, d.y, 3, arcade.color.RED)

        
    def on_update(self, delta_time):
        """
        All the logic to move, and the game logic goes here.
        Normally, you'll call update() on the sprite lists that
        need it.
        """
        self.ray_hits = []

        self.debug = []

        rays = []

        # to bottom
        for x in range(SCREEN_WIDTH):
            rays.append(Line(self.mouse_position, Point(x, 0)))
            rays.append(Line(self.mouse_position, Point(x, SCREEN_HEIGHT)))
        
        for y in range(SCREEN_HEIGHT):
            rays.append(Line(self.mouse_position, Point(0, y)))
            rays.append(Line(self.mouse_position, Point(SCREEN_WIDTH, y)))

        for ray in rays:
            single_ray_hits = []

            for line in self.lines:
                hit = line.check_collision(ray)
                if hit:
                    single_ray_hits.append(
                        Line(self.mouse_position, hit)
                    )
            
            for circle in self.circles:
                hit = circle.check_collision(ray)
                if hit:
                    for hit_points in hit:
                        single_ray_hits.append(
                            Line(self.mouse_position, hit_points)
                        )


            single_ray_hits = sorted(single_ray_hits, key=lambda x: math.dist(
                (x.a.x, x.a.y), (x.b.x, x.b.y)
            ))

            if single_ray_hits:
                self.ray_hits.append(single_ray_hits[0])
        
        # TODO: store normal

        arcade.print_timings()


    def on_key_press(self, key, key_modifiers):
        """
        Called whenever a key on the keyboard is pressed.

        For a full list of keys, see:
        https://api.arcade.academy/en/latest/arcade.key.html
        """
        pass

    def on_key_release(self, key, key_modifiers):
        """
        Called whenever the user lets off a previously pressed key.
        """
        pass

    def on_mouse_motion(self, x, y, delta_x, delta_y):
        self.mouse_position = Point(int(x), int(y))

    def on_mouse_press(self, x, y, button, key_modifiers):
        """
        Called when the user presses a mouse button.
        """
        pass

    def on_mouse_release(self, x, y, button, key_modifiers):
        """
        Called when a user releases a mouse button.
        """
        pass


def main():
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()