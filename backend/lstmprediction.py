"""Optional TensorFlow next-session LSTM. No market downloads or plotting imports."""

import logging
import threading

import numpy as np

logger = logging.getLogger(__name__)
_training_lock = threading.Lock()


def getPrediction(frame):
    import tensorflow as tf

    closes = frame['Close'].to_numpy(dtype=float)[-512:]
    if len(closes) < 65 or not np.isfinite(closes).all() or (closes <= 0).any():
        raise ValueError('LSTM requires at least 65 valid closing prices.')
    low, high = float(closes.min()), float(closes.max())
    if high == low:
        return np.array([closes[-1]])
    scaled = (closes - low) / (high - low)
    x = np.array([scaled[i - 60:i] for i in range(60, len(scaled))], dtype=np.float32)[..., None]
    y = scaled[60:].astype(np.float32)
    with _training_lock:
        tf.keras.utils.set_random_seed(42)
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(60, 1)),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(1),
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        logger.info('LSTM training started samples=%s', len(x))
        try:
            model.fit(x, y, batch_size=32, epochs=5, shuffle=False, verbose=0)
            # The final 60 actual closes predict the next day, not the last test day.
            next_sequence = scaled[-60:].astype(np.float32).reshape(1, 60, 1)
            predicted = float(model(next_sequence, training=False).numpy()[0, 0])
            logger.info('LSTM training completed')
            return np.array([predicted * (high - low) + low])
        finally:
            tf.keras.backend.clear_session()
