/**
 * Chart Components Index
 *
 * LEARNING MODULE 5: CHARTS AND VISUALIZATION
 * -------------------------------------------
 * This barrel file exports all chart components.
 *
 * Key concept:
 * **Barrel exports** let you import multiple components from one place:
 *
 * Instead of:
 *   import { SignalDistributionChart } from "@/components/charts/SignalDistributionChart";
 *   import { ScoreHistogramChart } from "@/components/charts/ScoreHistogramChart";
 *
 * You can write:
 *   import { SignalDistributionChart, ScoreHistogramChart } from "@/components/charts";
 *
 * File path: frontend/components/charts/index.ts
 */

export { SignalDistributionChart } from "./SignalDistributionChart";
export { ScoreHistogramChart } from "./ScoreHistogramChart";
export { SectorPerformanceChart } from "./SectorPerformanceChart";
