import type {
  SnapshotResponse,
  HierarchyScores,
  DeltaFrame,
  WeightSnapshot,
  WeightTrendPoint,
  WeightDeltaPoint,
  TrendPoint,
} from "@/store/useDateStore";

export type ScoringLevel = 0 | 1 | 2 | 3 | 4;
export type ScoringTab = "HISTORICAL" | "INTRADAY";
export type ViewMode = "SIMPLE" | "EXPERT";
export type DailyWindow = 30 | 90 | 365;
export type IntradayWindow = "6h" | "24h" | "7d";

export interface ChartWrapperBaseProps {
  className?: string;
  title?: string;
  emptyLabel?: string;
  minHeight?: number;
}

export interface SpiderChartWrapperProps extends ChartWrapperBaseProps {
  snapshot: SnapshotResponse | null;
  tier: "daily" | "hourly" | "current";
  level: ScoringLevel;
  parentKey?: string | null;
  size?: number;
  onLabelClick?: (label: string, item: { key: string; label: string; score: number; weight: number }) => void;
}

export interface TrendWrapperProps extends ChartWrapperBaseProps {
  series: TrendPoint[] | undefined | null;
  hierarchy: HierarchyScores | null | undefined;
  level: ScoringLevel;
  parentKey?: string | null;
  height?: number;
  showLegend?: boolean;
  windowLabel?: string;
}

export interface DeltaWrapperProps extends ChartWrapperBaseProps {
  deltaFrame: DeltaFrame | null | undefined;
  hierarchy: HierarchyScores | null | undefined;
  level: ScoringLevel;
  parentKey?: string | null;
  height?: number;
  includeL1Grid?: boolean;
  deltaLabel?: string;
  periodEndLabel?: string;
}

export interface WeightCurrentWrapperProps extends ChartWrapperBaseProps {
  weights: WeightSnapshot | null | undefined;
  level: ScoringLevel;
  parentKey?: string | null;
  height?: number;
}

export interface WeightTrendWrapperProps extends ChartWrapperBaseProps {
  weightTrends: WeightTrendPoint[] | undefined | null;
  weights: WeightSnapshot | null | undefined;
  level: ScoringLevel;
  parentKey?: string | null;
  height?: number;
  windowLabel?: string;
  showLegend?: boolean;
}

export interface WeightDeltaWrapperProps extends ChartWrapperBaseProps {
  weightDeltas: WeightDeltaPoint | null | undefined;
  weights: WeightSnapshot | null | undefined;
  level: ScoringLevel;
  parentKey?: string | null;
  height?: number;
}

export interface ViewHeaderControlsProps {
  scoringTab: ScoringTab;
  onScoringTabChange: (t: ScoringTab) => void;
  viewMode: ViewMode;
  onViewModeChange: (m: ViewMode) => void;
  windowDaily: DailyWindow;
  onWindowDailyChange: (w: DailyWindow) => void;
  windowIntraday: IntradayWindow;
  onWindowIntradayChange: (w: IntradayWindow) => void;
  className?: string;
}

export interface ScoringLevelSelectorProps {
  level: ScoringLevel;
  onLevelChange: (l: ScoringLevel) => void;
  className?: string;
  includeOverall?: boolean;
}

export interface ParentSelectorProps {
  hierarchy: HierarchyScores | null | undefined;
  level: ScoringLevel;
  parentLevel: Exclude<ScoringLevel, 0 | 4>;
  parentKey: string | null;
  onParentChange: (parentKey: string | null) => void;
  className?: string;
}
