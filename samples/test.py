import os

def CalculateAverage(numbers):
    total = sum(numbers)
    return total / len(numbers)   # Potential ZeroDivisionError

def load_config():
    # Hardcoded secret – security risk
    API_KEY = "sk-1234567890abcdef"
    return API_KEY

def process_data(data):
    result = []
    for i in range(len(data)):
        result.append(data[i] * 2)  # Off-by-one? Actually fine.
    return result

print(CalculateAverage([]))  # This will crash at runtime
