"""Account-free trend inputs. Provider failures are explicit, never synthetic data."""
import logging
import calendar
import re
import threading
import time
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from difflib import SequenceMatcher
from html.parser import HTMLParser
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import numpy as np

from stock_directory import EXCHANGE_CATALOGUE

logger = logging.getLogger(__name__)
_cache = OrderedDict()
_lock = threading.Lock()
UTC = timezone.utc


def cached(key, ttl, fetch):
    with _lock:
        entry = _cache.get(key)
        if entry and time.monotonic() - entry[0] < entry[1]:
            return entry[2]
    try:
        result = fetch()
        lifetime = ttl
    except Exception:
        logger.warning('Trend source unavailable: %s', key, exc_info=True)
        result, lifetime = {'available': False, 'error': 'Public source is unavailable or unsupported.'}, 60
    with _lock:
        _cache[key] = (time.monotonic(), lifetime, result)
        _cache.move_to_end(key)
        while len(_cache) > 128:
            _cache.popitem(last=False)
    return result


def fetch_text(url, headers=None):
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0', **(headers or {})})
    with urlopen(request, timeout=10) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError('Source response too large')
    return data.decode('utf-8')


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def text(self):
        return ' '.join(child.text() if isinstance(child, Node) else child for child in self.children)

    def find(self, tag=None, **attrs):
        for child in self.children:
            if isinstance(child, Node):
                if (tag is None or child.tag == tag) and all(child.attrs.get(k) == v for k, v in attrs.items()):
                    yield child
                yield from child.find(tag, **attrs)


class PageParser(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)


def number(value):
    try:
        result = float(re.sub(r'[,₹%\s]', '', value))
        return result if np.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def text(value):
    return re.sub(r'\s+', ' ', value.replace('\xa0', ' ')).strip()


def table_rows(node):
    return [[text(cell.text()) for cell in row.find() if cell.tag in {'th', 'td'}]
            for row in node.find('tr')]


def table(root, section):
    node = next(root.find(id=section), None)
    return table_rows(next(node.find('table'), Node())) if node else []


def row_values(rows, label):
    for row in rows:
        if row and text(row[0]).rstrip(' +') == label:
            return [number(cell) for cell in row[1:]]
    return []


def period_date(value):
    try:
        period = datetime.strptime(value, '%b %Y')
        return period.replace(day=calendar.monthrange(period.year, period.month)[1], tzinfo=UTC).isoformat()
    except (ValueError, TypeError):
        return None


def parse_fundamentals(html, url):
    root = PageParser(html).root
    top = next(root.find(id='top-ratios'), None)
    if not top:
        raise ValueError('Fundamental summary unavailable')
    ratios = {}
    for item in top.find('li'):
        label = next((n for n in item.find('span') if n.attrs.get('class') == 'name'), None)
        value = next((n for n in item.find('span') if n.attrs.get('class') == 'number'), None)
        if label and value:
            ratios[text(label.text())] = number(text(value.text()))
    quarters, ownership = table(root, 'quarters'), table(root, 'quarterly-shp')
    profits = row_values(quarters, 'Net Profit')
    sales = row_values(quarters, 'Sales') or row_values(quarters, 'Revenue')
    promoters = row_values(ownership, 'Promoters')
    institutions = row_values(ownership, 'FIIs')
    domestic = row_values(ownership, 'DIIs')
    def latest(values):
        return values[-1] if values else None
    def change(values):
        return values[-1] - values[-2] if len(values) >= 2 and all(v is not None for v in values[-2:]) else None
    def growth(values):
        # Only compare the same quarter a year earlier; missing cells keep alignment.
        return (values[-1] / values[-5] - 1) * 100 if len(values) >= 5 and values[-1] is not None and values[-5] is not None and values[-5] > 0 else None
    info = next(root.find(id='company-info'), Node())
    return {'available': True, 'source': url, 'fetched_at': datetime.now(UTC).isoformat(),
            'basis': 'Consolidated' if info.attrs.get('data-consolidated') == 'true' else 'Standalone',
            'name': text(next(root.find('h1'), Node()).text()),
            'pe': ratios.get('Stock P/E'), 'roe': ratios.get('ROE'), 'roce': ratios.get('ROCE'),
            'profit_growth_yoy': growth(profits), 'sales_growth_yoy': growth(sales),
            'latest_profit': latest(profits),
            'results_period': quarters[0][-1] if quarters and quarters[0] else None,
            'results_as_of': period_date(quarters[0][-1]) if quarters and quarters[0] else None,
            'ownership_period': ownership[0][-1] if ownership and ownership[0] else None,
            'ownership_as_of': period_date(ownership[0][-1]) if ownership and ownership[0] else None,
            'promoter_holding': latest(promoters), 'promoter_change_pp': change(promoters),
            'fii_holding': latest(institutions), 'fii_change_pp': change(institutions),
            'dii_holding': latest(domestic), 'dii_change_pp': change(domestic),
            'peer_pe': None, 'peer_count': 0, 'warehouse': info.attrs.get('data-warehouse-id'),
            'company_id': info.attrs.get('data-company-id')}


def parse_peers(html, company_id):
    root = PageParser(html).root
    rows = list(root.find('tr'))
    header = []
    for row in rows:
        cells = [text(cell.text()) for cell in row.find('th')]
        if cells:
            header = cells
            break
    column = next((i for i, label in enumerate(header) if label == 'P/E'), None)
    if column is None:
        return None, 0
    values = []
    for row in rows:
        if not row.attrs.get('data-row-company-id') or row.attrs['data-row-company-id'] == company_id:
            continue
        cells = [text(cell.text()) for cell in row.find('td')]
        value = number(cells[column]) if len(cells) > column else None
        if value is not None and value > 0:
            values.append(value)
    return (float(np.median(values)), len(values)) if len(values) >= 3 else (None, len(values))


def company_identity(ticker):
    stock = next((s for s in EXCHANGE_CATALOGUE['stocks'] if s['ticker'] == ticker), None)
    name = stock['name'] if stock else ticker.removesuffix('.NS').removesuffix('.BO')
    name = re.sub(r'\b(?:Limited|Ltd\.?|LTD\.?|Ltd\.?)\s*$', '', name, flags=re.I).strip()
    code = stock.get('scripCode') if stock and ticker.endswith('.BO') else ticker.removesuffix('.NS')
    return name, code


def fundamentals(ticker):
    if not ticker.endswith(('.NS', '.BO')):
        return {'available': False, 'error': 'Fundamental source supports Indian companies only.'}
    _, code = company_identity(ticker)
    def load():
        base = f'https://www.screener.in/company/{quote(code, safe="")}/'
        url = base + 'consolidated/'
        try:
            data = parse_fundamentals(fetch_text(url), url)
        except Exception:
            url = base
            data = parse_fundamentals(fetch_text(url), url)
        warehouse = data.pop('warehouse')
        company_id = data.pop('company_id')
        if warehouse and str(warehouse).isdigit():
            try:
                fragment = fetch_text(f'https://www.screener.in/api/company/{warehouse}/peers/',
                                      {'X-Requested-With': 'XMLHttpRequest', 'Referer': url})
                data['peer_pe'], data['peer_count'] = parse_peers(fragment, company_id)
            except Exception:
                logger.warning('Trend peer comparison unavailable for %s', ticker)
        return data
    return cached(('fundamentals', ticker), 21600, load)


def parse_news(xml, name, now, days, policy=False):
    root = ET.fromstring(xml)
    tokens = re.findall(r'[a-z0-9]+', name.lower())
    tokens = [word for word in tokens if word not in {'limited', 'ltd', 'company', 'corporation', 'india', 'the', 'and'}]
    items, seen = [], set()
    for entry in root.findall('./channel/item'):
        title = text(entry.findtext('title', ''))
        source = entry.findtext('source', '')
        headline = title.removesuffix(' - ' + source) if source else title
        if re.search(r'\bshare price prediction\b|\blive NSE\b.*\bchart\b', headline, re.I):
            continue
        key = re.sub(r'[^a-z0-9]', '', headline.lower())
        words = set(re.findall(r'[a-z0-9]+', headline.lower()))
        # Fail closed on ambiguous company names; the search alone is insufficient.
        if not tokens or not all(token in words for token in tokens) or key in seen:
            continue
        if any(item['publisher'] == source and SequenceMatcher(None, item['title'].lower(), headline.lower()).ratio() > .92 for item in items):
            continue
        if policy and not re.search(r'\b(budget|policy|tax|tariff|subsidy|government|allocation|duty|regulation)\b', headline, re.I):
            continue
        try:
            published = parsedate_to_datetime(entry.findtext('pubDate', '')).astimezone(UTC)
        except (ValueError, TypeError, OverflowError):
            continue
        if not now - timedelta(days=days) <= published <= now + timedelta(minutes=5):
            continue
        link = entry.findtext('link', '')
        if not link.startswith('https://news.google.com/'):
            continue
        seen.add(key)
        items.append({'title': headline, 'url': link, 'publisher': source,
                      'published_at': published.isoformat()})
    return sorted(items, key=lambda item: item['published_at'], reverse=True)[:12]


def news(ticker, policy=False):
    name, _ = company_identity(ticker)
    days = 30 if policy else 7
    query = f'"{name}" (budget OR policy OR tax OR tariff OR subsidy) when:{days}d' if policy else f'"{name}" stock when:{days}d'
    url = 'https://news.google.com/rss/search?' + urlencode({'q': query, 'hl': 'en-IN', 'gl': 'IN', 'ceid': 'IN:en'})
    def load():
        now = datetime.now(UTC)
        articles = parse_news(fetch_text(url), name, now, days, policy)
        return {'available': bool(articles), 'company': name, 'articles': articles, 'source': url,
                'fetched_at': now.isoformat(), 'error': None if articles else 'No recent company-matched headlines found.'}
    return cached(('policy' if policy else 'news', ticker), 900, load)
