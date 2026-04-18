/**
 * ProposalClusterMap - 解決案クラスタマップ（Polis風）
 *
 * 【表示の意味】選出基準は非表示（率直な意見収集のため）
 * - ×印：グループの中心
 * - 合意ゾーン内：合意に近い
 * - 円の外側：独創的
 * - オーラ：影響度
 *
 * 【操作】ズーム・パン・ホバー・クリック
 */
'use client';

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, ZAxis } from 'recharts';
import type { ProposalListItem } from '../../types/proposal';
import { getGenderDisplay } from '../../lib/countryFlags';
import CountryFlag from '../common/CountryFlag';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

// ========== 型定義 ==========
export interface ClusterDataPoint {
  x: number; // 0-1の範囲
  y: number; // 0-1の範囲
  proposal_id: number;
  cluster: number;
  conclusion: string;
  proposer_name: string;
  anonymous_name: string; // 匿名名
  comment_count: number;
  impact_score?: number; // 影響度スコア（0-1、オーラの大きさに使用）
  innovation_score?: number | null; // 独創性スコア（×からの距離と同一基準、「最も独創的」選出と一致）
  is_selected?: boolean; // 選出されたユーザーかどうか
  nationality?: string | null; // 国籍（選出されたユーザーのみ）
  gender?: string | null; // 性別（選出されたユーザーのみ）
  age?: number | null; // 年齢（選出されたユーザーのみ）
}

// クラスタ重心型（独創性の参照点）
interface ClusterCentroid {
  cluster_id: number;
  x: number;
  y: number;
}

// クラスタ情報型
interface ClusterInfo {
  cluster_id: number;
  size: number;
  theme: string;
  main_points_summary?: string;
}

interface AxisLabels {
  x_axis: {
    left: string;
    right: string;
  };
  y_axis: {
    left: string;
    right: string;
  };
}

export interface ClusteringResult {
  coordinates: ClusterDataPoint[];
  cluster_info: ClusterInfo[];
  cluster_centroids?: ClusterCentroid[];
  total_clusters: number;
  axis_labels?: AxisLabels;
  balance_summary?: string;
  majority_minority_summary?: string;
  cluster_comparison?: {
    similar_points?: string[];
    different_points?: string[];
  };
  most_original_proposal_id?: number;
  most_original_innovation_score?: number;
  /** エラー応答時など */
  error?: string;
}

interface ProposalClusterMapProps {
  challengeId: number;
  proposals: ProposalListItem[];
  onProposalClick: (proposalId: number, attributes?: {
    nationality?: string | null;
    gender?: string | null;
    age?: number | null;
    is_selected?: boolean;
  }) => void;
  selectedProposalId?: number | null;
  onClusteringDataLoaded?: (data: ClusteringResult) => void;
}

// クラスタごとの色（エクスポート）
export const CLUSTER_COLORS = [
  '#3B82F6', // 青
  '#10B981', // 緑
  '#F59E0B', // オレンジ
  '#EF4444', // 赤
  '#8B5CF6', // 紫
  '#EC4899', // ピンク
  '#14B8A6', // ティール
  '#F97316', // ダークオレンジ
];

const CHART_HEIGHT = 600;
const ZOOM_MIN = 1;
const ZOOM_MAX = 3;  // ズームイン最大3回（1→2→3）
const ZOOM_DELTA = 0.2;
const DRAG_THRESHOLD_PX = 5;
const POINT_RADIUS = 6;
const AURA_RADIUS_MIN = 8;
const AURA_RADIUS_MAX = 28;
const CENTROID_SIZE = 8;

// ========== 描画用サブコンポーネント ==========
/** クラスタ色の薄い版（オーラ用） */
function getClusterLightColor(hex: string, alpha = 0.35): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/** クラスタ重心を×印で描画。合意ゾーン（×付近＝合意に近い）の円も描画 */
function CentroidShape(props: { cx?: number; cy?: number; payload?: { cluster_id: number; zoneRadius?: number } }) {
  const { cx = 0, cy = 0, payload } = props;
  if (!payload) return null;
  const color = CLUSTER_COLORS[payload.cluster_id % CLUSTER_COLORS.length];
  const zoneRadius = payload.zoneRadius ?? 0;
  const lightColor = getClusterLightColor(color, 0.2);
  return (
    <g pointerEvents="none">
      {/* 合意ゾーン：×付近の薄い円（この中＝合意に近い・平均的な解決案） */}
      {zoneRadius > 0 && (
        <circle cx={cx} cy={cy} r={zoneRadius} fill={lightColor} stroke={color} strokeWidth={1} strokeDasharray="4 2" opacity={0.6} />
      )}
      {/* ×印：グループの中心（平均的な位置） */}
      <line x1={cx - CENTROID_SIZE} y1={cy - CENTROID_SIZE} x2={cx + CENTROID_SIZE} y2={cy + CENTROID_SIZE} stroke={color} strokeWidth={2} />
      <line x1={cx + CENTROID_SIZE} y1={cy - CENTROID_SIZE} x2={cx - CENTROID_SIZE} y2={cy + CENTROID_SIZE} stroke={color} strokeWidth={2} />
    </g>
  );
}

/** 最小ヒット半径（クリックしやすさのため、オーラより大きく確保） */
const MIN_HIT_RADIUS = 16;

/** 点＋オーラを描画するカスタムシェイプ（影響度＝オーラの大きさ、ヒット領域は拡張） */
function PointWithAuraShape(props: {
  cx?: number;
  cy?: number;
  payload?: { cluster: number; auraRadius?: number; pointRadius?: number; proposal_id: number };
  selectedProposalId?: number | null;
  onProposalClick?: (proposalId: number, attrs?: object) => void;
  onClickAttrs?: object;
}) {
  const { cx = 0, cy = 0, payload } = props;
  if (!payload) return null;
  const clusterColor = CLUSTER_COLORS[payload.cluster % CLUSTER_COLORS.length];
  const auraColor = getClusterLightColor(clusterColor);
  const auraR = payload.auraRadius ?? 12;
  const pointR = payload.pointRadius ?? 6;
  const hitR = Math.max(auraR, MIN_HIT_RADIUS);
  const isSelected = payload.proposal_id === props.selectedProposalId;

  return (
    <g
      cursor="pointer"
      onClick={() => props.onProposalClick?.(payload.proposal_id, props.onClickAttrs)}
    >
      {/* ヒット領域：透明の大きい円（オーラ非縮小のまま、全点クリックしやすく） */}
      <circle cx={cx} cy={cy} r={hitR} fill="transparent" stroke="none" />
      {/* オーラ：影響度に応じた大きさの円（薄いクラスタ色） */}
      <circle cx={cx} cy={cy} r={auraR} fill={auraColor} stroke="none" pointerEvents="none" />
      {/* 点：均一サイズの円（クラスタ色、ヒットは外側の透明円で受ける） */}
      <circle
        cx={cx}
        cy={cy}
        r={pointR}
        pointerEvents="none"
        fill={clusterColor}
        fillOpacity={isSelected ? 1 : 0.8}
        stroke={isSelected ? '#1F2937' : 'transparent'}
        strokeWidth={isSelected ? 4 : 0}
      />
    </g>
  );
}


// ========== メインコンポーネント ==========
const ProposalClusterMap: React.FC<ProposalClusterMapProps> = ({
  challengeId,
  proposals,
  onProposalClick,
  selectedProposalId,
  onClusteringDataLoaded
}) => {
  void proposals;
  const onClusteringDataLoadedRef = useRef(onClusteringDataLoaded);
  const [clusteringData, setClusteringData] = useState<ClusteringResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // ズーム・パン状態
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragStart = useRef<{ x: number; y: number; panX: number; panY: number; started?: boolean } | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    onClusteringDataLoadedRef.current = onClusteringDataLoaded;
  }, [onClusteringDataLoaded]);

  // --- データ取得 ---
  useEffect(() => {
    const fetchClustering = async () => {
      try {
        setLoading(true);
        setError(null);

        const token = localStorage.getItem('access_token');
        
        const response = await fetch(
          `${API_BASE_URL}/analytics/challenges/${challengeId}/clustering/`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          }
        );
        

        let data: ClusteringResult;
        try {
          data = (await response.json()) as ClusteringResult;
        } catch {
          data = { coordinates: [], cluster_info: [], total_clusters: 0 };
        }

        if (!response.ok) {
          const errorMessage = data?.error || `クラスタリング結果の取得に失敗しました（${response.status}）`;
          throw new Error(errorMessage);
        }
        setClusteringData(data);
        
        // 親コンポーネントにクラスタリングデータを渡す
        if (onClusteringDataLoadedRef.current) {
          onClusteringDataLoadedRef.current(data);
        }
      } catch (err) {
        console.error('クラスタリングエラー:', err);
        setError(err instanceof Error ? err.message : 'エラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchClustering();
  }, [challengeId]);

  // ズーム・パン操作（ホイールでズーム、ドラッグでパン）
  const zoomContainerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = zoomContainerRef.current;
    if (!el) return;
    const fn = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -ZOOM_DELTA : ZOOM_DELTA;
      setZoom((z) => Math.min(4, Math.max(1, z + delta)));
    };
    el.addEventListener('wheel', fn, { passive: false });
    return () => el.removeEventListener('wheel', fn);
  }, []);
  useEffect(() => {
    if (zoom <= 1) setPan({ x: 0, y: 0 });  // 初期状態ではパンをリセット
  }, [zoom]);
  const maxPan = (zoom - 1) * (CHART_HEIGHT / 2);
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0 && zoom > ZOOM_MIN) {
      dragStart.current = { x: e.clientX, y: e.clientY, panX: pan.x, panY: pan.y, started: false };
    }
  }, [pan, zoom]);
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragStart.current && zoom > 1) {
      const dx = e.clientX - dragStart.current.x;
      const dy = e.clientY - dragStart.current.y;
      if (!dragStart.current.started && (Math.abs(dx) > DRAG_THRESHOLD_PX || Math.abs(dy) > DRAG_THRESHOLD_PX)) {
        dragStart.current.started = true;
        setIsDragging(true);
      }
      if (dragStart.current.started) {
        const newPanX = Math.max(-maxPan, Math.min(maxPan, dragStart.current.panX + dx));
        const newPanY = Math.max(-maxPan, Math.min(maxPan, dragStart.current.panY + dy));
        setPan({ x: newPanX, y: newPanY });
      }
    }
  }, [zoom, maxPan]);
  const handleMouseUp = useCallback(() => { dragStart.current = null; setIsDragging(false); }, []);
  const handleMouseLeave = useCallback(() => { dragStart.current = null; setIsDragging(false); }, []);

  // --- 散布図データ（座標0-1→0-100、影響度→オーラ半径） ---
  const scatterData = useMemo(() => {
    if (!clusteringData) return [];

    const hasImpactScore = clusteringData.coordinates.some(p => typeof (p as ClusterDataPoint).impact_score === 'number');
    const values = hasImpactScore
      ? clusteringData.coordinates.map(p => (p as ClusterDataPoint).impact_score ?? 0)
      : clusteringData.coordinates.map(p => p.comment_count || 0);
    const maxVal = Math.max(...values, 0.001);
    const minVal = Math.min(...values);

    return clusteringData.coordinates.map(point => {
      const rawVal = hasImpactScore
        ? ((point as ClusterDataPoint).impact_score ?? 0)
        : (point.comment_count || 0);
      const scaledSize = Math.PI * POINT_RADIUS * POINT_RADIUS;
      let auraRadius: number;
      if (maxVal <= minVal) {
        auraRadius = (AURA_RADIUS_MIN + AURA_RADIUS_MAX) / 2;
      } else if (rawVal === 0) {
        auraRadius = AURA_RADIUS_MIN;
      } else {
        auraRadius = AURA_RADIUS_MIN + ((rawVal - minVal) / (maxVal - minVal)) * (AURA_RADIUS_MAX - AURA_RADIUS_MIN);
      }

      const finalX = point.x * 100;
      const finalY = 100 - (point.y * 100);

      return {
        ...point,
        x: finalX,
        y: finalY,
        z: scaledSize,
        pointRadius: POINT_RADIUS,
        auraRadius,
        comment_count: point.comment_count || 0
      };
    });
  }, [clusteringData]);

  // 重心データ＋合意ゾーン半径（クラスタ内で×に近い方から約33%が含まれる半径）
  const centroidData = useMemo(() => {
    if (!clusteringData?.cluster_centroids?.length || !scatterData.length) return [];
    const centroids = clusteringData.cluster_centroids.map(c => ({
      cx: c.x * 100,
      cy: 100 - (c.y * 100),
      cluster_id: c.cluster_id,
    }));
    return centroids.map(({ cx, cy, cluster_id }) => {
      const clusterPoints = scatterData.filter((p: { cluster: number }) => p.cluster === cluster_id);
      const distances = clusterPoints.map((p: { x: number; y: number }) =>
        Math.hypot(p.x - cx, p.y - cy)
      ).sort((a: number, b: number) => a - b);
      const p33Index = Math.floor(distances.length * 0.33);
      const rawRadius = distances.length > 0 ? distances[Math.max(0, p33Index)] : 8;
      const zoneRadius = Math.max(6, Math.min(rawRadius, 25));
      return {
        x: cx,
        y: cy,
        z: 100,
        cluster_id,
        zoneRadius,
        isCentroid: true,
      };
    });
  }, [clusteringData, scatterData]);


  // カスタムツールチップ（解決案の点のみ表示。重心×印は表示しない）
  type TooltipRow = { payload: ClusterDataPoint & { cluster_id?: number; isCentroid?: boolean } };
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: TooltipRow[] }) => {
    if (!active || !payload?.length) return null;
    // 複数Scatterで重心と解決案が重なる場合、解決案のペイロードを優先（proposal_id があるもの）
    const data = payload
      .map((p) => p.payload)
      .find((d) => d.proposal_id != null && !d.isCentroid);
    if (!data) return null;
    const displayName = data.anonymous_name || data.proposer_name || '匿名';
    return (
      <div className="bg-white border-2 border-gray-300 rounded-lg shadow-xl p-3 max-w-xs">
        <p className="font-semibold text-gray-900 mb-1">{displayName}</p>
        {(data.nationality || data.gender || data.age != null) ? (
          <div className="flex items-center gap-2 text-sm text-gray-700">
            {data.nationality && (
              <CountryFlag countryCode={data.nationality} size="medium" />
            )}
            {data.gender && <span>{getGenderDisplay(data.gender)}</span>}
            {data.age != null && <span>{data.age}歳</span>}
          </div>
        ) : null}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">AIが解決案を分析中...</p>
            <p className="text-sm text-gray-500 mt-2">初回は時間がかかる場合があります</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !clusteringData) {
    return (
      <div className="bg-white rounded-lg border border-red-200 p-6">
        <div className="text-center text-red-600">
          <p className="font-medium mb-2">⚠️ クラスタリングに失敗しました</p>
          <p className="text-sm">{error || '不明なエラー'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">🤖 AI解決案マップ（クラスタリング）</h3>
      <p className="text-sm text-gray-600 mb-4">
        AIが解決案の内容を分析し、似ている意見をグループ化しています。各点をクリックすると詳細が表示されます。
      </p>

      {/* 説明（選出基準は示さない：率直な意見収集のため） */}
      <div className="mb-4 p-4 bg-blue-50 rounded-lg text-sm text-gray-700 text-left">
        <p className="font-medium mb-2">💡 このマップについて</p>
        <ul className="space-y-1.5 text-sm">
          <li>・<span className="ml-1.5"><strong>×印付近の点</strong>：合意に近い解決案です。暗黙の共通点が多く、合意に近い内容であることを表します。</span></li>
          <li>・<span className="ml-1.5"><strong>×印から離れた点</strong>：独創的な解決案です。他と異なる視点やアイデアを含む解決案を示します。</span></li>
          <li>・<span className="ml-1.5"><strong>オーラ</strong>：影響度の大きさを表します。コメント数や議論の広がりが大きいほどオーラが大きくなります。</span></li>
          <li>・<span className="ml-1.5"><strong>色</strong>：グループ（類似した意見のまとまり）を表します。同じ色の点は内容が近い解決案です。</span></li>
        </ul>
      </div>
      {/* 散布図エリア（ズーム・パン対応） */}
      <div
        ref={zoomContainerRef}
        className="relative border border-gray-200 rounded-lg overflow-hidden bg-gray-50 w-full select-none"
        style={{ height: CHART_HEIGHT, cursor: zoom > ZOOM_MIN ? (isDragging ? 'grabbing' : 'grab') : 'default' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
      >
        <div className="absolute top-2 right-2 z-10 flex flex-col gap-1" onMouseDown={(e) => e.stopPropagation()}>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setZoom((z) => Math.min(ZOOM_MAX, z + 1)); }}
            className="w-8 h-8 rounded bg-white border border-gray-300 shadow-sm hover:bg-gray-50 text-gray-600 text-lg leading-none"
            title="ズームイン"
          >
            +
          </button>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); if (zoom > 1) setZoom((z) => Math.max(1, z - 1)); }}
            disabled={zoom <= 1}
            className={`w-8 h-8 rounded border text-lg leading-none ${
              zoom <= 1
                ? 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-white border-gray-300 hover:bg-gray-50 text-gray-600'
            }`}
            title="ズームアウト（初期状態が最小）"
          >
            −
          </button>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setZoom(ZOOM_MIN); setPan({ x: 0, y: 0 }); }}
            className="w-8 h-8 rounded bg-white border border-gray-300 shadow-sm hover:bg-gray-50 text-gray-600 text-xs"
            title="リセット"
          >
            ⟲
          </button>
        </div>
        <div
          style={{
            width: '100%',
            height: CHART_HEIGHT,
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center'
          }}
        >
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <ScatterChart margin={{ top: 20, right: 60, bottom: 60, left: 60 }}>
            <XAxis type="number" dataKey="x" domain={[0, 100]} ticks={[]} hide />
            <YAxis type="number" dataKey="y" domain={[0, 100]} ticks={[]} hide />
            <ZAxis type="number" dataKey="z" range={[200, 1200]} />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
            {/* クラスタ重心（×印）：独創性の参照点 */}
            {centroidData.length > 0 && (
              <Scatter
                data={centroidData}
                shape={(p: { cx?: number; cy?: number; payload?: { cluster_id: number } }) => (
                  <CentroidShape {...p} />
                )}
              />
            )}
            {/* 解決案の点：均一サイズ＋影響度オーラ */}
            <Scatter
              data={scatterData}
              shape={(props: { cx?: number; cy?: number; payload?: unknown }) => {
                const p = props.payload as ClusterDataPoint | undefined;
                return (
                  <PointWithAuraShape
                    cx={props.cx}
                    cy={props.cy}
                    payload={p}
                    selectedProposalId={selectedProposalId}
                    onProposalClick={onProposalClick}
                    onClickAttrs={p ? {
                      nationality: p.nationality,
                      gender: p.gender,
                      age: p.age,
                      is_selected: p.is_selected
                    } : undefined}
                  />
                );
              }}
            />
          </ScatterChart>
        </ResponsiveContainer>
        </div>
      </div>

      {/* グループ分類：各グループの名前・テーマ（1グループ1キーワード） */}
      <div className="mt-6 border-t pt-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-1">グループ分類</h4>
        <p className="text-xs text-gray-600 mb-3">各グループが「何についての意見か」を、1グループ1つのキーワード・テーマで示しています。</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {clusteringData.cluster_info.map((cluster) => (
            <div
              key={cluster.cluster_id}
              className="p-3 bg-gray-50 rounded-lg border border-gray-200 flex items-center gap-2"
            >
              <div
                className="w-4 h-4 rounded-full flex-shrink-0"
                style={{ backgroundColor: CLUSTER_COLORS[cluster.cluster_id % CLUSTER_COLORS.length] }}
              />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-gray-500">キーワード</p>
                <p className="text-sm font-medium text-gray-900">{cluster.theme}</p>
              </div>
              <span className="text-xs text-gray-500 flex-shrink-0">{cluster.size}件</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProposalClusterMap;

