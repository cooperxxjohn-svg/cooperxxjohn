'use client';

import React from 'react';
import { Upload, Brain, FileCheck, Download, ArrowRight } from 'lucide-react';

export default function HowItWorks() {
  const steps = [
    {
      number: '01',
      icon: Upload,
      title: 'Upload Drawings',
      description: 'Upload your construction drawings in PDF format. Supports multiple files and complex drawings.',
      details: ['Drag & drop interface', 'Multiple file support', 'Up to 50MB per file'],
    },
    {
      number: '02',
      icon: Brain,
      title: 'AI Extraction',
      description: 'Claude AI analyzes drawings to extract dimensions, materials, and specifications automatically.',
      details: ['Vision AI analysis', '95%+ accuracy', 'Handles complex drawings'],
    },
    {
      number: '03',
      icon: FileCheck,
      title: 'Auto Calculation',
      description: 'System applies CPWD formulas, DSR rates, and generates complete BOQ with all calculations.',
      details: ['CPWD compliant', 'DSR 2024 rates', 'Material & labour breakdown'],
    },
    {
      number: '04',
      icon: Download,
      title: 'Download & Use',
      description: 'Get your complete BOQ in Excel, PDF, or CSV format. Ready for submission.',
      details: ['Multiple formats', 'Professional formatting', 'Validation report included'],
    },
  ];

  return (
    <section id="how-it-works" className="py-20 lg:py-28 bg-gray-50 dark:bg-gray-900">
      <div className="section-container">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-6">
            How <span className="gradient-text">TakeoffAI</span> Works
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Four simple steps to get your accurate BOQ estimate. No manual calculations needed.
          </p>
        </div>

        {/* Steps */}
        <div className="relative">
          {/* Connection line (desktop) */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-200 via-primary-400 to-secondary-400 dark:from-primary-800 dark:via-primary-600 dark:to-secondary-600 transform -translate-y-1/2"></div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 relative z-10">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div
                  key={index}
                  className="relative"
                >
                  {/* Step card */}
                  <div className="card p-8 h-full group hover:shadow-2xl transition-all duration-300">
                    {/* Number badge */}
                    <div className="absolute -top-4 left-8">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-600 to-secondary-600 flex items-center justify-center text-white font-bold text-lg shadow-lg">
                        {step.number}
                      </div>
                    </div>

                    {/* Icon */}
                    <div className="mt-8 mb-6">
                      <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-primary-100 to-secondary-100 dark:from-primary-900/30 dark:to-secondary-900/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                        <Icon className="h-8 w-8 text-primary-600 dark:text-primary-400" />
                      </div>
                    </div>

                    {/* Content */}
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
                      {step.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      {step.description}
                    </p>

                    {/* Details */}
                    <ul className="space-y-2">
                      {step.details.map((detail, i) => (
                        <li key={i} className="flex items-center text-sm text-gray-500 dark:text-gray-500">
                          <div className="w-1.5 h-1.5 rounded-full bg-primary-600 mr-2"></div>
                          {detail}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Arrow (desktop) */}
                  {index < steps.length - 1 && (
                    <div className="hidden lg:block absolute top-1/2 -right-4 transform -translate-y-1/2 z-20">
                      <ArrowRight className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <div className="inline-flex flex-col items-center space-y-4">
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Ready to transform your BOQ workflow?
            </p>
            <a href="/estimate" className="btn-primary">
              Try It Now - Free Demo
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
