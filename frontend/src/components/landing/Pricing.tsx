'use client';

import React from 'react';
import { Check, Zap, Building2, Rocket } from 'lucide-react';

export default function Pricing() {
  const plans = [
    {
      name: 'Free Trial',
      icon: Zap,
      price: '₹0',
      period: 'for 14 days',
      description: 'Perfect for trying out TakeoffAI',
      features: [
        '3 BOQ generations',
        'Basic CPWD validation',
        'Export to Excel & PDF',
        'Email support',
        'Up to 10 pages per drawing',
      ],
      cta: 'Start Free Trial',
      popular: false,
      color: 'from-blue-600 to-cyan-600',
    },
    {
      name: 'Professional',
      icon: Building2,
      price: '₹4,999',
      period: 'per month',
      description: 'For small to medium contractors',
      features: [
        'Unlimited BOQ generations',
        'Full CPWD validation',
        'All export formats',
        'Priority support',
        'Unlimited pages',
        'Custom rate templates',
        'Batch processing',
      ],
      cta: 'Get Started',
      popular: true,
      color: 'from-primary-600 to-secondary-600',
    },
    {
      name: 'Enterprise',
      icon: Rocket,
      price: 'Custom',
      period: 'contact us',
      description: 'For large contractors & organizations',
      features: [
        'Everything in Professional',
        'API access',
        'Custom integrations',
        'Dedicated support',
        'Team collaboration',
        'Custom training',
        'On-premise deployment',
        'SLA guarantee',
      ],
      cta: 'Contact Sales',
      popular: false,
      color: 'from-purple-600 to-pink-600',
    },
  ];

  return (
    <section id="pricing" className="py-20 lg:py-28 bg-white dark:bg-gray-950">
      <div className="section-container">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-6">
            Simple, <span className="gradient-text">Transparent Pricing</span>
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Choose the plan that fits your needs. No hidden fees, cancel anytime.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {plans.map((plan, index) => {
            const Icon = plan.icon;
            return (
              <div
                key={index}
                className={`relative ${
                  plan.popular
                    ? 'md:-mt-4 md:mb-4'
                    : ''
                }`}
              >
                {/* Popular badge */}
                {plan.popular && (
                  <div className="absolute -top-5 left-0 right-0 flex justify-center">
                    <span className="inline-flex items-center px-4 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-primary-600 to-secondary-600 text-white shadow-lg">
                      Most Popular
                    </span>
                  </div>
                )}

                {/* Card */}
                <div
                  className={`card p-8 h-full flex flex-col ${
                    plan.popular
                      ? 'border-2 border-primary-600 dark:border-primary-500 shadow-2xl'
                      : ''
                  }`}
                >
                  {/* Icon */}
                  <div className="mb-6">
                    <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${plan.color} p-3 shadow-lg`}>
                      <Icon className="h-full w-full text-white" />
                    </div>
                  </div>

                  {/* Plan name */}
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                    {plan.name}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    {plan.description}
                  </p>

                  {/* Price */}
                  <div className="mb-6">
                    <div className="flex items-baseline">
                      <span className="text-5xl font-bold text-gray-900 dark:text-gray-100">
                        {plan.price}
                      </span>
                      {plan.price !== 'Custom' && (
                        <span className="ml-2 text-gray-600 dark:text-gray-400">
                          /{plan.period}
                        </span>
                      )}
                    </div>
                    {plan.price === 'Custom' && (
                      <span className="text-gray-600 dark:text-gray-400">{plan.period}</span>
                    )}
                  </div>

                  {/* CTA Button */}
                  <a
                    href={plan.name === 'Enterprise' ? '#' : '/estimate'}
                    className={`w-full text-center py-3 px-6 rounded-lg font-semibold transition-all duration-200 mb-8 ${
                      plan.popular
                        ? 'bg-gradient-to-r from-primary-600 to-secondary-600 text-white hover:shadow-lg hover:-translate-y-0.5'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600'
                    }`}
                  >
                    {plan.cta}
                  </a>

                  {/* Features */}
                  <ul className="space-y-4 flex-grow">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start">
                        <Check className="h-5 w-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>

        {/* FAQ Note */}
        <div className="mt-16 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            All plans include updates and new features. No setup fees.{' '}
            <a href="#" className="text-primary-600 dark:text-primary-400 hover:underline font-medium">
              View detailed comparison →
            </a>
          </p>
        </div>
      </div>
    </section>
  );
}
