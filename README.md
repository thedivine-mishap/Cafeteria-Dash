restaurant_game/
│
├── main.py                 # Entry point, game loop
│
├── settings.py             # Constants (screen size, colors, rates)
├── assets.py               # Image & font loading (centralized)
│
├── entities/
│   ├── __init__.py
│   ├── player.py           # Restaurant owner sprite
│   ├── customer.py         # Customer sprite + patience
│   └── food.py             # Food / cooking tasks
│
├── systems/
│   ├── __init__.py
│   ├── inventory.py        # Groceries & food stock
│   ├── cooking.py          # Cooking slots & timers
│   ├── queue_system.py     # Customer arrival & service logic
│
├── ui/
│   ├── __init__.py
│   ├── button.py           # Clickable buttons
│   ├── hud.py              # Money, time, patience bars
│   └── screens.py          # Menu / game over screens
│
├── assets/
│   ├── images/
│   │   ├── player.png
│   │   ├── customer.png
│   │   ├── kitchen.png
│   │   └── food/
│   │       └── fried_rice.png
│   │
│   ├── fonts/
│   │   └── pixel.ttf
│   │
│   └── sounds/
│       ├── click.wav
│       └── serve.wav
│
└── README.md
