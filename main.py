from sense_hat import SenseHat, stick
from dataclasses import dataclass
import enum
import time
import copy

sense = SenseHat()

WIDTH = 8
HEIGHT = 8
DARK = [0,0,0]
SNAKE = [0,0,255]


@dataclass
class Point:
    x: int
    y: int

class Dir(enum.IntEnum):
    left = 0
    right = 1
    up = 2
    down = 3

EVENT_TO_DIR = {
    stick.DIRECTION_UP: Dir.up,
    stick.DIRECTION_DOWN: Dir.down,
    stick.DIRECTION_LEFT: Dir.left,
    stick.DIRECTION_RIGHT: Dir.right,
}

def movePoint(point: Point, dir: Dir, reverse=False):
    inc = 1 if not reverse else -1
    match (dir):
        case Dir.left:
            point.x -= inc
        case Dir.right:
            point.x += inc
        case Dir.up:
            point.y -= inc
        case Dir.down:
            point.y += inc
    if point.x < 0:
        point.x += WIDTH
    if point.y < 0:
        point.y += HEIGHT
    point.x %= WIDTH
    point.y %= HEIGHT
    return point

class Snake:
    head: Point = Point(int(WIDTH/2), int(HEIGHT/2))
    bends: list[tuple[Point, Dir]] = []
    dir: Dir = Dir.left
    length: int = 4

    def step(self):
        self.head = movePoint(self.head, self.dir)

    def changeDir(self, new_dir: Dir):
        if (new_dir != dir):
            self.bends.append((self.head, dir))
            self.dir = new_dir

def drawSnake(snake: Snake):
    matrix = [DARK for i in range(64)]
    all_bends = snake.bends + [(snake.head, snake.dir)]
    rem = snake.length
    for headi in range(len(all_bends)-1,-1, -1):
        start = copy.deepcopy(all_bends[headi][0])
        end = None
        if headi > 0:
            end = all_bends[headi-1][0]
        dir = all_bends[headi][1]
        while((not end or start != end) and rem > 0):
            matrix[start.x + start.y*HEIGHT] = SNAKE
            start = movePoint(start, dir, reverse=True)
            rem -= 1
        if rem <=0:
            break
    sense.set_pixels(matrix)

if __name__ == "__main__":
    snake = Snake()
    while(True):
        events = sense.stick.get_events()
        if events:
            snake.changeDir(EVENT_TO_DIR[events[-1].direction])
        snake.step()
        drawSnake(snake)
        time.sleep(1)
