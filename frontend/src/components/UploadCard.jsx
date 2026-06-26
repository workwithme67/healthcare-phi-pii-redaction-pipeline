import React from 'react';
import { FileText, Calendar, AlertCircle, HardDrive } from 'lucide-react';

const UploadCard = ({ totalUploads, uploadedToday, pendingProcessing, avgSize }) => {
  const formatSize = (bytes) => {
    if (bytes === 0 || isNaN(bytes)) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const cards = [
    {
      title: 'Total Uploads',
      value: totalUploads,
      description: 'All-time submissions',
      icon: FileText,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50/50 border-indigo-100/80',
      iconBg: 'bg-indigo-100 text-indigo-700',
    },
    {
      title: 'Uploaded Today',
      value: uploadedToday,
      description: 'New clinical items today',
      icon: Calendar,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50/50 border-emerald-100/80',
      iconBg: 'bg-emerald-100 text-emerald-700',
    },
    {
      title: 'Pending Processing',
      value: pendingProcessing,
      description: 'Awaiting redaction',
      icon: AlertCircle,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50/50 border-amber-100/80',
      iconBg: 'bg-amber-100 text-amber-700',
    },
    {
      title: 'Avg Upload Size',
      value: typeof avgSize === 'string' ? avgSize : formatSize(avgSize),
      description: 'Average payload weight',
      icon: HardDrive,
      color: 'text-teal-600',
      bgColor: 'bg-teal-50/50 border-teal-100/80',
      iconBg: 'bg-teal-100 text-teal-700',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-6 rounded-3xl border ${card.bgColor} backdrop-blur-md shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 flex items-start justify-between bg-white/60`}
          >
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                {card.title}
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900 tracking-tight leading-none">
                  {card.value}
                </span>
              </div>
              <span className="text-xs text-slate-400 font-medium block">
                {card.description}
              </span>
            </div>
            <div className={`p-3 rounded-2xl ${card.iconBg} shadow-sm border border-white/50`}>
              <Icon className="w-5 h-5" />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default UploadCard;
