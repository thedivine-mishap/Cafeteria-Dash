# systems/inventory.py
class Inventory:
    def __init__(self):
        self.money = 100  # Starting cash
        # Raw Ingredients
        self.items = {
            "Rice": 0, "Egg": 0, "Veggie": 0, "Chicken": 0
        }
        
        # Cooked Food (Ready to serve)
        self.cooked_food = {
            "Fried Rice": 0, "Chicken Rice": 0, "Omelet": 0
        }

    def can_afford(self, cost):
        return self.money >= cost

    def buy(self, item, cost):
        if self.can_afford(cost):
            self.money -= cost
            self.items[item] += 1
            return True  # Purchase successful
        return False     # Not enough money