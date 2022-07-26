from service.db.redis import redis_queue#清空redis库

def clear_redis_queue():
    redis_queue.clear_all()