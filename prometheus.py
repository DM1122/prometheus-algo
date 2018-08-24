import datetime as dt
import matplotlib
from matplotlib import pyplot as plt
import modelib
import numpy as np
import NSRDBlib
import os
import processlib
import tensorflow as tf
from tensorflow import keras
import time

np.random.seed(123)
tf.set_random_seed(123)

#region Hyperparams
features = [       # Temperature/Clearsky DHI/Clearsky DNI/Clearsky GHI/Dew Point/DHI/DNI/GHI/Relative Humidity/Solar Zenith Angle/Surface Albedo/Pressure/Precipitable Water/Wind Direction/Wind Speed/Cloud Type_(0-10).0
    'Temperature',
    'Clearsky DHI',
    'Clearsky DNI',
    'Clearsky GHI',
    'Dew Point',
    'DHI',
    'DNI',
    'GHI',
    'Relative Humidity',
    'Solar Zenith Angle',
    'Surface Albedo',
    'Pressure',
    'Precipitable Water',
    'Wind Direction',
    'Wind Speed',
    'Cloud Type_0.0',
    'Cloud Type_1.0',
    'Cloud Type_2.0',
    'Cloud Type_3.0',
    'Cloud Type_4.0',
    'Cloud Type_6.0',
    'Cloud Type_7.0',
    'Cloud Type_8.0',
    'Cloud Type_9.0',
    'Cloud Type_10.0'
]
features_label = 'DHI'
features_label_shift = 24       # hourly resolution

learn_rate = 0.0003
model_type = 'RNN'      # LN/MLP/RNN/LSTM/GRU
n_layers = 2
n_nodes = 10
act = 'relu'

n_epochs = 3
batch_size = 128
sequence_length = 168

split_test = 0.2       # first
split_val = 0.25       # second
#endregion

#region Functions
def test_model():       # does not work in current version of keras
    print('Testing model...')
    result = model.evaluate(x=X_test, y=y_test)
    for name, value in zip(model.metrics_names, result):
        print(name, value)

def predict_model():
    print('Calculating output...')
    output = model.predict(x=X_test, verbose=1)

    data_forecast = processlib.unprocess(output, y_test)

    matplotlib.style.use('classic')
    fig = plt.figure('{0} Output: {1}'.format(model_type,features_label))
    ax1 = fig.add_subplot(1,1,1)
    ax1.set_title('Testing')

    data_forecast.plot(kind='line', ax=ax1)
    plt.show()
#endregion

#region Main
data = NSRDBlib.get_data(features)      # get data
data_features, data_labels = processlib.label(data, features_label, features_label_shift)       # create labels
X_train_raw, y_train_raw, X_test_raw, y_test_raw = processlib.split(data_features, data_labels, split_test)        # split data into train/test
X_train, y_train, X_test, y_test = processlib.normalize(X_train_raw,y_train_raw, X_test_raw, y_test_raw)        # normalize datasets

if model_type == 'RNN' or model_type == 'LSTM' or model_type == 'GRU':      # reshape data by sequence length
    X_train = processlib.reshape(X_train, sequence_length)
    y_train = processlib.reshape(y_train, sequence_length)
    X_test = processlib.reshape(X_test, sequence_length)
    y_test = processlib.reshape(y_test, sequence_length)

print('Commencing Prometheus model generation...')
if model_type == 'LN':
    model = modelib.create_model_linear(learn_rate, X_test.shape[0])
    print(model.summary())
elif model_type == 'MLP':
    model = modelib.create_model_dense(learn_rate, n_layers, n_nodes, act, X_test.shape[1])
    print(model.summary())
elif model_type == 'RNN':
    model = modelib.create_model_rnn(learn_rate, n_layers, n_nodes, act, X_test.shape[1])
else:
    raise ValueError('Invalid model type {}'.format(model_type))


log_date = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
log_dir = './logs/{0}({1})_{2}_layers({3})_nodes({4})/'.format(log_date,os.path.basename(__file__),model_type,n_layers,n_nodes)
callback_log = keras.callbacks.TensorBoard(
    log_dir=log_dir,
    histogram_freq=0,       # not working currently
    batch_size=32,
    write_graph=True,
    write_grads=False,
    write_images=False
)

time_start = time.time()
history = model.fit(        # train model
    x=X_train,
    y=y_train,
    batch_size=batch_size,
    epochs=n_epochs,
    verbose=1,
    callbacks=[callback_log],
    validation_split=split_val,
    shuffle=False
)
time_end = time.time()
time_elapsed = time_end - time_start

print('Model training completed!')
print("Validation Loss: {0:.2%}".format(history.history['val_loss'][-1]))
print('Elapsed time: {0:.2}sec'.format(time_elapsed))

test_model()
predict_model()

print('Debug:\n$tensorboard --logdir=logs')
#endregion