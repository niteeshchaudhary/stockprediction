"""One explained trend score. Fixed heuristics, not a trained price predictor."""
import logging
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import numpy as np

from forecast_models import rsi
from market_data import get_history, normalize_history
from trend_sources import company_identity, fundamentals, news

logger = logging.getLogger(__name__)
WEIGHTS = {'technical': 30, 'market': 15, 'news': 20, 'fundamentals': 20, 'ownership': 10, 'policy': 5}


def sentiment(headline, company=None):
    """Conservative phrase lexicon; ambiguity/negation contributes no direction."""
    import re
    value = headline.lower()
    # A negated headline cannot be safely interpreted with a phrase lexicon.
    if re.search(r'\b(no|not|denies|denied|rumou?r|may|might|could)\b', value):
        return 0
    if company:
        # Focus on the clause following the matched company, avoiding another
        # company's rally earlier in a multi-company headline.
        match = re.search(re.escape(company.lower()), value)
        if not match:
            return 0
        value = value[match.end():].split(';')[0]
    positive = [r'(?:profit|earnings|revenue|sales|demand)\w*\s+(?:\w+\s+){0,2}(?:rise|rises|rose|surge|surges|grow|growth|jump|jumps)',
                r'\b(?:wins?|secures?|awarded)\s+(?:\w+\s+){0,2}(?:order|contract)',
                r'\bshares?\s+(?:gain|gains|rise|rises|rally|rallies)\b',
                r'\b(?:upgrade|upgraded|buyback|record profit|debt reduction|tax relief|outperforms market)\b']
    negative = [r'(?:profit|earnings|revenue|sales|demand)\w*\s+(?:\w+\s+){0,2}(?:fall|falls|fell|drop|drops|decline|declines|slump)',
                r'\bshares?\s+(?:fall|falls|drop|drops|slide|slides|drag)\b',
                r'\b(?:downgrade|downgraded|fraud|default|penalty|penalties|loss|losses|investigation|tax hike|underperforms market)\b']
    pos = any(re.search(pattern, value) for pattern in positive)
    neg = any(re.search(pattern, value) for pattern in negative)
    return int(pos) - int(neg)


def fresh(value, now, days):
    try:
        stamp = datetime.fromisoformat(value)
        age = (now - stamp).total_seconds() / 86400
        return -1 <= age <= days
    except (TypeError, ValueError):
        return False


def headline_signal(data, now, days):
    articles = []
    for article in data.get('articles', []):
        if fresh(article['published_at'], now, days):
            articles.append({**article, 'signal': sentiment(article['title'], data.get('company'))})
    scored = [item for item in articles if item['signal'] != 0]
    if not scored:
        return None, articles
    weights = [math.exp(-(now - datetime.fromisoformat(item['published_at'])).total_seconds() / (86400 * days / 2)) for item in scored]
    # A single polar headline is weak evidence; require diversity for full strength.
    strength = min(1, len({item['publisher'] for item in scored}) / 3)
    return float(np.average([item['signal'] for item in scored], weights=weights) * strength), articles


def benchmark(ticker):
    symbol = '^BSESN' if ticker.endswith('.BO') else '^NSEI' if ticker.endswith('.NS') else '^GSPC'
    try:
        return {'ticker': symbol, 'history': get_history(symbol)}
    except Exception:
        logger.warning('Trend market benchmark unavailable for %s', ticker, exc_info=True)
        return {'ticker': symbol, 'history': None}


def build_trend(ticker, frame, financial, company_news, policy_news, market, now=None):
    now = now or datetime.now(timezone.utc)
    frame = normalize_history(frame)
    if len(frame) < 50:
        raise ValueError('At least 50 trading sessions are required for trend analysis.')
    closes = frame.Close.to_numpy(dtype=float)
    vol = float(np.std(np.diff(np.log(closes[-21:]))))
    scale = max(vol * np.sqrt(20), .01)
    ma20, ma50 = float(closes[-20:].mean()), float(closes[-50:].mean())
    return20 = float(closes[-1] / closes[-21] - 1)
    price_fresh = fresh(frame.Date.iloc[-1] + 'T00:00:00+00:00', now, 7)
    technical = float(.45 * np.tanh((closes[-1] / ma20 - 1) / scale)
                      + .35 * np.tanh(return20 / scale) + .2 * np.tanh((ma20 / ma50 - 1) / scale)) if price_fresh else None
    volumes = frame.Volume.to_numpy(dtype=float)
    volume_ratio = float(volumes[-1] / volumes[-21:-1].mean()) if volumes[-21:-1].mean() > 0 else None
    market_score, benchmark_return, relative = None, None, None
    benchmark_frame = market.get('history')
    if benchmark_frame is not None and price_fresh:
        aligned = frame[['Date', 'Close']].merge(benchmark_frame[['Date', 'Close']], on='Date', suffixes=('_stock', '_market')).tail(21)
        if len(aligned) == 21 and aligned.Date.iloc[-1] == frame.Date.iloc[-1]:
            benchmark_return = float(aligned.Close_market.iloc[-1] / aligned.Close_market.iloc[0] - 1)
            stock_return = float(aligned.Close_stock.iloc[-1] / aligned.Close_stock.iloc[0] - 1)
            relative = stock_return - benchmark_return
            market_score = float(.5 * np.tanh(benchmark_return / scale) + .5 * np.tanh(relative / scale))
    news_score, articles = headline_signal(company_news, now, 7)
    # Avoid counting the same policy story in two different factors.
    news_keys = {item['title'].lower() for item in articles}
    policy_data = {**policy_news, 'articles': [item for item in policy_news.get('articles', []) if item['title'].lower() not in news_keys]}
    policy_score, policy_articles = headline_signal(policy_data, now, 30)
    fundamental_parts = []
    pe, peer_pe = financial.get('pe'), financial.get('peer_pe')
    if pe is not None and peer_pe is not None and pe > 0 and peer_pe > 0:
        fundamental_parts.append((.35, float(np.clip(np.log(peer_pe / pe) / np.log(2), -1, 1))))
    results_fresh = fresh(financial.get('results_as_of'), now, 180)
    if results_fresh:
        for key, weight in [('profit_growth_yoy', .4), ('sales_growth_yoy', .25)]:
            value = financial.get(key)
            if value is not None:
                fundamental_parts.append((weight, float(np.tanh(value / 30))))
    # Missing earnings/valuation components reduce this factor rather than increase others.
    fundamental_score = sum(weight * value for weight, value in fundamental_parts) if fundamental_parts else None
    ownership_fresh = fresh(financial.get('ownership_as_of'), now, 180)
    ownership_parts = []
    if ownership_fresh:
        for key, weight in [('promoter_change_pp', .5), ('fii_change_pp', .25), ('dii_change_pp', .25)]:
            value = financial.get(key)
            if value is not None:
                ownership_parts.append((weight, float(np.tanh(value / 2))))
    ownership_score = sum(weight * value for weight, value in ownership_parts) if ownership_parts else None
    signals = {'technical': technical, 'market': market_score, 'news': news_score,
               'fundamentals': fundamental_score, 'ownership': ownership_score, 'policy': policy_score}
    names = {'technical': 'Price trend', 'market': 'Market & relative strength', 'news': 'Company news',
             'fundamentals': 'Valuation & earnings', 'ownership': 'Ownership changes', 'policy': 'Budget & policy news'}
    reasons = {
        'technical': '20/50-session averages and 20-session return, scaled by recent volatility.' if technical is not None else 'Price history is older than seven days.',
        'market': 'Aligned benchmark return and stock relative strength.' if market_score is not None else 'Insufficient aligned market history.',
        'news': f'{len(articles)} relevant headlines; conservative phrase sentiment, not full-article analysis.' if articles else company_news.get('error', 'News unavailable.'),
        'fundamentals': 'P/E versus the median of displayed peers, plus same-quarter profit and sales growth. Peer businesses can differ.' if fundamental_score is not None else 'Comparable valuation/earnings inputs unavailable or outdated.',
        'ownership': 'Quarter-on-quarter changes, not the absolute promoter holding. Changes can have non-trading causes.' if ownership_score is not None else 'Ownership changes unavailable or the reported period is older than six months.',
        'policy': 'Recent company-matched budget/policy headlines, excluding company-news duplicates. No full budget-document interpretation.' if policy_articles else 'No distinct recent company-matched budget/policy headlines.'}
    factors = [{'id': key, 'name': names[key], 'weight': WEIGHTS[key], 'available': value is not None,
                'signal': round(value, 4) if value is not None else None,
                'contribution': round(WEIGHTS[key] * value, 2) if value is not None else 0,
                'status': 'Scored' if value is not None else 'Unclassified' if (key == 'news' and articles) or (key == 'policy' and policy_articles) else 'Unavailable',
                'reason': reasons[key]} for key, value in signals.items()]
    score = float(sum(factor['contribution'] for factor in factors))
    coverage = sum(factor['weight'] for factor in factors if factor['available'] and factor['id'] not in {'fundamentals', 'ownership'})
    coverage += WEIGHTS['fundamentals'] * sum(weight for weight, _ in fundamental_parts)
    coverage += WEIGHTS['ownership'] * sum(weight for weight, _ in ownership_parts)
    coverage = round(coverage, 1)
    direction = 'Insufficient evidence' if coverage < 60 or not price_fresh else 'Upward bias' if score >= 15 else 'Downward bias' if score <= -15 else 'Mixed / flat bias'
    warnings = ['Fixed heuristic score, not a calibrated probability or a backtested trading strategy.',
                'Headline rules can miss context. Budget impact and promoter pledging are not verified by this model.']
    if coverage < 100:
        warnings.append('Missing or unclassified inputs contribute zero; their weights are not redistributed.')
    if not results_fresh:
        warnings.append('Quarterly earnings are unavailable/outdated and excluded from scoring.')
    if not ownership_fresh:
        warnings.append('Ownership data is unavailable/outdated and excluded from scoring.')
    return {'algorithm': 'Evidence-weighted trend score', 'ticker': ticker, 'company': company_identity(ticker)[0],
            'trend': direction, 'score': round(score, 2), 'coverage': coverage,
            'horizon': 'Indicative bias over the next 5–20 trading sessions',
            'generated_at': now.isoformat(), 'price_as_of': frame.Date.iloc[-1],
            'factors': factors, 'fundamentals': financial, 'news': articles, 'policy_news': policy_articles,
            'source_status': {'news': {k: v for k, v in company_news.items() if k != 'articles'},
                              'policy': {k: v for k, v in policy_news.items() if k != 'articles'}},
            'indicators': {'sma20': ma20, 'sma50': ma50, 'rsi14': rsi(closes), 'return20_pct': return20 * 100,
                           'annualized_volatility': vol * np.sqrt(252) * 100, 'volume_ratio': volume_ratio,
                           'benchmark': market.get('ticker'),
                           'benchmark_return20_pct': benchmark_return * 100 if benchmark_return is not None else None,
                           'relative_return20_pp': relative * 100 if relative is not None else None},
            'warnings': warnings}


def analyse_trend(ticker):
    # Independent sources run together; each public request has a bounded timeout.
    with ThreadPoolExecutor(max_workers=4) as workers:
        jobs = [workers.submit(fundamentals, ticker), workers.submit(news, ticker),
                workers.submit(news, ticker, True), workers.submit(benchmark, ticker)]
        frame = get_history(ticker)
        inputs = [job.result() for job in jobs]
    return build_trend(ticker, frame, *inputs)
