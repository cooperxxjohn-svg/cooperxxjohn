import React from 'react';
import Head from 'next/head';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import Hero from '@/components/landing/Hero';
import Features from '@/components/landing/Features';
import HowItWorks from '@/components/landing/HowItWorks';
import Pricing from '@/components/landing/Pricing';

export default function Home() {
  return (
    <>
      <Head>
        <title>TakeoffAI - AI-Powered BOQ Estimation for Indian Contractors</title>
        <meta
          name="description"
          content="Generate accurate Bill of Quantities in minutes using AI. CPWD compliant, fast, and accurate BOQ estimation for government contractors."
        />
      </Head>

      <div className="min-h-screen">
        <Header />

        <main>
          <Hero />
          <Features />
          <HowItWorks />
          <Pricing />
        </main>

        <Footer />
      </div>
    </>
  );
}
