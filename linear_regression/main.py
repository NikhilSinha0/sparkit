### IMPORTS
#import pandas as pd
import numpy as np
from pyspark import RDD
from core.main import SGDModel
from core.sgd import SGD
from core.point import Point
from typing import Union
###
class LinearRegression(SGDModel):
    def __init__(self, w_shape, b_shape, batch_size=32, lr=0.01):
        self.params = {"W": [0.0] * w_shape[0], "b": 0.0}  # Initialize b as a scalar
        self.batch_size = batch_size
        self.sgd = SGD(self.params, lr)

    def loss(self, data: Union[Point, RDD[Point]]):
        if isinstance(data, RDD):
            count = data.count()
            batches = data.randomSplit([self.batch_size] * (count // self.batch_size))
            losses = [batch.map(self.grad).sum() / batch.count() for batch in batches]
            return sum(losses) / len(losses)
        preds = self.predict(data)
        return 0.5 * (preds - data.labels) ** 2

    def predict(self, data: Union[Point, RDD[Point]]):
            W = self.params["W"]
            b = self.params["b"]
            if isinstance(data, RDD):
                return data.map(self.predict)
            else:
                return np.matmul(W, data.data) + b

    def grad(self, data: Union[Point, RDD[Point]]):
        if isinstance(data, RDD):
            count = data.count()
            grads = data.map(self.grad).reduce(lambda x, y: (x[0]+y[0], x[1]+y[1]))
            return grads[0]/count, grads[1]/count
        preds = self.predict(data)
        diff = preds-data.label
        return np.multiply(diff, data.data), diff

    def train(self, data, num_epochs):

        for epoch in range(num_epochs):
            data = data.sample(False, 1.0).cache()  # Shuffle the data
            num_batches = data.count() // self.batch_size
            # Split the data into batches as RDDs
            batches = data.randomSplit([1.0 / num_batches] * num_batches)
            for batch in batches:
                self.train_batch(batch)

        print("Training complete.")

    def train_batch(self, batch):
        official_batch_size = batch.count()
        grad = batch.map(self.grad).reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]))
        self.sgd.step({"W": grad[0] / official_batch_size, "b": grad[1] / official_batch_size})