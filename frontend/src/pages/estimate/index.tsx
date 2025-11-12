'use client';

import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import FileUpload from '@/components/estimate/FileUpload';
import ContractForm from '@/components/estimate/ContractForm';
import ProcessingState from '@/components/estimate/ProcessingState';
import { apiClient, ContractDetails } from '@/lib/api';
import { ArrowRight, Sparkles } from 'lucide-react';

export default function EstimatePage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [formData, setFormData] = useState<ContractDetails>({
    project_name: '',
    location: '',
    department: 'CPWD',
    completion_days: 365,
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState<'uploading' | 'extracting' | 'calculating' | 'validating' | 'complete'>('uploading');
  const [progress, setProgress] = useState(0);

  const handleFormChange = (field: keyof ContractDetails, value: string | number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (files.length === 0) {
      alert('Please upload at least one drawing');
      return;
    }

    if (!formData.project_name || !formData.location) {
      alert('Please fill in required fields');
      return;
    }

    setIsProcessing(true);
    setProcessingStage('uploading');
    setProgress(10);

    try {
      // Simulate progress through stages
      setTimeout(() => {
        setProcessingStage('extracting');
        setProgress(30);
      }, 1000);

      const response = await apiClient.createEstimation(files, formData);

      setProcessingStage('calculating');
      setProgress(60);

      setTimeout(() => {
        setProcessingStage('validating');
        setProgress(85);
      }, 1500);

      setTimeout(() => {
        setProgress(100);
        // Store result in sessionStorage
        sessionStorage.setItem('boqResult', JSON.stringify(response));
        // Navigate to results page
        router.push('/estimate/results');
      }, 2000);
    } catch (error: any) {
      console.error('Estimation error:', error);
      alert(`Error: ${error.message || 'Failed to generate BOQ. Please try again.'}`);
      setIsProcessing(false);
    }
  };

  return (
    <>
      <Head>
        <title>Generate BOQ - TakeoffAI</title>
        <meta
          name="description"
          content="Upload your construction drawings and generate accurate BOQ estimates in minutes."
        />
      </Head>

      <div className="min-h-screen flex flex-col">
        <Header />

        <main className="flex-1 pt-24 pb-16 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950">
          <div className="section-container">
            {/* Page Header */}
            <div className="text-center mb-12">
              <div className="inline-flex items-center space-x-2 px-4 py-2 bg-primary-100 dark:bg-primary-900/30 rounded-full mb-6">
                <Sparkles className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
                  AI-Powered BOQ Generation
                </span>
              </div>
              <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                Generate Your <span className="gradient-text">BOQ Estimate</span>
              </h1>
              <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                Upload construction drawings and project details. We'll generate a complete,
                CPWD-compliant BOQ in minutes.
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="max-w-5xl mx-auto space-y-8">
              {/* Step 1: Upload Drawings */}
              <div>
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center font-bold">
                    1
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Upload Construction Drawings
                  </h2>
                </div>
                <FileUpload files={files} onFilesChange={setFiles} />
              </div>

              {/* Step 2: Project Details */}
              <div>
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center font-bold">
                    2
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Enter Project Details
                  </h2>
                </div>
                <ContractForm formData={formData} onChange={handleFormChange} />
              </div>

              {/* Submit Button */}
              <div className="flex justify-center">
                <button
                  type="submit"
                  disabled={files.length === 0 || !formData.project_name || !formData.location}
                  className="btn-primary inline-flex items-center text-lg px-8 py-4 group"
                >
                  Generate BOQ Estimate
                  <ArrowRight className="ml-2 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>

              {/* Info */}
              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Processing typically takes 2-3 minutes. Your data is secure and not stored permanently.
                </p>
              </div>
            </form>
          </div>
        </main>

        <Footer />

        {/* Processing Overlay */}
        {isProcessing && (
          <ProcessingState stage={processingStage} progress={progress} />
        )}
      </div>
    </>
  );
}
