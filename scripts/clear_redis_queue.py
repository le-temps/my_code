from service.db.redis import redis_queue

def clear_redis_queue():
    redis_queue.clear_all()