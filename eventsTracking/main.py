import asyncio
import uvicorn
import json
from fastapi import FastAPI, HTTPException, Header
from confluent_kafka import KafkaException
from confluent_kafka import Producer
from datetime import datetime
from pydantic import BaseModel
from threading import Thread
from typing import Optional


class AIOProducer:
    # async kafka producer
    def __init__(self, configs, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._producer = Producer(configs)
        self._cancelled = False
        self._poll_thread = Thread(target=self._poll_loop)
        self._poll_thread.start()

    def _poll_loop(self):
        while not self._cancelled:
            self._producer.poll(0.1)

    def close(self):
        self._cancelled = True
        self._poll_thread.join()

    def produce(self, topic, value):
        result = self._loop.create_future()

        def ack(err, msg):
            if err:
                self._loop.call_soon_threadsafe(result.set_exception, KafkaException(err))
            else:
                self._loop.call_soon_threadsafe(result.set_result, msg)

        self._producer.produce(topic, value, on_delivery=ack)
        return result


class Event(BaseModel):
    event_time: Optional[datetime]
    user_id: int
    app_name: str
    event_action: Optional[str]
    event_category: str
    event_value: Optional[int]


producer = None
app = FastAPI()
secret_token = 'secret_token'


@app.on_event("startup")
async def startup_event():
    global producer
    producer = AIOProducer(
        {'bootstrap.servers': 'localhost:9092'})


@app.on_event("shutdown")
def shutdown_event():
    producer.close()


@app.post("/track")
async def create_event(event: Event, x_token: str = Header(...)):
    if x_token != secret_token:
        raise HTTPException(status_code=400, detail="Invalid X-Token header")
    try:
        event.event_time = str(datetime.utcnow())
        await producer.produce("events", json.dumps(event.dict()).encode('utf-8'))
        return {"detail": "Event created"}
    except KafkaException as ex:
        raise HTTPException(status_code=500, detail=ex.args[0].str())


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
