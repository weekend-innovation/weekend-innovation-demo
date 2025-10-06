import React from 'react';

interface ProfileFieldProps {
  label: string;
  value: string | React.ReactNode;
  className?: string;
}

/**
 * プロフィール項目の再利用可能なコンポーネント
 * 項目名と内容の枠を統一されたデザインで表示
 */
export const ProfileField: React.FC<ProfileFieldProps> = ({ 
  label, 
  value, 
  className = "" 
}) => {
  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">
        {label}
      </label>
      <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
        <p className="text-gray-900">{value}</p>
      </div>
    </div>
  );
};

/**
 * プロフィールセクションのヘッダーコンポーネント
 */
export const ProfileSectionHeader: React.FC<{ title: string }> = ({ title }) => {
  return (
    <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>
  );
};

/**
 * プロフィールセクションのラッパーコンポーネント
 */
export const ProfileSection: React.FC<{ 
  title: string; 
  children: React.ReactNode;
  className?: string;
}> = ({ title, children, className = "" }) => {
  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <ProfileSectionHeader title={title} />
      <div className="space-y-4">
        {children}
      </div>
    </div>
  );
};
