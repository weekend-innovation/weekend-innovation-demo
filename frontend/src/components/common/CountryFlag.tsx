/**
 * 国旗表示コンポーネント
 */
'use client';

import React from 'react';
import ReactCountryFlag from 'react-country-flag';
import { normalizeCountryCode } from '../../lib/countryFlags';

interface CountryFlagProps {
  countryCode: string | null | undefined;
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

const CountryFlag: React.FC<CountryFlagProps> = ({ 
  countryCode, 
  size = 'medium',
  className = ''
}) => {
  if (!countryCode) return null;
  
  const code = normalizeCountryCode(countryCode);
  
  // サイズに応じたスタイル（3:2のアスペクト比）
  const sizeStyles = {
    small: { width: '1.125rem', height: '0.75rem' },  // 18px × 12px（性別・年齢の白枠に合わせる）
    medium: { width: '1.5rem', height: '1rem' },      // 24px × 16px
    large: { width: '2.25rem', height: '1.5rem' },    // 36px × 24px
  };
  
  return (
    <span 
      className={`inline-block border border-gray-300 rounded ${className}`}
      style={{ padding: '2px' }}
    >
      <ReactCountryFlag
        countryCode={code}
        svg
        style={sizeStyles[size]}
        title={code}
      />
    </span>
  );
};

export default CountryFlag;

