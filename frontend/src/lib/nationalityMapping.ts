/**
 * 国籍コードと日本語名のマッピング
 * バックエンドのNATIONALITY_CHOICESと対応
 */
export const NATIONALITY_MAPPING: Record<string, string> = {
  'JP': '日本',
  'US': 'アメリカ',
  'CN': '中国',
  'KR': '韓国',
  'GB': 'イギリス',
  'DE': 'ドイツ',
  'FR': 'フランス',
  'IT': 'イタリア',
  'ES': 'スペイン',
  'CA': 'カナダ',
  'AU': 'オーストラリア',
  'BR': 'ブラジル',
  'IN': 'インド',
  'RU': 'ロシア',
  'SG': 'シンガポール',
  'TH': 'タイ',
  'MY': 'マレーシア',
  'ID': 'インドネシア',
  'PH': 'フィリピン',
  'VN': 'ベトナム',
  'TW': '台湾',
  'HK': '香港',
  'MX': 'メキシコ',
  'AR': 'アルゼンチン',
  'CL': 'チリ',
  'ZA': '南アフリカ',
  'EG': 'エジプト',
  'NG': 'ナイジェリア',
  'KE': 'ケニア',
  'MA': 'モロッコ',
  'TR': 'トルコ',
  'SA': 'サウジアラビア',
  'AE': 'UAE',
  'IL': 'イスラエル',
  'NO': 'ノルウェー',
  'SE': 'スウェーデン',
  'DK': 'デンマーク',
  'FI': 'フィンランド',
  'NL': 'オランダ',
  'BE': 'ベルギー',
  'CH': 'スイス',
  'AT': 'オーストリア',
  'PL': 'ポーランド',
  'CZ': 'チェコ',
  'HU': 'ハンガリー',
  'RO': 'ルーマニア',
  'BG': 'ブルガリア',
  'HR': 'クロアチア',
  'SI': 'スロベニア',
  'SK': 'スロバキア',
  'LT': 'リトアニア',
  'LV': 'ラトビア',
  'EE': 'エストニア',
  'IE': 'アイルランド',
  'PT': 'ポルトガル',
  'GR': 'ギリシャ',
  'CY': 'キプロス',
  'MT': 'マルタ',
};

/**
 * 国籍コードを日本語名に変換
 * @param code 国籍コード（例: 'JP'）
 * @returns 日本語名（例: '日本'）
 */
export const getNationalityName = (code: string): string => {
  return NATIONALITY_MAPPING[code] || code;
};

/**
 * 日本語名を国籍コードに変換
 * @param name 日本語名（例: '日本'）
 * @returns 国籍コード（例: 'JP'）
 */
export const getNationalityCode = (name: string): string => {
  const entry = Object.entries(NATIONALITY_MAPPING).find(([, value]) => value === name);
  return entry ? entry[0] : name;
};
