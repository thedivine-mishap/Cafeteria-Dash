# Cafeteria-Model-Simulation (Cafeteria Dash)

This project is a **Cafeteria Management Simulation Game** built in Python using Pygame. The system features both an interactive game mode where the user manually controls the cafeteria, and an automated simulation (experiment) mode designed for observing queue configurations, resource allocation, and overall efficiency over time.

## 🚀 Key Features
- **Interactive Gameplay:** Play manually by purchasing ingredients, deploying stoves, cooking meals, and serving customers before their patience runs out.
- **Queue System Simulator:** An automated `SimCustomer` and `SimKitchen` pipeline capable of accelerating time and testing varying parameters.
- **Experimentation Framework:** Allows parameter grid searches (number of queues vs number of stoves vs arrival rates) to find optimal configurations.
- **Data Analytics:** Exports simulation data to CSV and allows you to plot and analyze efficiency metrics with `pandas` and `numpy`.
- **Dynamic Metrics Tracker:** Real-time collection of game stats including wait times, revenue, ingredient costs, and lost customers.

## 🗂️ Project Architecture

The project is structured modularly:

- **`main.py`**: The entry point for the project holding the main game loop, UI interactions, sounds, and switching between interactive and simulation screens. 
- **`settings.py`**: Stores all global constants such as colors, UI sizing, game mechanics parameters (`ARRIVAL_RATE`, `PATIENCE_MEAN`), recipes, item prices, and the `SimConfig` dataclass for the simulation engine.
- **`assets/`**: Houses game assets such as sounds, fonts, and images. Also has a centralized script (`assets.py`) for management.
- **`entities/`**: Contains the visual sprites and interactive components for the `Customer`, `Player`, and `Food`.
- **`systems/`**: 
  - `kitchen.py`, `inventory.py`, `queue_system.py`: Manage core gameplay logic, stocking, and job scheduling.
  - `game_stats.py`: Metrics collector for both the interactive game and simulations.
  - `sound_manager.py`: Manages game sound effects and background music.
- **`simulation/`**: 
  - `simulator.py`: Contains a headless/accelerated version of the interactive game (`CafeteriaSimulator`) capable of running automated scenarios.
  - `experiment.py`, `analysis.py`: Handles parametric evaluations, plots statistics, and handles statistical generation.
- **`ui/`**: General user interface code, including buttons, heads-up display (`hud.py`), and the strategy summary screen.

## 🛠️ Gameplay Loop
1. **Buy Ingredients**: Restock Rice, Eggs, Veggies, or Chicken.
2. **Setup Kitchen**: You can buy extra stoves to cook multiple dishes simultaneously.
3. **Cook Meals**: Using ingredients, you can start cooking Fried Rice, Chicken Rice, or Omelets.
4. **Serve Customers**: Customers queue up randomly asking for specific dishes. Fulfilling orders makes money while failing to do so (patience drops) loses customers. The game ends after losing 5 customers or the time running out.

## ⚙️ How to Run the Project

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system. You will also need to install the required dependencies: `pygame`, `numpy`, and `pandas`.

Open your terminal or command prompt and run the following command to install the required libraries:

```bash
pip install pygame numpy pandas matplotlib
```

### 2. Launching the App
Navigate into the root directory of the project and execute `main.py`:

```bash
python main.py
```

### 3. Controls (Interactive Mode)
- **1/2/3/4**: Buy Rice / Egg / Veggie / Chicken.
- **R/C/O**: Cook Fried Rice / Chicken Rice / Omelet.
- **B**: Buy a new Stove.
- **SPACE**: Serve the first customer in the queue.
- **F11**: Toggle Fullscreen.

### 4. Running Simulations
1. On the Start screen, click **Simulation**.
2. Configure your test parameters using the `+` and `-` buttons (Stoves, Queues, Speed Multiplier, Restock Threshold, etc.).
3. Click **Start Experiment** to begin the automated runner.
4. Data will be automatically logged and available for analysis scripts upon completion.
