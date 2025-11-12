import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <meta charSet="utf-8" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
        <meta name="description" content="TakeoffAI - AI-powered BOQ estimation for Indian government contractors. Generate accurate Bill of Quantities in minutes." />
        <meta name="keywords" content="BOQ, Bill of Quantities, CPWD, construction, estimation, AI, contractors, India" />
        <meta property="og:title" content="TakeoffAI - AI-Powered BOQ Estimation" />
        <meta property="og:description" content="Generate accurate BOQ estimates in minutes with AI. CPWD compliant, fast, and accurate." />
        <meta property="og:type" content="website" />
        <meta name="twitter:card" content="summary_large_image" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
