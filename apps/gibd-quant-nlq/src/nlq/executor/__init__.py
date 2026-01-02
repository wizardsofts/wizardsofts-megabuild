"""Executor module for natural language queries."""

from src.nlq.executor.comparison_executor import ComparisonExecutor
from src.nlq.executor.threshold_executor import ThresholdExecutor
from src.nlq.executor.trend_executor import TrendExecutor

__all__ = ["TrendExecutor", "ThresholdExecutor", "ComparisonExecutor"]
