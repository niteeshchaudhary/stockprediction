"""Lightweight price models and chronological evaluation, using NumPy only.

Holt recurrence: https://otexts.com/fpp3/holt.html
Evaluation protocol: https://otexts.com/fpp3/tscv.html
"""
import numpy as np


def momentum(closes):
    returns = np.diff(np.log(closes[-61:]))
    weights = np.exp(np.linspace(-3, 0, len(returns)))
    return float(closes[-1] * np.exp(np.average(returns, weights=weights)))


def damped_trend(closes):
    # Fixed smoothing parameters; no tuning on evaluation targets.
    values = np.log(closes[-126:])
    level, trend = values[0], values[1] - values[0]
    alpha, beta, phi = .8, .1, .9
    for value in values[1:]:
        previous = level
        level = alpha * value + (1 - alpha) * (level + phi * trend)
        trend = beta * (level - previous) + (1 - beta) * phi * trend
    return float(np.exp(level + phi * trend))


def rsi(closes):
    moves = np.diff(closes[-15:])
    gain = np.maximum(moves, 0).mean()
    loss = np.maximum(-moves, 0).mean()
    return float(100 * gain / (gain + loss)) if gain + loss > 0 else 50.


def features(closes):
    returns = np.diff(np.log(closes[-21:]))
    return np.r_[returns[-5:], returns[-5:].mean(), returns.mean(), returns.std(),
                 closes[-1] / closes[-20:].mean() - 1, rsi(closes) / 100 - .5]


def technical_ridge(closes):
    closes = closes[-253:]
    x = np.array([features(closes[:i]) for i in range(21, len(closes))])
    y = np.diff(np.log(closes))[21 - 1:]
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-8] = 1
    design = np.column_stack([np.ones(len(x)), (x - mean) / scale])
    penalty = np.eye(design.shape[1]) * 10
    penalty[0, 0] = 0
    weights = np.linalg.solve(design.T @ design + penalty, design.T @ y)
    prediction = float(np.r_[1, (features(closes) - mean) / scale] @ weights)
    # Avoid extrapolating extreme returns beyond the training distribution.
    limit = max(.01, 3 * np.std(y))
    return float(closes[-1] * np.exp(np.clip(prediction, -limit, limit)))


def metrics(predicted, actual, previous):
    errors = predicted - actual
    def direction(prices):
        change = prices / previous - 1
        return np.where(np.abs(change) < 1e-8, 0, np.sign(change))
    return {'mae': float(np.abs(errors).mean()),
            'mape': float((np.abs(errors) / actual).mean() * 100),
            'direction_accuracy': float((direction(predicted) == direction(actual)).mean() * 100)}


def analyse(closes, ridge):
    methods = {'baseline': ('Last close baseline', lambda values: float(values[-1])),
               'ridge': ('Ridge autoregression', ridge),
               'momentum': ('Weighted momentum', momentum),
               'trend': ('Damped Holt trend', damped_trend),
               'technical': ('Technical indicator ridge', technical_ridge)}
    count = min(40, len(closes) - 45)
    start = len(closes) - count
    predictions = np.array([[function(closes[:i]) for _, function in methods.values()]
                            for i in range(start, len(closes))])
    if not np.all(np.isfinite(predictions)) or np.any(predictions <= 0):
        raise ValueError('A comparison model returned an invalid price.')
    actual, previous = closes[start:], closes[start - 1:-1]
    split = count // 2
    # Fit ensemble weights on earlier folds, then evaluate on later unseen folds.
    tuning_error = (np.abs(predictions[:split] - actual[:split, None]) / actual[:split, None]).mean(axis=0)
    weights = 1 / np.maximum(tuning_error, 1e-4)
    weights /= weights.sum()
    holdout, target, prior = predictions[split:], actual[split:], previous[split:]
    combined = holdout @ weights
    next_prices = np.array([function(closes) for _, function in methods.values()])
    estimate = float(next_prices @ weights)
    if not np.all(np.isfinite(next_prices)) or np.any(next_prices <= 0):
        raise ValueError('A comparison model returned an invalid price.')
    results = [{'id': key, 'name': name, 'price': float(next_prices[j]), 'weight': float(weights[j]),
                **metrics(holdout[:, j], target, prior)} for j, (key, (name, _)) in enumerate(methods.items())]
    ensemble_metrics = metrics(combined, target, prior)
    # Empirical error range, not a calibrated probability or price guarantee.
    width = float(np.quantile(np.abs(combined - target) / target, .9))
    return {'price': estimate, 'models': results, **ensemble_metrics,
            'evaluation_sessions': len(target), 'weight_fit_sessions': split,
            'beats_baseline': ensemble_metrics['mae'] < results[0]['mae'] - 1e-8,
            'error_range': {'low': max(.01, estimate * (1 - width)), 'high': estimate * (1 + width),
                            'label': 'Recent 90th-percentile absolute error range'},
            'indicators': {'rsi14': rsi(closes), 'sma20': float(closes[-20:].mean()),
                           'sma50': float(closes[-50:].mean()),
                           'annualized_volatility': float(np.std(np.diff(np.log(closes[-21:]))) * np.sqrt(252) * 100)},
            'scope': 'Daily closing-price analysis; excludes news, fundamentals and broader-market feeds.'}
