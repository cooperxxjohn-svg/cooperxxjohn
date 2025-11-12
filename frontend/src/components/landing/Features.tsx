'use client';

import React from 'react';
import {
  Zap, Shield, FileText, BarChart3, Download, CheckCircle2,
  Brain, Clock, IndianRupee, FileCheck, Sparkles, TrendingUp
} from 'lucide-react';

export default function Features() {
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Extraction',
      description: 'Claude Vision AI automatically extracts quantities, dimensions, and specifications from your drawings with 95%+ accuracy.',
      color: 'from-purple-500 to-indigo-500',
    },
    {
      icon: Shield,
      title: 'CPWD Compliant',
      description: 'Automatic validation against CPWD standards and specifications. Get detailed compliance reports with every estimate.',
      color: 'from-green-500 to-emerald-500',
    },
    {
      icon: Clock,
      title: 'Lightning Fast',
      description: 'Generate complete BOQ in 2-3 minutes. What used to take days now takes minutes. 10x faster than manual estimation.',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: IndianRupee,
      title: 'Accurate Costing',
      description: 'DSR 2024 rates built-in. Material, labour, and equipment costs calculated automatically with wastage factors.',
      color: 'from-amber-500 to-orange-500',
    },
    {
      icon: FileText,
      title: 'Multiple Formats',
      description: 'Export to Excel, PDF, CSV, or JSON. Professional formatting ready for submission to government departments.',
      color: 'from-pink-500 to-rose-500',
    },
    {
      icon: BarChart3,
      title: 'Detailed Analytics',
      description: 'Category-wise breakdown, material composition, labour requirements, and cost analysis in beautiful charts.',
      color: 'from-violet-500 to-purple-500',
    },
    {
      icon: FileCheck,
      title: 'Quality Validation',
      description: 'Automatic checks for rate reasonableness, quantity accuracy, and specification compliance.',
      color: 'from-teal-500 to-green-500',
    },
    {
      icon: Sparkles,
      title: 'Smart Categorization',
      description: 'Intelligent mapping of construction elements to BOQ categories. Earthwork, concrete, masonry - all auto-categorized.',
      color: 'from-red-500 to-pink-500',
    },
    {
      icon: TrendingUp,
      title: 'Cost Optimization',
      description: 'Get suggestions for cost savings and alternative materials. Optimize your tender rates competitively.',
      color: 'from-cyan-500 to-blue-500',
    },
  ];

  return (
    <section id="features" className="py-20 lg:py-28 bg-white dark:bg-gray-950">
      <div className="section-container">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-primary-100 dark:bg-primary-900/30 rounded-full mb-6">
            <Sparkles className="h-4 w-4 text-primary-600 dark:text-primary-400" />
            <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
              Features
            </span>
          </div>
          <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-6">
            Everything You Need for{' '}
            <span className="gradient-text">Perfect BOQ</span>
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Built specifically for Indian government contractors. CPWD standards, DSR rates,
            and IS codes - all in one powerful platform.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="card p-8 group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1"
              >
                {/* Icon */}
                <div className="relative mb-6">
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} p-3 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className="h-full w-full text-white" />
                  </div>
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} blur-xl opacity-20 group-hover:opacity-40 transition-opacity duration-300`}></div>
                </div>

                {/* Content */}
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <a
            href="/estimate"
            className="btn-primary inline-flex items-center group"
          >
            Start Generating BOQ
            <Zap className="ml-2 h-5 w-5 group-hover:scale-110 transition-transform" />
          </a>
        </div>
      </div>
    </section>
  );
}
