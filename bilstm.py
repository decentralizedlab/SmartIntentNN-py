import tensorflow as tf
from tensorflow import keras
import dataset as db
import os
import sys
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
argv = sys.argv[1:]


UNIT = 64
DIM = 768
VOC = 50264
PAD = 1
PAD_TKN = 512
BATCH = 500
BATCH_SIZE = 20
EPOCH = 50
MAX_SEQ = 256
MODEL_PATH = './models/bilstm'
DROP = 0.5  # best is 0.5


def buildModel():
    model = keras.Sequential()
    model.add(keras.layers.Masking(
        mask_value=PAD, input_shape=(None, PAD_TKN)))
    model.add(keras.layers.Embedding(input_dim=VOC, output_dim=DIM))
    model.add(keras.layers.AveragePooling2D(pool_size=(1, PAD_TKN)))
    model.add(keras.layers.Reshape((-1, DIM)))
    model.add(keras.layers.Bidirectional(
        keras.layers.LSTM(units=UNIT, return_sequences=True)))
    model.add(keras.layers.Bidirectional(
        keras.layers.LSTM(units=UNIT, return_sequences=False)))
    model.add(keras.layers.Dropout(DROP))
    model.add(keras.layers.Dense(10, activation='sigmoid'))
    model.summary()
    return model


def loadModel():
    try:
        return keras.models.load_model(MODEL_PATH)
    except Exception as e:
        print(e)
        return buildModel()


def summary():
    model = loadModel()
    model.summary()


def pad(xs):
    arr = []
    # find max length of sequence
    max = 0
    for x in xs:
        if (len(x) > max):
            max = len(x)
    # pad sequence to max
    if (max > MAX_SEQ):
        max = MAX_SEQ
    for x in xs:
        while (len(x) < max):
            x.append([1]*PAD_TKN)
        arr.append(x[:max])
    return arr


def train(batch=BATCH, batch_size=BATCH_SIZE, epoch=EPOCH, start=1):
    model = loadModel()
    model.compile(optimizer=keras.optimizers.Adam(),
                  loss=keras.losses.BinaryCrossentropy(),
                  metrics=[keras.metrics.BinaryAccuracy(),
                           keras.metrics.Precision(),
                           keras.metrics.Recall()])
    id = start
    print("Batch:", batch)
    print("Batch Size:", batch_size)
    print("Total:", batch*batch_size)
    while (batch > 0):
        xs = []
        ys = []
        print("Current Batch:", batch)
        print("Current Id:", id)
        while (len(xs) < batch_size):
            data = db.getXY(id)
            id = id+1
            if (data == None):
                continue
            xs.append(data['x'])
            ys.append(data['y'])
        tx = tf.convert_to_tensor(pad(xs))
        ty = tf.convert_to_tensor(ys)
        print(tx)
        print(ty)
        model.fit(tx, ty, batch_size=batch_size,
                  epochs=epoch, shuffle=True)
        model.save(MODEL_PATH)
        batch = batch-1


if (argv[0] == 'summary'):
    summary()
if (argv[0] == 'train'):
    train(batch=int(argv[1]), start=int(argv[2]),
          batch_size=int(argv[3]), epoch=int(argv[4]))
