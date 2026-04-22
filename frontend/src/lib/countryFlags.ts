/**
 * 国旗関連のユーティリティ関数
 */

/**
 * 国コードを正規化（大文字に変換）
 * @param countryCode ISO 3166-1 alpha-2 国コード (例: 'JP', 'US', 'CN')
 * @returns 大文字の国コード
 */
export function normalizeCountryCode(countryCode: string | null | undefined): string {
  if (!countryCode) return '';
  return countryCode.toUpperCase();
}

/**
 * 国コードから国名を取得（日本語）
 * @param countryCode ISO 3166-1 alpha-2 国コード
 * @returns 国名（日本語）
 */
export function getCountryName(countryCode: string | null | undefined): string {
  if (!countryCode) return '';
  
  const countryNames: Record<string, string> = {
    'JP': '日本',
    'US': 'アメリカ',
    'CN': '中国',
    'KR': '韓国',
    'TW': '台湾',
    'HK': '香港',
    'SG': 'シンガポール',
    'TH': 'タイ',
    'VN': 'ベトナム',
    'PH': 'フィリピン',
    'ID': 'インドネシア',
    'MY': 'マレーシア',
    'IN': 'インド',
    'AU': 'オーストラリア',
    'NZ': 'ニュージーランド',
    'GB': 'イギリス',
    'FR': 'フランス',
    'DE': 'ドイツ',
    'IT': 'イタリア',
    'ES': 'スペイン',
    'CA': 'カナダ',
    'MX': 'メキシコ',
    'BR': 'ブラジル',
    'AR': 'アルゼンチン',
    'RU': 'ロシア',
    'SA': 'サウジアラビア',
    'AE': 'アラブ首長国連邦',
    'ZA': '南アフリカ',
    'EG': 'エジプト',
  };
  
  return countryNames[countryCode.toUpperCase()] || countryCode;
}

/**
 * 性別を日本語表示に変換
 * @param gender 性別コード ('male', 'female', 'other', 'prefer_not_to_say')
 * @returns 日本語表示
 */
export function getGenderDisplay(gender: string | null | undefined): string {
  if (!gender) return '';
  
  const genderDisplay: Record<string, string> = {
    'male': '男性',
    'female': '女性',
    'other': 'その他',
    'prefer_not_to_say': '回答しない',
  };
  
  return genderDisplay[gender] || gender;
}

