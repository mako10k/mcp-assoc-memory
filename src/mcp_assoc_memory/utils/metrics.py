"""
メトリクス収集基盤
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import time


@dataclass
class MetricValue:
    """メトリクス値"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class CounterMetric:
    """カウンターメトリクス"""
    name: str
    description: str
    value: int = 0
    labels: Dict[str, str] = field(default_factory=dict)

    def increment(self, amount: int = 1):
        """カウンターを増加"""
        self.value += amount


@dataclass
class GaugeMetric:
    """ゲージメトリクス"""
    name: str
    description: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)

    def set(self, value: float):
        """値を設定"""
        self.value = value

    def increment(self, amount: float = 1.0):
        """値を増加"""
        self.value += amount

    def decrement(self, amount: float = 1.0):
        """値を減少"""
        self.value -= amount


@dataclass
class HistogramMetric:
    """ヒストグラムメトリクス"""
    name: str
    description: str
    buckets: List[float] = field(
        default_factory=lambda: [
            0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
    bucket_counts: Dict[float, int] = field(default_factory=dict)
    sum_value: float = 0.0
    count: int = 0
    labels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """初期化後処理"""
        for bucket in self.buckets:
            self.bucket_counts[bucket] = 0

    def observe(self, value: float):
        """値を観測"""
        self.sum_value += value
        self.count += 1

        for bucket in self.buckets:
            if value <= bucket:
                self.bucket_counts[bucket] += 1


class MetricsCollector:
    """メトリクス収集器"""

    def __init__(self, retention_period: timedelta = timedelta(hours=24)):
        self.retention_period = retention_period
        self.counters: Dict[str, CounterMetric] = {}
        self.gauges: Dict[str, GaugeMetric] = {}
        self.histograms: Dict[str, HistogramMetric] = {}
        self.time_series: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000))
        self.lock = threading.RLock()

    def counter(self, name: str, description: str = "",
                labels: Dict[str, str] = None) -> CounterMetric:
        """カウンターメトリクスを取得または作成"""
        key = self._generate_key(name, labels or {})

        with self.lock:
            if key not in self.counters:
                self.counters[key] = CounterMetric(
                    name=name,
                    description=description,
                    labels=labels or {}
                )
            return self.counters[key]

    def gauge(self, name: str, description: str = "",
              labels: Dict[str, str] = None) -> GaugeMetric:
        """ゲージメトリクスを取得または作成"""
        key = self._generate_key(name, labels or {})

        with self.lock:
            if key not in self.gauges:
                self.gauges[key] = GaugeMetric(
                    name=name,
                    description=description,
                    labels=labels or {}
                )
            return self.gauges[key]

    def histogram(self,
                  name: str,
                  description: str = "",
                  labels: Dict[str,
                               str] = None,
                  buckets: List[float] = None) -> HistogramMetric:
        """ヒストグラムメトリクスを取得または作成"""
        key = self._generate_key(name, labels or {})

        with self.lock:
            if key not in self.histograms:
                self.histograms[key] = HistogramMetric(
                    name=name,
                    description=description,
                    labels=labels or {},
                    buckets=buckets or [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
                )
            return self.histograms[key]

    def time_series_value(self, name: str, value: float,
                          labels: Dict[str, str] = None):
        """時系列値を記録"""
        key = self._generate_key(name, labels or {})

        with self.lock:
            self.time_series[key].append(MetricValue(
                timestamp=datetime.utcnow(),
                value=value,
                labels=labels or {}
            ))

    def _generate_key(self, name: str, labels: Dict[str, str]) -> str:
        """メトリクスキーを生成"""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_metrics_summary(self) -> Dict[str, Any]:
        """メトリクス概要を取得"""
        with self.lock:
            summary = {
                "counters": {
                    key: {
                        "name": metric.name,
                        "description": metric.description,
                        "value": metric.value,
                        "labels": metric.labels
                    }
                    for key, metric in self.counters.items()
                },
                "gauges": {
                    key: {
                        "name": metric.name,
                        "description": metric.description,
                        "value": metric.value,
                        "labels": metric.labels
                    }
                    for key, metric in self.gauges.items()
                },
                "histograms": {
                    key: {
                        "name": metric.name,
                        "description": metric.description,
                        "count": metric.count,
                        "sum": metric.sum_value,
                        "average": metric.sum_value / metric.count if metric.count > 0 else 0,
                        "bucket_counts": metric.bucket_counts,
                        "labels": metric.labels
                    }
                    for key, metric in self.histograms.items()
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            return summary

    def cleanup_old_data(self):
        """古いデータをクリーンアップ"""
        cutoff_time = datetime.utcnow() - self.retention_period

        with self.lock:
            for key, values in self.time_series.items():
                # 古い値を削除
                while values and values[0].timestamp < cutoff_time:
                    values.popleft()


class PerformanceMetrics:
    """パフォーマンスメトリクス"""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def record_memory_operation(
            self,
            operation: str,
            duration_ms: float,
            success: bool = True):
        """記憶操作のメトリクスを記録"""
        # 操作カウント
        counter = self.collector.counter(
            "memory_operations_total", "Total number of memory operations", {
                "operation": operation, "status": "success" if success else "error"})
        counter.increment()

        # 操作時間
        histogram = self.collector.histogram(
            "memory_operation_duration_ms",
            "Duration of memory operations in milliseconds",
            {"operation": operation}
        )
        histogram.observe(duration_ms)

    def record_search_operation(
            self,
            domain: str,
            result_count: int,
            duration_ms: float):
        """検索操作のメトリクスを記録"""
        # 検索カウント
        counter = self.collector.counter(
            "search_operations_total",
            "Total number of search operations",
            {"domain": domain}
        )
        counter.increment()

        # 検索時間
        histogram = self.collector.histogram(
            "search_duration_ms",
            "Duration of search operations in milliseconds",
            {"domain": domain}
        )
        histogram.observe(duration_ms)

        # 結果数
        histogram = self.collector.histogram(
            "search_result_count",
            "Number of search results",
            {"domain": domain},
            buckets=[1, 5, 10, 25, 50, 100, 250, 500]
        )
        histogram.observe(result_count)

    def record_embedding_operation(
            self,
            model: str,
            text_length: int,
            duration_ms: float):
        """埋め込み生成のメトリクスを記録"""
        # 埋め込み生成カウント
        counter = self.collector.counter(
            "embedding_operations_total",
            "Total number of embedding operations",
            {"model": model}
        )
        counter.increment()

        # 生成時間
        histogram = self.collector.histogram(
            "embedding_duration_ms",
            "Duration of embedding generation in milliseconds",
            {"model": model}
        )
        histogram.observe(duration_ms)

        # テキスト長
        histogram = self.collector.histogram(
            "embedding_text_length",
            "Length of text for embedding generation",
            {"model": model},
            buckets=[100, 500, 1000, 2000, 5000, 10000]
        )
        histogram.observe(text_length)


# グローバルメトリクス収集器
_global_collector = MetricsCollector()
_global_performance_metrics = PerformanceMetrics(_global_collector)


def get_metrics_collector() -> MetricsCollector:
    """グローバルメトリクス収集器を取得"""
    return _global_collector


def get_performance_metrics() -> PerformanceMetrics:
    """グローバルパフォーマンスメトリクスを取得"""
    return _global_performance_metrics
