import random

def process_query(query):
    query = query.lower()

    if "congestion" in query:
        return "This area is highly congested due to peak traffic load."

    elif "best route" in query:
        return "Suggested route avoids high-density traffic zones."

    elif "traffic" in query:
        return "Traffic is increasing due to peak hour conditions."

    elif "emergency" in query:
        return "Emergency routes are optimized for fastest response."

    else:
        return "Simulation completed with default parameters."


def generate_confidence():
    return random.randint(75, 95)