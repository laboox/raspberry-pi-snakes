from setuptools import find_packages, setup

setup(
    name="snake-game",
    version="1.0.0",
    description="Snake game for Raspberry Pi with LED matrix",
    author="Sina",
    packages=find_packages(),
    install_requires=[
        "pygame>=2.0.0",
        "adafruit-circuitpython-neopixel-spi>=1.0.0",
        "adafruit-blinka>=8.0.0",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "snake-game=snake.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
