"""Entry point for Braitenberg Vehicles simulation."""

import sys
from gui.app import App


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/vehicle_2a_fear.json"
    app = App(config_path)
    app.run()


if __name__ == "__main__":
    main()
