'use client';

import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import BOQSummary from '@/components/results/BOQSummary';
import ValidationDisplay from '@/components/results/ValidationDisplay';
import BOQTable from '@/components/results/BOQTable';
import { EstimationResponse } from '@/lib/api';
import { ArrowLeft, Sparkles } from 'lucide-react';

export default function ResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<EstimationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get result from sessionStorage
    const stored = sessionStorage.getItem('boqResult');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setResult(parsed);
      } catch (error) {
        console.error('Error parsing result:', error);
        router.push('/estimate');
      }
    } else {
      // No result found, redirect to estimate page
      router.push('/estimate');
    }
    setLoading(false);
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading results...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  return (
    <>
      <Head>
        <title>BOQ Results - {result.boq.contract.contract_name} - TakeoffAI</title>
        <meta
          name="description"
          content={`BOQ estimation results for ${result.boq.contract.contract_name}`}
        />
      </Head>

      <div className="min-h-screen flex flex-col">
        <Header />

        <main className="flex-1 pt-24 pb-16 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950">
          <div className="section-container">
            {/* Page Header */}
            <div className="mb-8">
              <Link
                href="/estimate"
                className="inline-flex items-center text-primary-600 dark:text-primary-400 hover:underline mb-4"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Create New Estimate
              </Link>

              <div className="flex items-center justify-between">
                <div>
                  <div className="inline-flex items-center space-x-2 px-4 py-2 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
                    <Sparkles className="h-4 w-4 text-green-600 dark:text-green-400" />
                    <span className="text-sm font-medium text-green-700 dark:text-green-300">
                      BOQ Generated Successfully
                    </span>
                  </div>
                  <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100">
                    Your BOQ Estimate
                  </h1>
                </div>
              </div>
            </div>

            {/* Summary Section */}
            <div className="mb-8">
              <BOQSummary boq={result.boq} categorySummary={result.category_summary} />
            </div>

            {/* Validation Section */}
            {result.validation && (
              <div className="mb-8">
                <ValidationDisplay validation={result.validation} />
              </div>
            )}

            {/* BOQ Table */}
            <div>
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                  Bill of Quantities - Detailed Items
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Click on any item to view material and labour breakdown
                </p>
              </div>
              <BOQTable sections={result.boq.sections} />
            </div>

            {/* Action Buttons */}
            <div className="mt-12 flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/estimate" className="btn-primary inline-flex items-center justify-center">
                Generate Another BOQ
              </Link>
              <button
                onClick={() => window.print()}
                className="btn-secondary inline-flex items-center justify-center"
              >
                Print BOQ
              </button>
            </div>
          </div>
        </main>

        <Footer />
      </div>
    </>
  );
}
