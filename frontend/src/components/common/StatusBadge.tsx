import React from 'react';
import { SRF_STATUS_COLORS, JOB_STATUS_COLORS } from '../../utils/constants';
import { formatStatus } from '../../utils/formatters';

interface StatusBadgeProps {
  status: string;
  type?: 'srf' | 'job' | 'custom';
  customColors?: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ 
  status, 
  type = 'custom', 
  customColors = 'bg-gray-100 text-gray-800' 
}) => {
  let colorClasses = customColors;
  
  if (type === 'srf' && status in SRF_STATUS_COLORS) {
    colorClasses = SRF_STATUS_COLORS[status as keyof typeof SRF_STATUS_COLORS];
  } else if (type === 'job' && status in JOB_STATUS_COLORS) {
    colorClasses = JOB_STATUS_COLORS[status as keyof typeof JOB_STATUS_COLORS];
  }
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClasses}`}>
      {formatStatus(status)}
    </span>
  );
};

export default StatusBadge;
