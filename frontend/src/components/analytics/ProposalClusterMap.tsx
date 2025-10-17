/**
 * 解決案クラスタマップコンポーネント
 * AIによるクラスタリングで、似ている意見をグループ化して表示
 */
'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ZAxis, ReferenceLine } from 'recharts';
import type { ProposalListItem } from '../../types/proposal';
import { getGenderDisplay } from '../../lib/countryFlags';
import CountryFlag from '../common/CountryFlag';

// クラスタデータポイント型
interface ClusterDataPoint {
  x: number; // 0-1の範囲
  y: number; // 0-1の範囲
  proposal_id: number;
  cluster: number;
  conclusion: string;
  proposer_name: string;
  anonymous_name: string; // 匿名名
  comment_count: number; // 影響度（コメント数）
  is_selected?: boolean; // 選出されたユーザーかどうか
  nationality?: string | null; // 国籍（選出されたユーザーのみ）
  gender?: string | null; // 性別（選出されたユーザーのみ）
  age?: number | null; // 年齢（選出されたユーザーのみ）
}

// クラスタ情報型
interface ClusterInfo {
  cluster_id: number;
  size: number;
  theme: string;
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

interface ClusteringResult {
  coordinates: ClusterDataPoint[];
  cluster_info: ClusterInfo[];
  total_clusters: number;
  axis_labels?: AxisLabels;
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


const ProposalClusterMap: React.FC<ProposalClusterMapProps> = ({
  challengeId,
  proposals,
  onProposalClick,
  selectedProposalId,
  onClusteringDataLoaded
}) => {
  const [clusteringData, setClusteringData] = useState<ClusteringResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // クラスタリング結果を取得
  useEffect(() => {
    const fetchClustering = async () => {
      try {
        setLoading(true);
        setError(null);

        const token = localStorage.getItem('access_token');
        
        const response = await fetch(
          `http://localhost:8000/api/analytics/challenges/${challengeId}/clustering/`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          }
        );
        

        if (!response.ok) {
          throw new Error('クラスタリング結果の取得に失敗しました');
        }

        const data = await response.json();
        console.log('クラスタリングAPI レスポンス:', data);
        console.log('座標データサンプル（属性情報付き）:', data.coordinates?.slice(0, 3));
        setClusteringData(data);
        
        // 親コンポーネントにクラスタリングデータを渡す
        if (onClusteringDataLoaded) {
          onClusteringDataLoaded(data);
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

  // 散布図用のデータを準備（0-100%の範囲に変換）
  const scatterData = useMemo(() => {
    if (!clusteringData) return [];
    
    // コメント数の統計を取得
    const commentCounts = clusteringData.coordinates.map(p => p.comment_count || 0);
    const maxComments = Math.max(...commentCounts);
    const minComments = Math.min(...commentCounts);
    
    
    return clusteringData.coordinates.map(point => {
      const commentCount = point.comment_count || 0;
      
      // コメント数に応じて点の大きさを決定（面積ベース）
      // 最小半径4、最大半径12の範囲でスケーリング
      let radius;
      if (maxComments === minComments) {
        // 全て同じコメント数の場合
        radius = 6;
      } else if (commentCount === 0) {
        // コメントなしは最小サイズ
        radius = 4;
      } else {
        // 線形スケーリング（半径）
        radius = 4 + ((commentCount - minComments) / (maxComments - minComments)) * 8;
      }
      
      // 面積に変換（πr²）
      const scaledSize = Math.PI * radius * radius;
      
      const finalX = point.x * 100;
      const finalY = 100 - (point.y * 100); // Y軸を反転（Rechartsの座標系に合わせる）
      
      
      return {
        ...point,
        x: finalX, // 0-1を0-100に変換
        y: finalY, // 0-1を0-100に変換
        z: scaledSize,
        radius: radius, // 半径を直接保存
        comment_count: commentCount
      };
    });
  }, [clusteringData]);


  // カスタムツールチップ
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as ClusterDataPoint;
      const cluster = clusteringData?.cluster_info.find(c => c.cluster_id === data.cluster);
      
      return (
        <div className="bg-white border-2 border-gray-300 rounded-lg shadow-xl p-4 max-w-xs">
          <p className="font-semibold text-gray-900 mb-1">{data.anonymous_name}</p>
          
          {/* 選出されたユーザーの属性情報 */}
          {data.is_selected && (data.nationality || data.gender || data.age) && (
            <div className="flex items-center gap-2 text-sm text-gray-700 mb-2">
              {data.nationality && (
                <CountryFlag countryCode={data.nationality} size="medium" />
              )}
              {data.gender && (
                <span>{getGenderDisplay(data.gender)}</span>
              )}
              {data.age && (
                <span>{data.age}歳</span>
              )}
            </div>
          )}
          
          <p className="text-sm text-gray-700 mb-2 line-clamp-3">{data.conclusion}</p>
          <div className="flex items-center gap-4 text-xs text-gray-600">
            {cluster && (
              <div>
                <span className="font-medium">グループ: </span>
                <span>{cluster.theme}</span>
              </div>
            )}
            <div>
              <span className="font-medium">💬 コメント: </span>
              <span>{data.comment_count}件</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
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

      {/* 説明 */}
      <div className="mb-4 p-4 bg-blue-50 rounded-lg text-sm text-gray-700">
        <p className="font-medium mb-2">💡 このマップについて</p>
        <ul className="space-y-1 text-xs">
          <li>• <strong>位置</strong>：プロットされた点同士が近いほど解決案の内容が類似し、プロットされた点が中央に近いほど解決案の内容の独創性が低く、離れるほど独創性が高いことを表しています</li>
          <li>• <strong>色</strong>：色で解決案のグループを表しています</li>
          <li>• <strong>大きさ</strong>：大きさで解決案に対するコメント数の多さを表しています</li>
        </ul>
      </div>
      
      <ResponsiveContainer width="100%" height={600}>
        <ScatterChart
          margin={{ top: 20, right: 20, bottom: 60, left: 80 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          
          {/* 十字の灰色の線（X軸・Y軸）を中央に描画 */}
          <ReferenceLine x={50} stroke="#9CA3AF" strokeWidth={2} strokeDasharray="5 5" />
          <ReferenceLine y={50} stroke="#9CA3AF" strokeWidth={2} strokeDasharray="5 5" />
          
          <XAxis
            type="number"
            dataKey="x"
            name="X座標"
            domain={[0, 100]}
            ticks={[]}
            hide={true}
          />
          
          <YAxis
            type="number"
            dataKey="y"
            name="Y座標"
            domain={[0, 100]}
            ticks={[]}
            hide={true}
          />
          
          <ZAxis type="number" dataKey="z" range={[200, 1200]} />
          
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          
          
          {/* 解決案の点（RechartsのScatterコンポーネントを使用） */}
          <Scatter data={scatterData}>
            {scatterData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={CLUSTER_COLORS[entry.cluster % CLUSTER_COLORS.length]}
                opacity={entry.proposal_id === selectedProposalId ? 1 : 0.8}
                stroke={entry.proposal_id === selectedProposalId ? '#1F2937' : 'transparent'}
                strokeWidth={entry.proposal_id === selectedProposalId ? 4 : 0}
                style={{ 
                  cursor: 'pointer',
                  filter: 'none',
                  boxShadow: 'none',
                  dropShadow: 'none',
                  outline: 'none',
                  border: 'none'
                }}
                onClick={() => onProposalClick(entry.proposal_id, {
                  nationality: entry.nationality,
                  gender: entry.gender,
                  age: entry.age,
                  is_selected: entry.is_selected
                })}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* クラスタ凡例 */}
      <div className="mt-6 border-t pt-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">グループ分類（{clusteringData.total_clusters}グループ）</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {clusteringData.cluster_info.map((cluster) => (
            <div
              key={cluster.cluster_id}
              className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg"
            >
              <div
                className="w-4 h-4 rounded-full flex-shrink-0"
                style={{ backgroundColor: CLUSTER_COLORS[cluster.cluster_id % CLUSTER_COLORS.length] }}
              ></div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{cluster.theme}</p>
                <p className="text-xs text-gray-600">{cluster.size}件</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProposalClusterMap;

