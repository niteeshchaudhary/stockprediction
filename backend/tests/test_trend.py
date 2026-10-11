import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
import trend_service as service
import trend_sources as sources

NOW = datetime(2026, 10, 12, 9, tzinfo=timezone.utc)


def history():
    prices = 100 * np.exp(np.arange(100) * .001)
    return pd.DataFrame({'Date': pd.date_range(end='2026-10-09', periods=100),
                         'Open': prices, 'High': prices, 'Low': prices, 'Close': prices,
                         'Volume': np.full(100, 1000)})


def article(title, published='2026-10-11T09:00:00+00:00'):
    return {'title': title, 'publisher': 'Example', 'published_at': published, 'url': 'https://news.google.com/rss/articles/example'}


class SourceTests(unittest.TestCase):
    def test_fundamentals_preserve_blank_quarters_and_ownership_changes(self):
        html = '''<div id="company-info" data-consolidated="true" data-company-id="1" data-warehouse-id="2"></div>
        <h1>Example Ltd</h1><ul id="top-ratios"><li><span class="name">Stock P/E</span><span class="number">25.5</span></li></ul>
        <section id="quarters"><table><tr><th></th><th>Jun 2025</th><th>Sep 2025</th><th>Dec 2025</th><th>Mar 2026</th><th>Jun 2026</th></tr>
        <tr><td>Net Profit +</td><td>100</td><td></td><td>50</td><td>80</td><td>120</td></tr>
        <tr><td>Sales +</td><td>200</td><td>250</td><td>300</td><td>350</td><td>400</td></tr></table></section>
        <div id="quarterly-shp"><table><tr><th></th><th>Mar 2026</th><th>Jun 2026</th></tr>
        <tr><td>Promoters +</td><td>50%</td><td>51%</td></tr><tr><td>FIIs +</td><td>20%</td><td>19%</td></tr></table></div>'''
        result = sources.parse_fundamentals(html, 'https://www.screener.in/company/EXAMPLE/')
        self.assertEqual(result['pe'], 25.5)
        self.assertAlmostEqual(result['profit_growth_yoy'], 20)
        self.assertAlmostEqual(result['sales_growth_yoy'], 100)
        self.assertEqual(result['ownership_as_of'], '2026-06-30T00:00:00+00:00')
        self.assertEqual(result['promoter_change_pp'], 1)
        self.assertEqual(result['fii_change_pp'], -1)
        self.assertIsNone(result['dii_change_pp'])

    def test_peer_comparison_excludes_target_and_nonpositive_pe(self):
        html = '<table><tr><th>Company</th><th>P/E</th></tr>'
        for identifier, pe in [('1', 999), ('2', 10), ('3', 20), ('4', 30), ('5', -5)]:
            html += f'<tr data-row-company-id="{identifier}"><td>Example</td><td>{pe}</td></tr>'
        html += '</table>'
        self.assertEqual(sources.parse_peers(html, '1'), (20, 3))

    def test_news_filters_other_companies_old_future_and_duplicate_titles(self):
        def item(title, date):
            return f'<item><title>{title} - Publisher</title><source>Publisher</source><link>https://news.google.com/rss/articles/test</link><pubDate>{date}</pubDate></item>'
        valid = item('Reliance Industries profits rise', 'Sun, 11 Oct 2026 09:00:00 GMT')
        xml = '<rss><channel>' + valid + valid + item('Reliance Power profits rise', 'Sun, 11 Oct 2026 09:00:00 GMT') + item('Reliance Industries old story', 'Tue, 01 Sep 2026 09:00:00 GMT') + item('Reliance Industries future story', 'Sun, 18 Oct 2026 09:00:00 GMT') + '</channel></rss>'
        articles = sources.parse_news(xml, 'Reliance Industries', NOW, 7)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['title'], 'Reliance Industries profits rise')

    def test_cached_source_failure_is_explicit_and_does_not_raise(self):
        key = ('test', 'failure')
        sources._cache.pop(key, None)
        with self.assertLogs('trend_sources', 'WARNING'):
            failed = sources.cached(key, 600, lambda: (_ for _ in ()).throw(OSError('Offline')))
        self.assertFalse(failed['available'])
        self.assertEqual(sources.cached(key, 600, lambda: self.fail('Failure should be briefly cached')), failed)
        sources._cache.pop(key, None)


class TrendTests(unittest.TestCase):
    def test_weak_coverage_cannot_claim_direction(self):
        result = service.build_trend('RELIANCE.NS', history(), {}, {}, {}, {'history': None}, NOW)
        self.assertEqual(result['coverage'], 30)
        self.assertEqual(result['trend'], 'Insufficient evidence')
        self.assertEqual(len(result['factors']), 6)
        self.assertTrue(-30 <= result['score'] <= 30)

    def test_stale_ownership_and_results_excluded(self):
        data = {'ownership_as_of': '2025-06-30T00:00:00+00:00', 'results_as_of': '2025-06-30T00:00:00+00:00',
                'promoter_change_pp': 10, 'profit_growth_yoy': 100}
        result = service.build_trend('RELIANCE.NS', history(), data, {}, {}, {'history': None}, NOW)
        self.assertFalse(next(f for f in result['factors'] if f['id'] == 'ownership')['available'])
        self.assertFalse(next(f for f in result['factors'] if f['id'] == 'fundamentals')['available'])

    def test_news_negation_and_policy_duplicates_are_not_positive_signals(self):
        self.assertEqual(service.sentiment('Reliance Industries denies record profit'), 0)
        self.assertEqual(service.sentiment('Reliance Industries profit falls'), -1)
        self.assertEqual(service.sentiment('Reliance Industries wins large contract'), 1)
        self.assertEqual(service.sentiment('Adani shares gain; Reliance Industries publishes report', 'Reliance Industries'), 0)
        self.assertEqual(service.sentiment('Reliance Industries falls Friday, underperforms market', 'Reliance Industries'), -1)
        story = article('Reliance Industries wins government contract')
        result = service.build_trend('RELIANCE.NS', history(), {}, {'articles': [story]}, {'articles': [story]}, {'history': None}, NOW)
        self.assertEqual(result['policy_news'], [])
        self.assertGreater(next(f for f in result['factors'] if f['id'] == 'news')['contribution'], 0)

    def test_relevant_but_unclassified_headline_does_not_invent_sentiment(self):
        score, stories = service.headline_signal({'articles': [article('Example publishes annual report')]}, NOW, 7)
        self.assertIsNone(score)
        self.assertEqual(stories[0]['signal'], 0)

    def test_short_history_rejected(self):
        with self.assertRaisesRegex(ValueError, '50 trading sessions'):
            service.build_trend('RELIANCE.NS', history().tail(49), {}, {}, {}, {}, NOW)

    def test_route_returns_one_trend_with_partial_sources(self):
        result = service.build_trend('RELIANCE.NS', history(), {}, {}, {}, {'history': None}, NOW)
        with patch.object(server, 'analyse_trend', return_value=result) as analyse:
            response = server.app.test_client().get('/data/trend/reliance')
        self.assertEqual(response.status_code, 200)
        analyse.assert_called_once_with('RELIANCE.NS')
        self.assertEqual(response.json['trend'], 'Insufficient evidence')
        self.assertEqual(server.app.test_client().get('/data/trend/unknown').status_code, 404)
