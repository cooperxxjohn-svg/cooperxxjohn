'use client';

import React from 'react';
import { Loader2, CheckCircle2, FileText, Calculator, Shield } from 'lucide-react';

interface ProcessingStateProps {
  stage: 'uploading' | 'extracting' | 'calculating' | 'validating' | 'complete';
  progress: number;
}

export default function ProcessingState({ stage, progress }: ProcessingStateProps) {
  const stages = [
    {
      id: 'uploading',
      label: 'Uploading Files',
      icon: FileText,
      description: 'Uploading your construction drawings...',
    },
    {
      id: 'extracting',
      label: 'AI Extraction',
      icon: Loader2,
      description: 'Analyzing drawings with Claude Vision AI...',
    },
    {
      id: 'calculating',
      label: 'Calculating BOQ',
      icon: Calculator,
      description: 'Applying CPWD rates and formulas...',
    },
    {
      id: 'validating',
      label: 'Validation',
      icon: Shield,
      description: 'Checking CPWD compliance...',
    },
  ];

  const currentStageIndex = stages.findIndex((s) => s.id === stage);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="card p-8 max-w-2xl w-full animate-scale-in">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 mb-4">
            <Loader2 className="h-8 w-8 text-primary-600 dark:text-primary-400 animate-spin" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Generating Your BOQ
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            This typically takes 2-3 minutes. Please don't close this window.
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
            <span>Processing...</span>
            <span>{progress}%</span>
          </div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-600 to-secondary-600 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Stages */}
        <div className="space-y-4">
          {stages.map((stageItem, index) => {
            const Icon = stageItem.icon;
            const isActive = index === currentStageIndex;
            const isComplete = index < currentStageIndex;

            return (
              <div
                key={stageItem.id}
                className={`flex items-center space-x-4 p-4 rounded-lg transition-all duration-300 ${
                  isActive
                    ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800'
                    : isComplete
                    ? 'bg-green-50 dark:bg-green-900/20'
                    : 'bg-gray-50 dark:bg-gray-800'
                }`}
              >
                {/* Icon */}
                <div
                  className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                    isActive
                      ? 'bg-primary-100 dark:bg-primary-900/50'
                      : isComplete
                      ? 'bg-green-100 dark:bg-green-900/50'
                      : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  {isComplete ? (
                    <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
                  ) : (
                    <Icon
                      className={`h-5 w-5 ${
                        isActive
                          ? 'text-primary-600 dark:text-primary-400 animate-spin'
                          : 'text-gray-400 dark:text-gray-500'
                      }`}
                    />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1">
                  <p
                    className={`font-semibold ${
                      isActive || isComplete
                        ? 'text-gray-900 dark:text-gray-100'
                        : 'text-gray-500 dark:text-gray-400'
                    }`}
                  >
                    {stageItem.label}
                  </p>
                  {isActive && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {stageItem.description}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Fun fact */}
        <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            <strong>Did you know?</strong> Our AI analyzes hundreds of construction elements per
            second, achieving 95%+ accuracy in quantity extraction.
          </p>
        </div>
      </div>
    </div>
  );
}
