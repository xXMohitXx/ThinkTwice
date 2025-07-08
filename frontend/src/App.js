import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import './App.css';
import { MoonIcon, SunIcon, Cog6ToothIcon, ExclamationTriangleIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Simulate Grammarly-like monitoring
const SIMULATED_APPS = [
  { name: 'Email', placeholder: 'Write your email here...' },
  { name: 'Chat', placeholder: 'Type your message...' },
  { name: 'Social Media', placeholder: 'What\'s on your mind?' },
  { name: 'Comments', placeholder: 'Add a comment...' },
  { name: 'Review', placeholder: 'Write a review...' }
];

function getInitialDarkMode() {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('thinktwice-darkmode');
    if (stored !== null) return stored === 'true';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  return false;
}

function App() {
  const [text, setText] = useState('');
  const [threshold, setThreshold] = useState(0.5);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const [userId] = useState('user-' + Math.random().toString(36).substr(2, 9));
  const [analytics, setAnalytics] = useState(null);
  const [selectedApp, setSelectedApp] = useState(SIMULATED_APPS[0]);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [monitoringLogs, setMonitoringLogs] = useState([]);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(getInitialDarkMode());
  const [settingsOpen, setSettingsOpen] = useState(false);
  const abortControllerRef = useRef(null);

  // Debounced text analysis with better error handling
  const analyzeText = useCallback(async (textToAnalyze, currentThreshold) => {
    if (!textToAnalyze.trim()) {
      setAnalysis(null);
      setShowWarning(false);
      setError(null);
      return;
    }

    // Cancel previous request if still pending
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/analyze-text`, {
        text: textToAnalyze,
        threshold: currentThreshold
      }, {
        signal: abortControllerRef.current.signal,
        timeout: 10000 // 10 second timeout
      });
      
      setAnalysis(response.data);
      setShowWarning(response.data.should_warn);
      
      // Add to monitoring logs
      if (isMonitoring) {
        const logEntry = {
          timestamp: new Date().toLocaleTimeString(),
          app: selectedApp.name,
          text: textToAnalyze.slice(0, 50) + (textToAnalyze.length > 50 ? '...' : ''),
          regretScore: response.data.regret_score,
          warned: response.data.should_warn
        };
        setMonitoringLogs(prev => [logEntry, ...prev.slice(0, 9)]);
      }
      
    } catch (error) {
      if (error.name === 'AbortError') {
        // Request was cancelled, ignore
        return;
      }
      
      console.error('Error analyzing text:', error);
      setError(`Analysis failed: ${error.message}`);
      setAnalysis(null);
      setShowWarning(false);
    } finally {
      setLoading(false);
    }
  }, [selectedApp, isMonitoring]);

  // Debounce effect
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      analyzeText(text, threshold);
    }, 300); // Reduced debounce time for faster response

    return () => clearTimeout(debounceTimer);
  }, [text, threshold, analyzeText]);

  // Save user settings
  const saveSettings = async (newThreshold) => {
    try {
      await axios.post(`${API_BASE_URL}/api/user-settings`, {
        user_id: userId,
        threshold: newThreshold
      });
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  // Load analytics
  const loadAnalytics = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/analytics`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  // Test API connection
  const testConnection = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/health`);
      console.log('API Health:', response.data);
      setError(null);
    } catch (error) {
      setError(`Connection failed: ${error.message}`);
      console.error('API connection test failed:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
    testConnection();
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
    localStorage.setItem('thinktwice-darkmode', darkMode);
  }, [darkMode]);

  const handleThresholdChange = (newThreshold) => {
    setThreshold(newThreshold);
    saveSettings(newThreshold);
  };

  const getRegretScoreColor = (score) => {
    if (score < 0.3) return 'text-green-500';
    if (score < 0.6) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getRegretScoreLabel = (score) => {
    if (score < 0.2) return 'Safe';
    if (score < 0.4) return 'Caution';
    if (score < 0.6) return 'Risky';
    return 'High Risk';
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${darkMode ? 'bg-gradient-to-br from-slate-900 to-slate-800' : 'bg-gradient-to-br from-slate-50 to-slate-100'}`}>
      {/* Top Bar */}
      <div className={`w-full flex items-center justify-between px-4 py-3 shadow-md ${darkMode ? 'bg-slate-900 border-b border-slate-700' : 'bg-white border-b border-slate-200'}`}>
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold select-none ${darkMode ? 'text-white' : 'text-slate-800'}">🛑 ThinkTwice</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            aria-label="Settings"
            className="p-2 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 transition"
            onClick={() => setSettingsOpen(v => !v)}
          >
            <Cog6ToothIcon className={`w-6 h-6 ${darkMode ? 'text-slate-300' : 'text-slate-600'}`} />
          </button>
        </div>
      </div>
      {/* Settings Modal */}
      {settingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setSettingsOpen(false)}>
          <div className={`bg-white dark:bg-slate-800 rounded-xl shadow-xl p-6 min-w-[300px] relative animate-fadeIn`} onClick={e => e.stopPropagation()}>
            <button className="absolute top-2 right-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" onClick={() => setSettingsOpen(false)}>&times;</button>
            <h2 className="text-lg font-semibold mb-4 text-slate-800 dark:text-slate-100 flex items-center gap-2"><Cog6ToothIcon className="w-5 h-5" /> Settings</h2>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-slate-700 dark:text-slate-200">Dark Mode</span>
              <button
                className={`ml-auto flex items-center gap-1 px-3 py-1 rounded-full transition ${darkMode ? 'bg-slate-700 text-white' : 'bg-slate-200 text-slate-700'}`}
                onClick={() => setDarkMode(dm => !dm)}
              >
                {darkMode ? <MoonIcon className="w-5 h-5" /> : <SunIcon className="w-5 h-5" />}
                {darkMode ? 'On' : 'Off'}
              </button>
            </div>
            {/* Future settings can go here */}
          </div>
        </div>
      )}
      <div className="container mx-auto px-2 sm:px-4 py-6 max-w-2xl">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className={`text-3xl sm:text-4xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-slate-800'}`}>🛑 ThinkTwice</h1>
          <p className={`text-slate-500 dark:text-slate-300 text-base sm:text-lg`}>Real-Time Regret Prevention - Like Grammarly for Emotional Intelligence</p>
          {error && (
            <div className="mt-4 p-3 bg-red-100 dark:bg-red-900/60 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 rounded-lg flex items-center gap-3 animate-shake">
              <ExclamationCircleIcon className="w-5 h-5" />
              {error}
              <button 
                onClick={testConnection}
                className="ml-auto px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
              >
                Retry
              </button>
            </div>
          )}
        </div>

        {/* Monitoring Toggle */}
        <div className="max-w-4xl mx-auto mb-6">
          <div className="bg-white rounded-lg shadow-md p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-slate-700">System Monitoring:</span>
              <button
                onClick={() => setIsMonitoring(!isMonitoring)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  isMonitoring 
                    ? 'bg-green-500 text-white' 
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                {isMonitoring ? '🟢 ON' : '🔴 OFF'}
              </button>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Simulating:</span>
              <select
                value={selectedApp.name}
                onChange={(e) => setSelectedApp(SIMULATED_APPS.find(app => app.name === e.target.value))}
                className="px-3 py-1 border border-slate-300 rounded-lg text-sm"
              >
                {SIMULATED_APPS.map(app => (
                  <option key={app.name} value={app.name}>{app.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Main Card */}
        <div className={`rounded-2xl shadow-xl p-4 sm:p-8 mb-8 transition-colors duration-300 ${darkMode ? 'bg-slate-900 border border-slate-700' : 'bg-white border border-slate-200'}`}> 
          {/* Message Box */}
          <div className="mb-6">
            <textarea
              className={`w-full min-h-[100px] max-h-[200px] rounded-lg p-3 text-base transition-colors duration-200 border focus:outline-none focus:ring-2 focus:ring-blue-400 resize-vertical ${darkMode ? 'bg-slate-800 text-white border-slate-700' : 'bg-slate-100 text-slate-800 border-slate-300'}`}
              placeholder={selectedApp.placeholder}
              value={text}
              onChange={e => setText(e.target.value)}
              autoFocus
            />
          </div>
          {/* Regret Threshold Slider */}
          <div className="mb-6">
            <div className="flex items-center gap-3">
              <span className="text-sm text-slate-500 dark:text-slate-300">Regret Threshold</span>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.01"
                value={threshold}
                onChange={e => handleThresholdChange(parseFloat(e.target.value))}
                className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <span className="text-xs text-slate-500 dark:text-slate-300">{threshold}</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">Adjust how sensitive the warning system should be</p>
          </div>
          {/* Warning Alert */}
          {showWarning && analysis && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/60 border-l-4 border-red-500 dark:border-red-700 rounded-r-lg animate-pulse flex items-center gap-3 shadow-lg">
              <ExclamationTriangleIcon className="w-6 h-6 text-red-500 dark:text-red-300 animate-bounce" />
              <div>
                <h3 className="text-sm font-semibold text-red-800 dark:text-red-200 flex items-center gap-1">
                  ⚠️ Think Twice Before Sending
                </h3>
                <p className="mt-1 text-sm text-red-700 dark:text-red-200">This message might be regrettable. Consider rephrasing before sending.</p>
              </div>
            </div>
          )}
          {/* Analysis Results */}
          {analysis && (
            <div className="mb-8 animate-fadeIn">
              <h3 className={`text-lg font-semibold mb-4 flex items-center gap-2 ${darkMode ? 'text-white' : 'text-slate-800'}`}>
                <CheckCircleIcon className="w-5 h-5 text-green-500 dark:text-green-300" /> Analysis Results
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Overall Score */}
                <div className={`rounded-lg p-4 flex flex-col items-center ${darkMode ? 'bg-slate-800' : 'bg-slate-50'}`}>
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">Overall Regret Score</span>
                  <span className={`text-2xl font-bold mb-2 ${getRegretScoreColor(analysis.regret_score)}`}>{getRegretScoreLabel(analysis.regret_score)}</span>
                  <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 mb-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        analysis.regret_score < 0.3 ? 'bg-green-500 dark:bg-green-400' :
                        analysis.regret_score < 0.6 ? 'bg-yellow-500 dark:bg-yellow-400' : 'bg-red-500 dark:bg-red-400'
                      }`}
                      style={{ width: `${Math.min(analysis.regret_score * 100, 100)}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-slate-500 dark:text-slate-300">{(analysis.regret_score * 100).toFixed(1)}%</span>
                </div>
                {/* Detailed Breakdown */}
                <div className={`rounded-lg p-4 ${darkMode ? 'bg-slate-800' : 'bg-slate-50'}`}> 
                  <h4 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-3">Detailed Analysis</h4>
                  <div className="space-y-2">
                    {Object.entries(analysis.analysis).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between">
                        <span className="text-xs text-slate-500 dark:text-slate-300 capitalize flex items-center gap-1">
                          {key.replace('_', ' ')}
                          {value > 0.6 && <ExclamationTriangleIcon className="w-4 h-4 text-red-400 dark:text-red-300 animate-bounce" />}
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-200 dark:bg-slate-700 rounded-full h-1">
                            <div 
                              className={`h-1 rounded-full transition-all duration-300 ${
                                value < 0.3 ? 'bg-green-400 dark:bg-green-300' :
                                value < 0.6 ? 'bg-yellow-400 dark:bg-yellow-300' : 'bg-red-400 dark:bg-red-300'
                              }`}
                              style={{ width: `${Math.min(value * 100, 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-slate-600 dark:text-slate-200 w-8 text-right">{(value * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Monitoring Logs */}
          {isMonitoring && monitoringLogs.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Live Monitoring Feed</h3>
              <div className="bg-slate-50 rounded-lg p-4 max-h-60 overflow-y-auto">
                {monitoringLogs.map((log, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-slate-200 last:border-b-0">
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-500">{log.timestamp}</span>
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                        {log.app}
                      </span>
                      <span className="text-xs text-slate-600">{log.text}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-medium ${getRegretScoreColor(log.regretScore)}`}>
                        {(log.regretScore * 100).toFixed(0)}%
                      </span>
                      {log.warned && (
                        <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                          ⚠️ Warned
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Analytics Dashboard */}
          {analytics && (
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Your Usage Statistics</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {analytics.total_analyses}
                  </div>
                  <div className="text-sm text-blue-600">Total Analyses</div>
                </div>
                <div className="bg-red-50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {analytics.warned_analyses}
                  </div>
                  <div className="text-sm text-red-600">Warnings Triggered</div>
                </div>
                <div className="bg-green-50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {((1 - analytics.warning_rate) * 100).toFixed(0)}%
                  </div>
                  <div className="text-sm text-green-600">Safe Messages</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Features Section */}
        <div className="max-w-4xl mx-auto mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="bg-blue-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Real-Time Analysis</h3>
            <p className="text-slate-600 text-sm">
              Instant feedback as you type, powered by advanced NLP models
            </p>
          </div>

          <div className="text-center">
            <div className="bg-green-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">System Monitoring</h3>
            <p className="text-slate-600 text-sm">
              Monitor text across different apps like Grammarly does
            </p>
          </div>

          <div className="text-center">
            <div className="bg-purple-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Customizable</h3>
            <p className="text-slate-600 text-sm">
              Adjust sensitivity levels to match your communication style
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-slate-500 dark:text-slate-400 text-xs">
          <p>ThinkTwice - Helping you communicate better, one message at a time</p>
        </div>
      </div>
    </div>
  );
}

export default App;