from app.services.router_service import RouterService


router = RouterService()

decision = router.analyze(
    "Write a Python program to implement merge sort"
)

print(decision)
print("Task:", decision.task_type)
print("Complexity:", decision.complexity)