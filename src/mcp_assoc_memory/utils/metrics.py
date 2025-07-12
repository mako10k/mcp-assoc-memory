"""
メトリクス収集基盤
"""
import time
from typing import Any, Dict, Callable


class MetricsCollector:
    def __init__(self) -> None:
        self.metrics: Dict[str, Any] = {}

    def record(self, name: str, value: Any) -> None:
        self.metrics[name] = value

    def increment(self, name: str, amount: int = 1) -> None:
        self.metrics[name] = self.metrics.get(name, 0) + amount

    def timer(self, name: str) -> Callable[[], None]:
        start = time.time()

        def done() -> None:
            self.metrics[name] = time.time() - start
        return done

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics


metrics = MetricsCollector()
