import { useState, useRef } from 'react';
import {
  Upload,
  FileText,
  CheckCircle,
  Loader,
  Download,
  BarChart3,
  DollarSign,
  List,
  Target
} from 'lucide-react';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

function App() {
  const [activeTab, setActiveTab] = useState('upload'); // upload, processing, results
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [boqData, setBoqData] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError(null);
    } else {
      setError('Please upload a PDF file');
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError(null);
    } else {
      setError('Please upload a PDF file');
    }
  };

  const simulateProcessing = () => {
    return new Promise((resolve) => {
      const duration = 8000 + Math.random() * 7000; // 8-15 seconds
      const startTime = Date.now();

      const updateProgress = () => {
        const elapsed = Date.now() - startTime;
        const newProgress = Math.min((elapsed / duration) * 100, 100);
        setProgress(newProgress);

        if (newProgress < 100) {
          requestAnimationFrame(updateProgress);
        } else {
          resolve();
        }
      };

      updateProgress();
    });
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setActiveTab('processing');
    setIsProcessing(true);
    setProgress(0);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Start both the API call and the progress simulation
      const [apiResponse] = await Promise.all([
        fetch('http://localhost:5000/api/process-drawing', {
          method: 'POST',
          body: formData,
        }),
        simulateProcessing()
      ]);

      if (!apiResponse.ok) {
        const errorData = await apiResponse.json();
        throw new Error(errorData.error || 'Failed to process drawing');
      }

      const data = await apiResponse.json();
      setBoqData(data);
      setActiveTab('results');
    } catch (err) {
      setError(err.message);
      setActiveTab('upload');
    } finally {
      setIsProcessing(false);
      setProgress(0);
    }
  };

  const exportToCSV = () => {
    if (!boqData || !boqData.boqItems) return;

    const csvContent = [
      ['Item', 'Description', 'Quantity', 'Unit', 'Rate', 'Amount'],
      ...boqData.boqItems.map(item => [
        item.item,
        item.description,
        item.qty,
        item.unit,
        item.rate,
        item.amount
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, `BOQ_${boqData.projectName.replace(/\s+/g, '_')}.csv`);
  };

  const exportToExcel = () => {
    if (!boqData || !boqData.boqItems) return;

    const worksheet = XLSX.utils.json_to_sheet(
      boqData.boqItems.map(item => ({
        'Item': item.item,
        'Description': item.description,
        'Quantity': item.qty,
        'Unit': item.unit,
        'Rate': item.rate,
        'Amount': item.amount
      }))
    );

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'BOQ');

    XLSX.writeFile(workbook, `BOQ_${boqData.projectName.replace(/\s+/g, '_')}.xlsx`);
  };

  const resetApp = () => {
    setActiveTab('upload');
    setSelectedFile(null);
    setBoqData(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-black/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BarChart3 className="w-8 h-8 text-cyan-400" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                TakeoffAI
              </h1>
            </div>
            <p className="text-gray-400 text-sm">AI-Powered BOQ Estimation</p>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="border-b border-gray-800 bg-black/30">
        <div className="container mx-auto px-6">
          <div className="flex space-x-1">
            <button
              onClick={() => !isProcessing && setActiveTab('upload')}
              disabled={isProcessing}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'upload'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-gray-400 hover:text-gray-300'
              } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="flex items-center space-x-2">
                <Upload className="w-4 h-4" />
                <span>Upload</span>
              </div>
            </button>
            <button
              onClick={() => !isProcessing && setActiveTab('processing')}
              disabled={!boqData && !isProcessing}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'processing'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-gray-400 hover:text-gray-300'
              } ${(!boqData && !isProcessing) ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="flex items-center space-x-2">
                <Loader className="w-4 h-4" />
                <span>Processing</span>
              </div>
            </button>
            <button
              onClick={() => !isProcessing && boqData && setActiveTab('results')}
              disabled={!boqData || isProcessing}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'results'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-gray-400 hover:text-gray-300'
              } ${(!boqData || isProcessing) ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4" />
                <span>Results</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-2">Upload Construction Drawing</h2>
              <p className="text-gray-400">Upload a PDF drawing to generate an automated BOQ</p>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
                {error}
              </div>
            )}

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
                isDragging
                  ? 'border-cyan-400 bg-cyan-400/10'
                  : 'border-gray-700 hover:border-gray-600 bg-gray-900/50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="hidden"
              />

              <FileText className={`w-16 h-16 mx-auto mb-4 ${
                isDragging ? 'text-cyan-400' : 'text-gray-600'
              }`} />

              {selectedFile ? (
                <div>
                  <p className="text-lg font-medium text-cyan-400 mb-2">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-400">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-lg font-medium mb-2">
                    Drag & drop your PDF here
                  </p>
                  <p className="text-gray-400">or click to browse</p>
                </div>
              )}
            </div>

            <div className="mt-8 flex justify-center">
              <button
                onClick={handleUpload}
                disabled={!selectedFile}
                className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:from-gray-700 disabled:to-gray-800 disabled:cursor-not-allowed rounded-lg font-medium transition-all transform hover:scale-105 disabled:hover:scale-100 flex items-center space-x-2"
              >
                <Upload className="w-5 h-5" />
                <span>Process Drawing</span>
              </button>
            </div>
          </div>
        )}

        {/* Processing Tab */}
        {activeTab === 'processing' && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-2">Processing Drawing</h2>
              <p className="text-gray-400">AI is analyzing your construction drawing...</p>
            </div>

            <div className="bg-gray-900/50 rounded-xl p-8 border border-gray-800">
              <div className="flex justify-center mb-8">
                <div className="relative">
                  <div className="w-24 h-24 border-4 border-gray-700 border-t-cyan-400 rounded-full animate-spin"></div>
                  <Loader className="w-12 h-12 text-cyan-400 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                </div>
              </div>

              <div className="mb-6">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400">Progress</span>
                  <span className="text-cyan-400 font-medium">{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300 rounded-full"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-3 text-sm text-gray-400">
                <div className={`flex items-center ${progress > 10 ? 'text-cyan-400' : ''}`}>
                  <CheckCircle className={`w-5 h-5 mr-3 ${progress > 10 ? 'text-cyan-400' : 'text-gray-600'}`} />
                  <span>Uploading PDF drawing...</span>
                </div>
                <div className={`flex items-center ${progress > 30 ? 'text-cyan-400' : ''}`}>
                  <CheckCircle className={`w-5 h-5 mr-3 ${progress > 30 ? 'text-cyan-400' : 'text-gray-600'}`} />
                  <span>Extracting text and specifications...</span>
                </div>
                <div className={`flex items-center ${progress > 60 ? 'text-cyan-400' : ''}`}>
                  <CheckCircle className={`w-5 h-5 mr-3 ${progress > 60 ? 'text-cyan-400' : 'text-gray-600'}`} />
                  <span>Analyzing with Claude AI...</span>
                </div>
                <div className={`flex items-center ${progress > 90 ? 'text-cyan-400' : ''}`}>
                  <CheckCircle className={`w-5 h-5 mr-3 ${progress > 90 ? 'text-cyan-400' : 'text-gray-600'}`} />
                  <span>Generating BOQ...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && boqData && (
          <div>
            <div className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-3xl font-bold mb-2">{boqData.projectName}</h2>
                <p className="text-gray-400">{boqData.projectType}</p>
              </div>
              <button
                onClick={resetApp}
                className="px-6 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all"
              >
                New Upload
              </button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Total Value</p>
                    <p className="text-2xl font-bold text-cyan-400">
                      ₹{boqData.totalValue?.toLocaleString('en-IN') || '0'}
                    </p>
                  </div>
                  <DollarSign className="w-10 h-10 text-cyan-400 opacity-50" />
                </div>
              </div>

              <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Line Items</p>
                    <p className="text-2xl font-bold text-blue-400">{boqData.lineItems || 0}</p>
                  </div>
                  <List className="w-10 h-10 text-blue-400 opacity-50" />
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Accuracy</p>
                    <p className="text-2xl font-bold text-purple-400">{boqData.accuracy || 'N/A'}</p>
                  </div>
                  <Target className="w-10 h-10 text-purple-400 opacity-50" />
                </div>
              </div>

              <div className="bg-gradient-to-br from-green-500/10 to-cyan-500/10 border border-green-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Processing Time</p>
                    <p className="text-2xl font-bold text-green-400">{boqData.processingTime || 0}s</p>
                  </div>
                  <Loader className="w-10 h-10 text-green-400 opacity-50" />
                </div>
              </div>
            </div>

            {/* Export Buttons */}
            <div className="flex space-x-4 mb-6">
              <button
                onClick={exportToCSV}
                className="px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 rounded-lg font-medium transition-all flex items-center space-x-2"
              >
                <Download className="w-5 h-5" />
                <span>Export CSV</span>
              </button>
              <button
                onClick={exportToExcel}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-lg font-medium transition-all flex items-center space-x-2"
              >
                <Download className="w-5 h-5" />
                <span>Export Excel</span>
              </button>
            </div>

            {/* BOQ Table */}
            <div className="bg-gray-900/50 rounded-xl border border-gray-800 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-800/50 border-b border-gray-700">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">Item</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">Description</th>
                      <th className="px-6 py-4 text-right text-sm font-medium text-gray-300">Qty</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">Unit</th>
                      <th className="px-6 py-4 text-right text-sm font-medium text-gray-300">Rate (₹)</th>
                      <th className="px-6 py-4 text-right text-sm font-medium text-gray-300">Amount (₹)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {boqData.boqItems?.map((item, index) => (
                      <tr key={index} className="hover:bg-gray-800/30 transition-colors">
                        <td className="px-6 py-4 text-sm text-cyan-400">{item.item}</td>
                        <td className="px-6 py-4 text-sm text-gray-300">{item.description}</td>
                        <td className="px-6 py-4 text-sm text-right text-gray-300">{item.qty?.toLocaleString('en-IN')}</td>
                        <td className="px-6 py-4 text-sm text-gray-400">{item.unit}</td>
                        <td className="px-6 py-4 text-sm text-right text-gray-300">
                          {item.rate?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4 text-sm text-right font-medium text-cyan-400">
                          {item.amount?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-gray-800/50 border-t-2 border-cyan-500">
                    <tr>
                      <td colSpan="5" className="px-6 py-4 text-right font-bold text-lg">Total:</td>
                      <td className="px-6 py-4 text-right font-bold text-lg text-cyan-400">
                        ₹{boqData.totalValue?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-black/30 mt-12">
        <div className="container mx-auto px-6 py-6 text-center text-gray-400 text-sm">
          <p>© 2024 TakeoffAI - Powered by Claude AI</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
