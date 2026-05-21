import { Package, Clock, DollarSign } from 'lucide-react'

export default function MaterialsList({ materials, laborHours, totalCost }) {
  // Mock materials data structure - this would come from the backend
  const defaultMaterials = {
    framing: [
      { name: '2x4 Studs (8ft)', quantity: 45, unit: 'pcs', unitCost: 3.5 },
      { name: '2x4 Studs (10ft)', quantity: 12, unit: 'pcs', unitCost: 4.25 },
      { name: 'Metal Track (10ft)', quantity: 8, unit: 'pcs', unitCost: 6.5 },
    ],
    drywall: [
      { name: '4x8 Drywall Sheets (1/2")', quantity: 85, unit: 'sheets', unitCost: 12.0 },
      { name: '4x8 Drywall Sheets (5/8")', quantity: 15, unit: 'sheets', unitCost: 14.5 },
    ],
    finishing: [
      { name: 'Joint Compound (5 gal)', quantity: 12, unit: 'buckets', unitCost: 18.0 },
      { name: 'Paper Tape (500ft)', quantity: 8, unit: 'rolls', unitCost: 8.5 },
      { name: 'Mesh Tape (300ft)', quantity: 4, unit: 'rolls', unitCost: 12.0 },
      { name: 'Corner Bead (10ft)', quantity: 24, unit: 'pcs', unitCost: 3.25 },
    ],
    fasteners: [
      { name: 'Drywall Screws (1-1/4")', quantity: 6, unit: 'lbs', unitCost: 8.5 },
      { name: 'Drywall Screws (1-5/8")', quantity: 4, unit: 'lbs', unitCost: 9.0 },
    ],
  }

  const materialsData = materials || defaultMaterials

  const calculateCategoryTotal = (items) => {
    return items.reduce((sum, item) => sum + (item.quantity * item.unitCost), 0)
  }

  const calculateTotalMaterials = () => {
    return Object.values(materialsData).reduce((total, category) => {
      return total + calculateCategoryTotal(category)
    }, 0)
  }

  const laborPhases = laborHours || [
    { phase: 'Framing', hours: 24, rate: 50 },
    { phase: 'Hanging Drywall', hours: 16, rate: 50 },
    { phase: 'Taping & Mudding (1st coat)', hours: 12, rate: 50 },
    { phase: 'Sanding & 2nd coat', hours: 10, rate: 50 },
    { phase: 'Final coat & touch-ups', hours: 8, rate: 50 },
    { phase: 'Cleanup', hours: 4, rate: 40 },
  ]

  const totalLaborCost = laborPhases.reduce((sum, phase) => sum + (phase.hours * phase.rate), 0)
  const totalMaterialsCost = calculateTotalMaterials()
  const grandTotal = totalCost || (totalLaborCost + totalMaterialsCost)

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600 font-medium">Materials Cost</p>
              <p className="text-2xl font-bold text-blue-900 mt-1">
                ${totalMaterialsCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Package className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600 font-medium">Labor Cost</p>
              <p className="text-2xl font-bold text-green-900 mt-1">
                ${totalLaborCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-green-600 mt-1">
                {laborPhases.reduce((sum, p) => sum + p.hours, 0)} hours total
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card bg-purple-50 border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-600 font-medium">Total Project Cost</p>
              <p className="text-2xl font-bold text-purple-900 mt-1">
                ${grandTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Materials Breakdown */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Materials Breakdown</h3>

        <div className="space-y-6">
          {/* Framing Materials */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3 flex items-center justify-between">
              <span>Framing Materials</span>
              <span className="text-primary-600">
                ${calculateCategoryTotal(materialsData.framing).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </h4>
            <div className="space-y-2">
              {materialsData.framing.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm py-2 border-b border-gray-100">
                  <span className="text-gray-700">{item.name}</span>
                  <div className="flex items-center space-x-4">
                    <span className="text-gray-600">{item.quantity} {item.unit}</span>
                    <span className="font-medium text-gray-900 w-20 text-right">
                      ${(item.quantity * item.unitCost).toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Drywall Sheets */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3 flex items-center justify-between">
              <span>Drywall Sheets</span>
              <span className="text-primary-600">
                ${calculateCategoryTotal(materialsData.drywall).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </h4>
            <div className="space-y-2">
              {materialsData.drywall.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm py-2 border-b border-gray-100">
                  <span className="text-gray-700">{item.name}</span>
                  <div className="flex items-center space-x-4">
                    <span className="text-gray-600">{item.quantity} {item.unit}</span>
                    <span className="font-medium text-gray-900 w-20 text-right">
                      ${(item.quantity * item.unitCost).toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Finishing Materials */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3 flex items-center justify-between">
              <span>Finishing Materials</span>
              <span className="text-primary-600">
                ${calculateCategoryTotal(materialsData.finishing).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </h4>
            <div className="space-y-2">
              {materialsData.finishing.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm py-2 border-b border-gray-100">
                  <span className="text-gray-700">{item.name}</span>
                  <div className="flex items-center space-x-4">
                    <span className="text-gray-600">{item.quantity} {item.unit}</span>
                    <span className="font-medium text-gray-900 w-20 text-right">
                      ${(item.quantity * item.unitCost).toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Fasteners */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3 flex items-center justify-between">
              <span>Fasteners & Hardware</span>
              <span className="text-primary-600">
                ${calculateCategoryTotal(materialsData.fasteners).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </h4>
            <div className="space-y-2">
              {materialsData.fasteners.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm py-2 border-b border-gray-100">
                  <span className="text-gray-700">{item.name}</span>
                  <div className="flex items-center space-x-4">
                    <span className="text-gray-600">{item.quantity} {item.unit}</span>
                    <span className="font-medium text-gray-900 w-20 text-right">
                      ${(item.quantity * item.unitCost).toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Labor Breakdown */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Labor Breakdown by Phase</h3>

        <div className="space-y-2">
          {laborPhases.map((phase, idx) => (
            <div key={idx} className="flex items-center justify-between text-sm py-3 border-b border-gray-100">
              <span className="text-gray-700 font-medium">{phase.phase}</span>
              <div className="flex items-center space-x-6">
                <span className="text-gray-600">{phase.hours} hrs @ ${phase.rate}/hr</span>
                <span className="font-medium text-gray-900 w-24 text-right">
                  ${(phase.hours * phase.rate).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          ))}
          <div className="flex items-center justify-between text-sm py-3 font-semibold">
            <span className="text-gray-900">Total Labor</span>
            <span className="text-gray-900 w-24 text-right">
              ${totalLaborCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </div>

      {/* Project Total */}
      <div className="card bg-gradient-to-r from-primary-50 to-purple-50 border-primary-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 font-medium">Project Total</p>
            <p className="text-xs text-gray-500 mt-1">Materials + Labor</p>
          </div>
          <p className="text-3xl font-bold text-primary-600">
            ${grandTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        </div>
      </div>
    </div>
  )
}
