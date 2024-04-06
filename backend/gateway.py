import uuid
from typing import Union

from fastapi import FastAPI
import csv
from pydantic import BaseModel


app = FastAPI()


class OrderFormRequestSchema(BaseModel):
    contact: str
    model: str
    comment: str


@app.get("/catalog")
def read_root():
    return {
        "Камеры": ["Крутая камера пиздец"],
        "Запчасти": {
            "Электроника": ["Эл. запчасть 1", "Эл. запчасть 2", "Эл. запчасть 3"],
            "Механика": ["Мех. деталь 1", "Мех. деталь 2", "Мех. деталь 3"]
        }
    }


@app.post("/form")
def read_item(order_from: OrderFormRequestSchema):
    user_id = str(uuid.uuid4())
    with open("db.csv", 'a', newline='') as csv_output:
        fieldnames = ['user_id', 'contact', 'model', 'comment']
        writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
        output = order_from.dict()
        output['user_id'] = user_id
        writer.writerow(output)
        return 200


