import json


with open("data/routes_2.json", "r") as f_routes:
    routes = json.load(f_routes)

print(f"Number of routes: {len(routes)}")
