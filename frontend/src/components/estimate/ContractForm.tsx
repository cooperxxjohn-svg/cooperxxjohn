'use client';

import React from 'react';
import { ContractDetails } from '@/lib/api';

interface ContractFormProps {
  formData: ContractDetails;
  onChange: (field: keyof ContractDetails, value: string | number) => void;
}

export default function ContractForm({ formData, onChange }: ContractFormProps) {
  return (
    <div className="card p-8">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
        Project Details
      </h2>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Project Name */}
        <div className="md:col-span-2">
          <label
            htmlFor="project_name"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Project Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="project_name"
            required
            value={formData.project_name}
            onChange={(e) => onChange('project_name', e.target.value)}
            placeholder="e.g., Government Office Building Construction"
            className="input-field"
          />
        </div>

        {/* Location */}
        <div>
          <label
            htmlFor="location"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Location <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="location"
            required
            value={formData.location}
            onChange={(e) => onChange('location', e.target.value)}
            placeholder="e.g., New Delhi"
            className="input-field"
          />
        </div>

        {/* Department */}
        <div>
          <label
            htmlFor="department"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Department
          </label>
          <input
            type="text"
            id="department"
            value={formData.department || 'CPWD'}
            onChange={(e) => onChange('department', e.target.value)}
            placeholder="e.g., CPWD"
            className="input-field"
          />
        </div>

        {/* Contract Number */}
        <div>
          <label
            htmlFor="contract_no"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Contract Number
          </label>
          <input
            type="text"
            id="contract_no"
            value={formData.contract_no || ''}
            onChange={(e) => onChange('contract_no', e.target.value)}
            placeholder="e.g., CPWD/2024/001"
            className="input-field"
          />
        </div>

        {/* Client */}
        <div>
          <label
            htmlFor="client"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Client Name
          </label>
          <input
            type="text"
            id="client"
            value={formData.client || ''}
            onChange={(e) => onChange('client', e.target.value)}
            placeholder="e.g., Ministry of Public Works"
            className="input-field"
          />
        </div>

        {/* Completion Period */}
        <div>
          <label
            htmlFor="completion_days"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Completion Period (Days)
          </label>
          <input
            type="number"
            id="completion_days"
            value={formData.completion_days || 365}
            onChange={(e) => onChange('completion_days', parseInt(e.target.value))}
            min="1"
            className="input-field"
          />
        </div>

        {/* Estimated Cost */}
        <div>
          <label
            htmlFor="estimated_cost"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Estimated Cost (₹)
          </label>
          <input
            type="number"
            id="estimated_cost"
            value={formData.estimated_cost || ''}
            onChange={(e) => onChange('estimated_cost', parseFloat(e.target.value))}
            placeholder="Optional - auto-calculated"
            min="0"
            step="0.01"
            className="input-field"
          />
        </div>
      </div>

      <p className="mt-6 text-sm text-gray-500 dark:text-gray-400">
        <span className="text-red-500">*</span> Required fields
      </p>
    </div>
  );
}
