"""Executor module for natural language queries."""

from nlq.executor.comparison_executor import ComparisonExecutor
from nlq.executor.threshold_executor import ThresholdExecutor
from nlq.executor.trend_executor import TrendExecutor

__all__ = ["TrendExecutor", "ThresholdExecutor", "ComparisonExecutor"]
