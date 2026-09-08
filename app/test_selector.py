print("TEST FILE STARTED")

from app.services.provider_selector import ProviderSelector

print("ProviderSelector imported")

selector = ProviderSelector()

print("ProviderSelector created")

decision = selector.select_provider("What is Python?")

print("Received decision:")
print(decision)
print("Task type:", decision.task_type)
print("Complexity:", decision.complexity)

print("TEST FILE FINISHED")