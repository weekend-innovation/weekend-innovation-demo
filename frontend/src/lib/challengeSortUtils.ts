/**
 * 課題一覧のソート・状態判定
 * - 募集終了後に相当するリスト: deadline の新しい順、同日は作成の新しい順
 * - 募集中・投稿者: deadline が近い順
 * - 募集中・提案者: やるべきアクション順、次フェーズ終了まで近い順
 */

export interface SortableChallenge {
  deadline: string;
  created_at: string;
  status?: string;
  current_phase?: string;
  proposal_deadline?: string;
  edit_deadline?: string;
  evaluation_deadline?: string;
  has_proposed?: boolean;
  has_completed_all_evaluations?: boolean;
}

/** 募集終了が直近の課題ほど先頭（同一 deadline は作成の新しい順） */
export function sortExpiredChallenges<T extends SortableChallenge>(challenges: T[]): T[] {
  return [...challenges].sort((a, b) => {
    const da = new Date(a.deadline).getTime();
    const db = new Date(b.deadline).getTime();
    if (db !== da) return db - da; // 全体期限の新しい順
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime(); // 同一期限は投稿の新しい順
  });
}

/** 募集中（投稿者）: 全体期限が近い順、同一期限は投稿の新しい順 */
export function sortActiveContributorChallenges<T extends SortableChallenge>(challenges: T[]): T[] {
  return [...challenges].sort((a, b) => {
    const da = new Date(a.deadline).getTime();
    const db = new Date(b.deadline).getTime();
    if (da !== db) return da - db; // 期限が近い順
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime(); // 同一期限は投稿の新しい順
  });
}

/** 次のフェーズまでのミリ秒（少ないほど「次のフェーズに近い」） */
function msUntilNextPhase(c: SortableChallenge): number {
  const now = Date.now();
  const p = c.current_phase;
  if (p === 'proposal' && c.proposal_deadline) return new Date(c.proposal_deadline).getTime() - now;
  if (p === 'edit' && c.edit_deadline) return new Date(c.edit_deadline).getTime() - now;
  if (p === 'evaluation' && c.evaluation_deadline) return new Date(c.evaluation_deadline).getTime() - now;
  return Infinity;
}

/**
 * 提案者について「満了扱いと同等の失格」か（※関数名は isProposerFailed）
 * - 提案期間が終了したのに未提案
 * - 評価期間が終了したのに評価未完了（編集期間の編集は任意のため対象外）
 */
export function isProposerFailed(c: SortableChallenge): boolean {
  const now = Date.now();
  const proposed = !!c.has_proposed;
  const completed = !!c.has_completed_all_evaluations;
  if (c.proposal_deadline && now > new Date(c.proposal_deadline).getTime() && !proposed) return true;
  if (c.evaluation_deadline && proposed && !completed && now > new Date(c.evaluation_deadline).getTime()) return true;
  return false;
}

/** 提案済みかつ評価完了か（フェーズ／status が closed・completed のときは false） */
export function isAllPhasesCompleted(c: SortableChallenge): boolean {
  if (c.current_phase === 'closed' || c.status === 'closed' || c.status === 'completed')
    return false;
  return !!(c.has_proposed && c.has_completed_all_evaluations);
}

/**
 * 全体の deadline が過ぎているか（status 未更新のフォールバック用）
 */
export function isDeadlinePassed(c: SortableChallenge): boolean {
  if (!c.deadline) return false;
  return new Date(c.deadline).getTime() < Date.now();
}

/** 投稿者視点で募集が終了扱いか（status または deadline 超過） */
export function isContributorExpired(c: SortableChallenge): boolean {
  return c.status === 'closed' || c.status === 'completed' || isDeadlinePassed(c);
}

/**
 * 提案者について「満了扱い」か（全体の満了 or 上記フェーズ終了による失格）
 * status の更新が遅れても、deadline が過ぎていれば満了として扱う
 */
export function isProposerExpiredOrFailed(c: SortableChallenge): boolean {
  return (
    c.status === 'closed' ||
    c.status === 'completed' ||
    isDeadlinePassed(c) ||
    isProposerFailed(c)
  );
}

/** 提案者が自分の評価完了後ストーリーを閲覧できるか（終了状態かつ参加済み評価完了） */
export function canProposerViewResults(c: SortableChallenge): boolean {
  return isProposerExpiredOrFailed(c) && !!(c.has_proposed && c.has_completed_all_evaluations);
}

/**
 * 募集中（提案者）:
 * 優先度: まだやるべきことがある課題を上に、全フェーズ達成（することがない）を一番下に
 * 1. 提案期間中かつ未提案（最優先）
 * 2. 評価期間中かつ評価未完了（評価が必要）
 * 3. 編集期間（編集は任意だが、まだ続きがある）
 * 4. 全フェーズ達成（することがない＝一番下）
 * 各グループ内では次のフェーズまで近い順、同条件は投稿の新しい順
 */
export function sortActiveProposerChallenges<T extends SortableChallenge>(challenges: T[]): T[] {
  return [...challenges].sort((a, b) => {
    const getActionPriority = (c: SortableChallenge): number => {
      if (c.current_phase === 'proposal' && !c.has_proposed) return 0; // 提案が必要
      if (c.current_phase === 'evaluation' && c.has_proposed && !c.has_completed_all_evaluations) return 1; // 評価が必要
      if (c.current_phase === 'edit' && c.has_proposed) return 2; // 編集期間（まだ続きがある）
      if (isAllPhasesCompleted(c)) return 4; // 全フェーズ達成（することがない＝一番下）
      return 2; // フォールバック（編集期間など）
    };

    const aPriority = getActionPriority(a);
    const bPriority = getActionPriority(b);
    if (aPriority !== bPriority) return aPriority - bPriority;

    const ma = msUntilNextPhase(a);
    const mb = msUntilNextPhase(b);
    if (ma !== mb) return ma - mb; // 次のフェーズまで近い順
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime(); // 投稿の新しい順
  });
}
