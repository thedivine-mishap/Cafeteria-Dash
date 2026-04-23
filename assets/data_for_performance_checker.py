# Dummy Data for Cafeteria Simulation
# This file contains test data for development and testing purposes

# Test data for customers
test_customers = [
    {"id": 1, "name": "Alice Johnson", "arrival_time": 8.5,
        "patience": 10.0, "budget": 15.50},
    {"id": 2, "name": "Bob Smith", "arrival_time": 8.7,
        "patience": 8.5, "budget": 12.00},
    {"id": 3, "name": "Charlie Brown", "arrival_time": 8.9,
        "patience": 12.0, "budget": 20.00},
    {"id": 4, "name": "Diana Prince", "arrival_time": 9.1,
        "patience": 9.0, "budget": 18.75},
    {"id": 5, "name": "Edward Norton", "arrival_time": 9.3,
        "patience": 11.0, "budget": 16.25},
    {"id": 6, "name": "Fiona Apple", "arrival_time": 9.5,
        "patience": 7.5, "budget": 13.00},
    {"id": 7, "name": "George Miller", "arrival_time": 9.7,
        "patience": 10.5, "budget": 19.50},
    {"id": 8, "name": "Hannah Montana", "arrival_time": 9.9,
        "patience": 8.0, "budget": 14.75},
    {"id": 9, "name": "Isaac Newton", "arrival_time": 10.1,
        "patience": 9.5, "budget": 17.00},
    {"id": 10, "name": "Julia Roberts", "arrival_time": 10.3,
        "patience": 11.5, "budget": 21.00},
    {"id": 11, "name": "Kevin Hart", "arrival_time": 10.5,
        "patience": 6.5, "budget": 11.00},
    {"id": 12, "name": "Laura Palmer", "arrival_time": 10.7,
        "patience": 10.0, "budget": 15.75},
    {"id": 13, "name": "Michael Jordan", "arrival_time": 10.9,
        "patience": 12.5, "budget": 22.50},
    {"id": 14, "name": "Nicole Kidman", "arrival_time": 11.1,
        "patience": 8.5, "budget": 18.00},
    {"id": 15, "name": "Oscar Wilde", "arrival_time": 11.3,
        "patience": 9.0, "budget": 16.50},
    {"id": 16, "name": "Patricia Houston",
        "arrival_time": 11.5, "patience": 7.0, "budget": 12.50},
    {"id": 17, "name": "Quincy Jones", "arrival_time": 11.7,
        "patience": 11.0, "budget": 19.75},
    {"id": 18, "name": "Rachel Green", "arrival_time": 11.9,
        "patience": 9.5, "budget": 17.50},
    {"id": 19, "name": "Samuel Jackson", "arrival_time": 12.1,
        "patience": 10.5, "budget": 20.25},
    {"id": 20, "name": "Taylor Swift", "arrival_time": 12.3,
        "patience": 8.0, "budget": 13.75},
    {"id": 21, "name": "Uma Thurman", "arrival_time": 12.5,
        "patience": 11.5, "budget": 21.50},
    {"id": 22, "name": "Victor Hugo", "arrival_time": 12.7,
        "patience": 9.0, "budget": 18.50},
    {"id": 23, "name": "Wendy Williams", "arrival_time": 12.9,
        "patience": 7.5, "budget": 14.00},
    {"id": 24, "name": "Xavier Dolan", "arrival_time": 13.1,
        "patience": 10.0, "budget": 16.00},
    {"id": 25, "name": "Yvonne Strahovski",
        "arrival_time": 13.3, "patience": 12.0, "budget": 23.00},
]

# Test data for food items
test_food_items = [
    {"id": 1, "name": "Burger", "price": 8.50,
        "cook_time": 3.5, "stock": 50, "calories": 520},
    {"id": 2, "name": "Pizza Slice", "price": 5.00,
        "cook_time": 2.0, "stock": 60, "calories": 285},
    {"id": 3, "name": "Salad", "price": 6.50,
        "cook_time": 1.5, "stock": 40, "calories": 150},
    {"id": 4, "name": "Pasta", "price": 7.00,
        "cook_time": 4.0, "stock": 35, "calories": 380},
    {"id": 5, "name": "Sandwich", "price": 5.50,
        "cook_time": 2.5, "stock": 45, "calories": 320},
    {"id": 6, "name": "Tacos", "price": 6.00,
        "cook_time": 3.0, "stock": 30, "calories": 280},
    {"id": 7, "name": "Fried Chicken", "price": 9.00,
        "cook_time": 4.5, "stock": 25, "calories": 450},
    {"id": 8, "name": "Fish and Chips", "price": 8.00,
        "cook_time": 3.5, "stock": 20, "calories": 520},
    {"id": 9, "name": "Soup", "price": 4.50,
        "cook_time": 2.0, "stock": 50, "calories": 180},
    {"id": 10, "name": "Rice Bowl", "price": 5.50,
        "cook_time": 2.5, "stock": 40, "calories": 400},
]

# Test data for queue operations
queue_test_data = [
    {"timestamp": 8.5, "action": "join_queue", "customer_id": 1},
    {"timestamp": 8.7, "action": "join_queue", "customer_id": 2},
    {"timestamp": 8.9, "action": "join_queue", "customer_id": 3},
    {"timestamp": 9.1, "action": "join_queue", "customer_id": 4},
    {"timestamp": 9.3, "action": "join_queue", "customer_id": 5},
    {"timestamp": 9.5, "action": "order_placed", "customer_id": 1, "item_id": 1},
    {"timestamp": 9.7, "action": "order_placed", "customer_id": 2, "item_id": 2},
    {"timestamp": 9.9, "action": "order_placed", "customer_id": 3, "item_id": 3},
    {"timestamp": 10.1, "action": "order_placed", "customer_id": 4, "item_id": 1},
    {"timestamp": 10.3, "action": "order_placed", "customer_id": 5, "item_id": 4},
    {"timestamp": 10.5, "action": "order_completed", "customer_id": 1},
    {"timestamp": 10.7, "action": "order_completed", "customer_id": 2},
    {"timestamp": 10.9, "action": "order_completed", "customer_id": 3},
    {"timestamp": 11.1, "action": "left_queue", "customer_id": 6},
    {"timestamp": 11.3, "action": "join_queue", "customer_id": 7},
    {"timestamp": 11.5, "action": "join_queue", "customer_id": 8},
    {"timestamp": 11.7, "action": "order_placed", "customer_id": 4, "item_id": 2},
    {"timestamp": 11.9, "action": "order_placed", "customer_id": 5, "item_id": 5},
    {"timestamp": 12.1, "action": "order_completed", "customer_id": 4},
    {"timestamp": 12.3, "action": "order_completed", "customer_id": 5},
]

# Test data for metrics
metrics_test_data = [
    {"metric_name": "queue_length", "value": 5, "timestamp": 8.5},
    {"metric_name": "average_wait_time", "value": 3.2, "timestamp": 8.7},
    {"metric_name": "customer_satisfaction", "value": 0.82, "timestamp": 8.9},
    {"metric_name": "food_quality_score", "value": 4.5, "timestamp": 9.1},
    {"metric_name": "service_speed", "value": 2.8, "timestamp": 9.3},
    {"metric_name": "inventory_utilization", "value": 0.65, "timestamp": 9.5},
    {"metric_name": "revenue_per_hour", "value": 145.50, "timestamp": 9.7},
    {"metric_name": "peak_queue_length", "value": 12, "timestamp": 9.9},
    {"metric_name": "orders_completed", "value": 18, "timestamp": 10.1},
    {"metric_name": "repeat_customers", "value": 7, "timestamp": 10.3},
    {"metric_name": "average_order_value", "value": 6.75, "timestamp": 10.5},
    {"metric_name": "stock_depletion_rate", "value": 0.35, "timestamp": 10.7},
    {"metric_name": "cook_efficiency", "value": 0.78, "timestamp": 10.9},
    {"metric_name": "customer_churn", "value": 0.15, "timestamp": 11.1},
    {"metric_name": "total_revenue", "value": 287.50, "timestamp": 11.3},
]

# Test data for cooking operations
cooking_test_data = [
    {"recipe_id": 1, "name": "Burger", "ingredients": [
        "bun", "patty", "lettuce", "tomato"], "steps": 4, "time": 3.5},
    {"recipe_id": 2, "name": "Pizza Slice", "ingredients": [
        "dough", "sauce", "cheese"], "steps": 3, "time": 2.0},
    {"recipe_id": 3, "name": "Salad", "ingredients": [
        "lettuce", "tomato", "cucumber", "dressing"], "steps": 2, "time": 1.5},
    {"recipe_id": 4, "name": "Pasta", "ingredients": [
        "pasta", "sauce", "cheese"], "steps": 4, "time": 4.0},
    {"recipe_id": 5, "name": "Sandwich", "ingredients": [
        "bread", "ham", "cheese", "lettuce"], "steps": 3, "time": 2.5},
    {"recipe_id": 6, "name": "Tacos", "ingredients": [
        "tortilla", "meat", "salsa", "cheese"], "steps": 3, "time": 3.0},
    {"recipe_id": 7, "name": "Fried Chicken", "ingredients": [
        "chicken", "flour", "oil"], "steps": 5, "time": 4.5},
    {"recipe_id": 8, "name": "Fish and Chips", "ingredients": [
        "fish", "potatoes", "oil", "batter"], "steps": 5, "time": 3.5},
    {"recipe_id": 9, "name": "Soup", "ingredients": [
        "broth", "vegetables", "seasoning"], "steps": 3, "time": 2.0},
    {"recipe_id": 10, "name": "Rice Bowl", "ingredients": [
        "rice", "vegetables", "protein"], "steps": 3, "time": 2.5},
]

# Test data for player strategies
strategy_test_data = [
    {"strategy_id": 1, "name": "Premium Focus",
        "description": "Prioritize expensive items with higher margins", "priority": "high_price"},
    {"strategy_id": 2, "name": "Volume Strategy",
        "description": "Focus on quick-to-cook items for high throughput", "priority": "speed"},
    {"strategy_id": 3, "name": "Balanced Approach",
        "description": "Mix of all food types for customer variety", "priority": "balanced"},
    {"strategy_id": 4, "name": "Customer Satisfaction",
        "description": "Optimize for customer happiness scores", "priority": "satisfaction"},
    {"strategy_id": 5, "name": "Inventory Management",
        "description": "Minimize waste and optimize stock usage", "priority": "inventory"},
]

# Test data for simulation results
simulation_results = [
    {"simulation_id": 1, "total_revenue": 450.75,
        "avg_satisfaction": 0.85, "queue_efficiency": 0.90},
    {"simulation_id": 2, "total_revenue": 523.50,
        "avg_satisfaction": 0.78, "queue_efficiency": 0.88},
    {"simulation_id": 3, "total_revenue": 487.25,
        "avg_satisfaction": 0.82, "queue_efficiency": 0.92},
    {"simulation_id": 4, "total_revenue": 412.00,
        "avg_satisfaction": 0.76, "queue_efficiency": 0.85},
    {"simulation_id": 5, "total_revenue": 561.80,
        "avg_satisfaction": 0.88, "queue_efficiency": 0.94},
    {"simulation_id": 6, "total_revenue": 498.40,
        "avg_satisfaction": 0.81, "queue_efficiency": 0.89},
    {"simulation_id": 7, "total_revenue": 445.20,
        "avg_satisfaction": 0.79, "queue_efficiency": 0.87},
    {"simulation_id": 8, "total_revenue": 532.15,
        "avg_satisfaction": 0.84, "queue_efficiency": 0.91},
]

# Additional test configuration data
test_config = {
    "simulation_duration": 8.0,
    "number_of_customers": 25,
    "number_of_kitchen_staff": 3,
    "number_of_counter_staff": 2,
    "peak_hour_multiplier": 1.5,
    "random_seed": 42,
    "enable_logging": True,
    "log_level": "DEBUG",
}

# Performance benchmark data
performance_benchmarks = [
    {"operation": "add_customer_to_queue", "avg_time_ms": 0.5, "max_time_ms": 2.1},
    {"operation": "process_order", "avg_time_ms": 1.2, "max_time_ms": 4.5},
    {"operation": "update_inventory", "avg_time_ms": 0.8, "max_time_ms": 3.2},
    {"operation": "calculate_metrics", "avg_time_ms": 2.5, "max_time_ms": 8.9},
    {"operation": "render_ui", "avg_time_ms": 16.7, "max_time_ms": 33.4},
]

# Test edge cases
edge_case_scenarios = [
    {"scenario": "empty_queue", "description": "Handle simulation with no customers"},
    {"scenario": "stock_depletion", "description": "All food items sold out"},
    {"scenario": "staff_unavailable", "description": "All kitchen staff busy"},
    {"scenario": "long_queue", "description": "Queue exceeds maximum capacity"},
    {"scenario": "negative_budget", "description": "Customer with insufficient funds"},
    {"scenario": "invalid_order", "description": "Customer ordering non-existent item"},
]

# Expansion data for future features
future_features_data = [
    {"feature": "Online Ordering", "estimated_complexity": "high", "dependencies": 2},
    {"feature": "Loyalty Program", "estimated_complexity": "medium", "dependencies": 1},
    {"feature": "Mobile App", "estimated_complexity": "very_high", "dependencies": 3},
    {"feature": "Analytics Dashboard",
        "estimated_complexity": "medium", "dependencies": 2},
    {"feature": "Payment Integration",
        "estimated_complexity": "high", "dependencies": 1},
    {"feature": "Multi-location Support",
        "estimated_complexity": "very_high", "dependencies": 4},
]

# Extended customer profiles for personality testing
extended_customer_profiles = [
    {"id": 26, "name": "Zachary King", "type": "VIP",
        "frequency": "daily", "avg_spend": 25.00},
    {"id": 27, "name": "Amy Foster", "type": "regular",
        "frequency": "3x_weekly", "avg_spend": 12.50},
    {"id": 28, "name": "Bradley Cooper", "type": "casual",
        "frequency": "monthly", "avg_spend": 8.00},
    {"id": 29, "name": "Cameron Diaz", "type": "VIP",
        "frequency": "daily", "avg_spend": 28.50},
    {"id": 30, "name": "Daniel Radcliffe", "type": "regular",
        "frequency": "weekly", "avg_spend": 15.75},
]

# System performance logs
system_logs = [
    {"timestamp": "2026-04-25 09:30:15", "level": "INFO",
        "message": "Simulation started"},
    {"timestamp": "2026-04-25 09:30:45", "level": "INFO",
        "message": "First customer arrived"},
    {"timestamp": "2026-04-25 09:31:20",
        "level": "DEBUG", "message": "Queue length: 3"},
    {"timestamp": "2026-04-25 09:32:00", "level": "INFO", "message": "Order placed"},
    {"timestamp": "2026-04-25 09:32:45",
        "level": "DEBUG", "message": "Cooking started"},
    {"timestamp": "2026-04-25 09:33:15",
        "level": "INFO", "message": "Order completed"},
    {"timestamp": "2026-04-25 09:34:00", "level": "DEBUG",
        "message": "Revenue updated: +8.50"},
    {"timestamp": "2026-04-25 09:35:30",
        "level": "INFO", "message": "Simulation ended"},
]
