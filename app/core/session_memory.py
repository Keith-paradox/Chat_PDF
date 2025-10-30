import redis
import json
from app.config import settings

class SessionMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def save_turn(self, question, answer, sources):
        turn = json.dumps({"question": question, "answer": answer, "sources": sources})
        self.redis.rpush(self.session_id, turn)

    def history(self):
        return [json.loads(x) for x in self.redis.lrange(self.session_id, 0, -1)]

    def clear(self):
        self.redis.delete(self.session_id)
