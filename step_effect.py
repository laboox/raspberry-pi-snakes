from led_map import MAP, PORTALS
import neopixel_spi as neopixel
import board
import time
import RPi.GPIO as GPIO

WIDTH = len(MAP[0])
HEIGHT = len(MAP)
BUTTON_PIN = 8
COLORS = [
    (0, 0, 255),
    (127, 0, 255),
    (255, 0, 255),
    (255, 0, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 255, 127),
    (0, 127, 255),
]
current_color = 0

NUM_PIXELS = 100
PIXEL_ORDER = neopixel.GRB
spi = board.SPI()
pixels = neopixel.NeoPixel_SPI(
    spi, NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False
)

def draw_effect(height=0, color=(0, 0, 255)):
    """Draws the game board in the console."""
    matrix = [(0, 0, 0)] * NUM_PIXELS
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if y >= HEIGHT-1-height:
                matrix[MAP[y][x]] = (0, 0, 0)
            else:
                matrix[MAP[y][x]] = color
    
    for i in range(NUM_PIXELS):
            pixels[i] = matrix[i]
    pixels.show()

def draw_step_effect(interval=0.02):
    global current_color

    print("Drawing step effect")

    for i in range(HEIGHT-1, -1, -1):
        draw_effect(i, COLORS[current_color])
        time.sleep(interval)
    current_color = (current_color + 1) % len(COLORS)
    print("Current color: ", current_color)

if __name__ == "__main__":
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    low = True
    while True: # Run forever
        if GPIO.input(BUTTON_PIN) == GPIO.HIGH and low:
            print("Button was pushed!")
            draw_step_effect()
            low = False
        elif GPIO.input(BUTTON_PIN) == GPIO.LOW:
            low = True