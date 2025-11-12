'use client';

import React from 'react';
import { Download, FileText, Table, FileJson, Printer } from 'lucide-react';
import { BOQDocument } from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/utils';
import { apiClient } from '@/lib/api';

interface BOQSummaryProps {
  boq: BOQDocument;
  categorySummary?: Record<string, { amount: number }>;
}

export default function BOQSummary({ boq, categorySummary }: BOQSummaryProps) {
  const handleDownload = async (format: 'excel' | 'pdf' | 'csv' | 'json') => {
    try {
      const blob = await apiClient.downloadBOQ(format);
      const filename = `BOQ_${boq.contract.contract_name.replace(/\s+/g, '_')}_${boq.boq_id}.${format === 'excel' ? 'xlsx' : format}`;
      apiClient.downloadFile(blob, filename);
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download file. Please try again.');
    }
  };

  const totalWithGST = boq.gst_percentage
    ? boq.total_amount * (1 + boq.gst_percentage / 100)
    : boq.total_amount;

  return (
    <div className="space-y-6">
      {/* Project Info Card */}
      <div className="card p-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              {boq.contract.contract_name}
            </h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Location:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{boq.contract.location}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Department:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{boq.contract.department}</span>
              </div>
              {boq.contract.client && (
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Client:</span>
                  <span className="font-medium text-gray-900 dark:text-gray-100">{boq.contract.client}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">BOQ ID:</span>
                <span className="font-mono text-xs text-gray-900 dark:text-gray-100">{boq.boq_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Generated:</span>
                <span className="text-gray-900 dark:text-gray-100">{formatDate(boq.created_date)}</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col justify-center items-end">
            <div className="text-right mb-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Estimated Cost</p>
              <p className="text-4xl font-bold gradient-text">{formatCurrency(boq.total_amount)}</p>
              {boq.gst_percentage && (
                <>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    + GST @ {boq.gst_percentage}%
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {formatCurrency(totalWithGST)}
                  </p>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Download Options */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Download BOQ
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={() => handleDownload('excel')}
            className="flex flex-col items-center p-4 rounded-lg bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30 border border-green-200 dark:border-green-800 transition-colors group"
          >
            <Table className="h-8 w-8 text-green-600 dark:text-green-400 mb-2 group-hover:scale-110 transition-transform" />
            <span className="text-sm font-medium text-green-700 dark:text-green-300">Excel</span>
            <span className="text-xs text-green-600 dark:text-green-400">.xlsx</span>
          </button>

          <button
            onClick={() => handleDownload('pdf')}
            className="flex flex-col items-center p-4 rounded-lg bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 border border-red-200 dark:border-red-800 transition-colors group"
          >
            <FileText className="h-8 w-8 text-red-600 dark:text-red-400 mb-2 group-hover:scale-110 transition-transform" />
            <span className="text-sm font-medium text-red-700 dark:text-red-300">PDF</span>
            <span className="text-xs text-red-600 dark:text-red-400">.pdf</span>
          </button>

          <button
            onClick={() => handleDownload('csv')}
            className="flex flex-col items-center p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 border border-blue-200 dark:border-blue-800 transition-colors group"
          >
            <Download className="h-8 w-8 text-blue-600 dark:text-blue-400 mb-2 group-hover:scale-110 transition-transform" />
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">CSV</span>
            <span className="text-xs text-blue-600 dark:text-blue-400">.csv</span>
          </button>

          <button
            onClick={() => handleDownload('json')}
            className="flex flex-col items-center p-4 rounded-lg bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 border border-purple-200 dark:border-purple-800 transition-colors group"
          >
            <FileJson className="h-8 w-8 text-purple-600 dark:text-purple-400 mb-2 group-hover:scale-110 transition-transform" />
            <span className="text-sm font-medium text-purple-700 dark:text-purple-300">JSON</span>
            <span className="text-xs text-purple-600 dark:text-purple-400">.json</span>
          </button>
        </div>
      </div>

      {/* Category Summary */}
      {categorySummary && Object.keys(categorySummary).length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Category-wise Breakdown
          </h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(categorySummary).map(([category, data]) => {
              const percentage = (data.amount / boq.total_amount) * 100;
              return (
                <div
                  key={category}
                  className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {category.replace(/_/g, ' ')}
                  </p>
                  <p className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">
                    {formatCurrency(data.amount)}
                  </p>
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-600 rounded-full"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
