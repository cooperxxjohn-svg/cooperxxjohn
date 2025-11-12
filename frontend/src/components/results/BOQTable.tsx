'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Download, Printer } from 'lucide-react';
import { BOQSection, BOQItem } from '@/lib/api';
import { formatCurrency, formatNumber } from '@/lib/utils';

interface BOQTableProps {
  sections: BOQSection[];
}

export default function BOQTable({ sections }: BOQTableProps) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const toggleItem = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const isExpanded = (itemId: string) => expandedItems.has(itemId);

  return (
    <div className="space-y-8">
      {sections.map((section, sectionIndex) => (
        <div key={sectionIndex} className="card overflow-hidden">
          {/* Section Header */}
          <div className="bg-gradient-to-r from-primary-600 to-secondary-600 px-6 py-4">
            <h3 className="text-xl font-bold text-white">
              Section {section.section_no}: {section.title}
            </h3>
            {section.description && (
              <p className="text-primary-100 mt-1">{section.description}</p>
            )}
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                    Item No.
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                    Unit
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                    Rate (₹)
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                    Amount (₹)
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {section.items.map((item, itemIndex) => {
                  const itemId = `${section.section_no}-${itemIndex}`;
                  const expanded = isExpanded(itemId);

                  return (
                    <React.Fragment key={itemIndex}>
                      {/* Main row */}
                      <tr className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                          {item.item_no}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                          <div>
                            <p className="font-medium">{item.description}</p>
                            {item.specification && (
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                {item.specification}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                          {item.unit || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-100">
                          {item.quantity ? formatNumber(item.quantity) : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-100">
                          {item.unit_rate ? formatCurrency(item.unit_rate) : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold text-gray-900 dark:text-gray-100">
                          {item.total_amount ? formatCurrency(item.total_amount) : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          {(item.materials?.length || item.labour?.length) && (
                            <button
                              onClick={() => toggleItem(itemId)}
                              className="inline-flex items-center px-3 py-1 text-xs font-medium rounded-md bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 hover:bg-primary-200 dark:hover:bg-primary-900/50 transition-colors"
                            >
                              {expanded ? (
                                <>
                                  <ChevronUp className="h-4 w-4 mr-1" />
                                  Hide
                                </>
                              ) : (
                                <>
                                  <ChevronDown className="h-4 w-4 mr-1" />
                                  Show
                                </>
                              )}
                            </button>
                          )}
                        </td>
                      </tr>

                      {/* Expanded details row */}
                      {expanded && (
                        <tr className="bg-gray-50 dark:bg-gray-800">
                          <td colSpan={7} className="px-6 py-6">
                            <div className="grid md:grid-cols-2 gap-6">
                              {/* Materials */}
                              {item.materials && item.materials.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                                    Materials
                                  </h4>
                                  <div className="bg-white dark:bg-gray-900 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
                                    <table className="w-full text-sm">
                                      <thead className="bg-gray-100 dark:bg-gray-800">
                                        <tr>
                                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300">
                                            Material
                                          </th>
                                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-700 dark:text-gray-300">
                                            Qty
                                          </th>
                                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-700 dark:text-gray-300">
                                            Rate
                                          </th>
                                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-700 dark:text-gray-300">
                                            Amount
                                          </th>
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                        {item.materials.map((material, i) => (
                                          <tr key={i}>
                                            <td className="px-3 py-2 text-gray-900 dark:text-gray-100">
                                              <div>
                                                <p className="font-medium">{material.name}</p>
                                                {material.grade && (
                                                  <p className="text-xs text-gray-500 dark:text-gray-400">
                                                    {material.grade}
                                                  </p>
                                                )}
                                              </div>
                                            </td>
                                            <td className="px-3 py-2 text-right text-gray-700 dark:text-gray-300">
                                              {material.quantity ? formatNumber(material.quantity) : '-'}
                                            </td>
                                            <td className="px-3 py-2 text-right text-gray-700 dark:text-gray-300">
                                              {material.rate ? formatCurrency(material.rate) : '-'}
                                            </td>
                                            <td className="px-3 py-2 text-right text-gray-900 dark:text-gray-100 font-medium">
                                              {material.amount ? formatCurrency(material.amount) : '-'}
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              )}

                              {/* Labour */}
                              {item.labour && item.labour.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                                    Labour
                                  </h4>
                                  <div className="bg-white dark:bg-gray-900 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
                                    <table className="w-full text-sm">
                                      <thead className="bg-gray-100 dark:bg-gray-800">
                                        <tr>
                                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300">
                                            Category
                                          </th>
                                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-700 dark:text-gray-300">
                                            Qty
                                          </th>
                                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-700 dark:text-gray-300">
                                            Rate
                                          </th>
                                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-700 dark:text-gray-300">
                                            Amount
                                          </th>
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                        {item.labour.map((labour, i) => (
                                          <tr key={i}>
                                            <td className="px-3 py-2 text-gray-900 dark:text-gray-100 font-medium">
                                              {labour.category}
                                            </td>
                                            <td className="px-3 py-2 text-right text-gray-700 dark:text-gray-300">
                                              {labour.quantity ? formatNumber(labour.quantity) : '-'}
                                            </td>
                                            <td className="px-3 py-2 text-right text-gray-700 dark:text-gray-300">
                                              {labour.rate ? formatCurrency(labour.rate) : '-'}
                                            </td>
                                            <td className="px-3 py-2 text-right text-gray-900 dark:text-gray-100 font-medium">
                                              {labour.amount ? formatCurrency(labour.amount) : '-'}
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Location */}
                            {item.location && (
                              <div className="mt-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                  <span className="font-medium">Location:</span> {item.location}
                                </p>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>

              {/* Section total */}
              <tfoot className="bg-gray-100 dark:bg-gray-800 border-t-2 border-gray-300 dark:border-gray-600">
                <tr>
                  <td
                    colSpan={5}
                    className="px-6 py-4 text-right text-sm font-semibold text-gray-900 dark:text-gray-100"
                  >
                    Section {section.section_no} Total:
                  </td>
                  <td className="px-6 py-4 text-right text-sm font-bold text-gray-900 dark:text-gray-100">
                    {formatCurrency(
                      section.items.reduce((sum, item) => sum + (item.total_amount || 0), 0)
                    )}
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
