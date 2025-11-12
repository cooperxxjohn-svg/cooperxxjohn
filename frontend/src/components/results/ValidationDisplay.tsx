'use client';

import React from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { ValidationResult } from '@/lib/api';

interface ValidationDisplayProps {
  validation: ValidationResult;
}

export default function ValidationDisplay({ validation }: ValidationDisplayProps) {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />;
      default:
        return null;
    }
  };

  const getSeverityBg = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
      case 'info':
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
      default:
        return '';
    }
  };

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        CPWD Validation Status
      </h3>

      {/* Overall status */}
      <div
        className={`p-4 rounded-lg mb-6 ${
          validation.is_valid
            ? 'bg-green-50 dark:bg-green-900/20 border-2 border-green-200 dark:border-green-800'
            : 'bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-200 dark:border-yellow-800'
        }`}
      >
        <div className="flex items-center space-x-3">
          {validation.is_valid ? (
            <>
              <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400" />
              <div>
                <p className="font-semibold text-green-900 dark:text-green-100 text-lg">
                  CPWD Compliant
                </p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  All validations passed successfully
                </p>
              </div>
            </>
          ) : (
            <>
              <AlertTriangle className="h-8 w-8 text-yellow-600 dark:text-yellow-400" />
              <div>
                <p className="font-semibold text-yellow-900 dark:text-yellow-100 text-lg">
                  {validation.total_issues} Validation Issue(s) Found
                </p>
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  {validation.errors.length} errors, {validation.warnings.length} warnings,{' '}
                  {validation.info.length} info
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Issues list */}
      {validation.total_issues > 0 && (
        <div className="space-y-4">
          {/* Errors */}
          {validation.errors.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-red-700 dark:text-red-300 mb-2">
                Errors ({validation.errors.length})
              </h4>
              <div className="space-y-2">
                {validation.errors.map((issue, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${getSeverityBg('error')}`}
                  >
                    <div className="flex items-start space-x-3">
                      {getSeverityIcon('error')}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-red-900 dark:text-red-100">
                          {issue.category}
                        </p>
                        <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                          {issue.message}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Warnings */}
          {validation.warnings.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-yellow-700 dark:text-yellow-300 mb-2">
                Warnings ({validation.warnings.length})
              </h4>
              <div className="space-y-2">
                {validation.warnings.map((issue, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${getSeverityBg('warning')}`}
                  >
                    <div className="flex items-start space-x-3">
                      {getSeverityIcon('warning')}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                          {issue.category}
                        </p>
                        <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                          {issue.message}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Info */}
          {validation.info.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-2">
                Information ({validation.info.length})
              </h4>
              <div className="space-y-2">
                {validation.info.map((issue, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${getSeverityBg('info')}`}
                  >
                    <div className="flex items-start space-x-3">
                      {getSeverityIcon('info')}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                          {issue.category}
                        </p>
                        <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                          {issue.message}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
