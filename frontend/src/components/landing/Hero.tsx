'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, Zap, Shield, Clock } from 'lucide-react';

export default function Hero() {
  return (
    <section className="relative pt-32 pb-20 lg:pt-40 lg:pb-28 overflow-hidden">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-secondary-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800"></div>
      <div className="absolute top-0 right-0 w-1/2 h-1/2 bg-primary-100 dark:bg-primary-950 rounded-full blur-3xl opacity-20"></div>
      <div className="absolute bottom-0 left-0 w-1/2 h-1/2 bg-secondary-100 dark:bg-secondary-950 rounded-full blur-3xl opacity-20"></div>

      <div className="section-container relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Column - Content */}
          <div className="space-y-8 animate-slide-up">
            {/* Badge */}
            <div className="inline-flex items-center space-x-2 px-4 py-2 bg-primary-100 dark:bg-primary-900/30 rounded-full">
              <Zap className="h-4 w-4 text-primary-600 dark:text-primary-400" />
              <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
                AI-Powered BOQ Generation
              </span>
            </div>

            {/* Heading */}
            <div className="space-y-4">
              <h1 className="text-5xl lg:text-6xl xl:text-7xl font-bold text-gray-900 dark:text-gray-100 leading-tight">
                Generate Accurate{' '}
                <span className="gradient-text">BOQ Estimates</span>{' '}
                in Minutes
              </h1>
              <p className="text-xl text-gray-600 dark:text-gray-400 leading-relaxed max-w-2xl">
                Transform construction drawings into comprehensive Bill of Quantities using
                AI. CPWD compliant, fast, and accurate. Perfect for Indian government contractors.
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/estimate" className="btn-primary inline-flex items-center justify-center group">
                Try Demo - It's Free
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link href="#how-it-works" className="btn-outline inline-flex items-center justify-center">
                Learn More
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 pt-8 border-t border-gray-200 dark:border-gray-700">
              <div>
                <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">95%</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Accuracy Rate</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">10x</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Faster</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">₹50L+</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Saved</div>
              </div>
            </div>
          </div>

          {/* Right Column - Visual */}
          <div className="relative lg:block animate-scale-in">
            <div className="relative">
              {/* Floating cards */}
              <div className="card p-6 transform hover:scale-105 transition-transform duration-300">
                <div className="space-y-4">
                  {/* File upload visual */}
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                      <svg className="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">Upload Drawings</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">PDF format supported</div>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
                      <span>Processing...</span>
                      <span>85%</span>
                    </div>
                    <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div className="h-full w-[85%] bg-gradient-to-r from-primary-600 to-secondary-600 rounded-full animate-shimmer"></div>
                    </div>
                  </div>

                  {/* Sample BOQ items */}
                  <div className="space-y-2">
                    {[
                      { item: 'Earthwork excavation', amount: '₹1,25,000' },
                      { item: 'Concrete M20 grade', amount: '₹3,45,000' },
                      { item: 'Steel reinforcement', amount: '₹2,15,000' },
                    ].map((item, index) => (
                      <div
                        key={index}
                        className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                      >
                        <span className="text-sm text-gray-700 dark:text-gray-300">{item.item}</span>
                        <span className="text-sm font-semibold text-primary-600 dark:text-primary-400">
                          {item.amount}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-2">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                      <Shield className="h-3 w-3 mr-1" />
                      CPWD Compliant
                    </span>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                      <Clock className="h-3 w-3 mr-1" />
                      2-3 mins
                    </span>
                  </div>
                </div>
              </div>

              {/* Decorative elements */}
              <div className="absolute -top-4 -right-4 w-20 h-20 bg-primary-200 dark:bg-primary-800 rounded-full blur-2xl opacity-50"></div>
              <div className="absolute -bottom-4 -left-4 w-20 h-20 bg-secondary-200 dark:bg-secondary-800 rounded-full blur-2xl opacity-50"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
