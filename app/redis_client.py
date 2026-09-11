import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

if __name__=="__main__":
    print(redis_client.ping())

