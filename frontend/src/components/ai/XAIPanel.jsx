import React, { useState, useEffect } from 'react';
import { usePravaahStore } from '../../store/pravaahStore';
import { useAuthStore } from '../../store/authStore';
import { Brain, ChevronDown, ChevronUp, Loader, Play, AlertTriangle, Lock } from 'lucide-react';
import { getRiskBadgeClass, getAlertColors } from '../../utils/riskColorScale';

export default function XAIPanel() {
  const {
    selectedDistrictId,
    districts,
    analyses,
    runAnalysis,
    isRunningAnalysis,
    analysisError,
  } = usePravaahStore();
  const { isAuthenticated } = useAuthStore();

  const [expandedStep, setExpandedStep] = useState(null);
  
  const district = districts.find(d => d.district_id === selectedDistrictId);
  const analysis = selectedDistrictId ? analyses[selectedDistrictId] : null;
  const alertColors = analysis ? getAlertColors(analysis.alert_level) : null;

  return (
    <div className="flex flex-col h-full animate-fade-in relative overflow-hidden">
      <div className="px-5 py-3 border-b border-navy-800 bg-navy-900/50 flex justify-between items-center z-10">
        <div className="flex items-center gap-2">
          <Brain size={16} className="text-cyan-glow" />
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">6. Gemma 4 Reasoning</h3>
        </div>
        
        {/* Run Analysis Button */}
        <div className="relative group">
          <button
            onClick={() => isAuthenticated && runAnalysis(selectedDistrictId, !!analysis)}
            disabled={isRunningAnalysis || !selectedDistrictId || !isAuthenticated}
            className={`px-3 py-1 text-xs font-semibold rounded transition-colors flex items-center gap-1.5 border ${
              !isAuthenticated
                ? 'bg-navy-800 text-gray-500 border-navy-700 cursor-not-allowed opacity-60'
                : 'bg-cyan-glow/10 hover:bg-cyan-glow/20 text-cyan-glow border-cyan-glow/30 disabled:opacity-50 disabled:cursor-not-allowed'
            }`}
          >
            {isRunningAnalysis ? (
              <><Loader size={12} className="animate-spin" /> Analyzing…</>
            ) : !isAuthenticated ? (
              <><Lock size={10} className="text-gray-500" /> {analysis ? 'Refresh' : 'Run Analysis'}</>
            ) : (
              <><Play size={10} fill="currentColor" /> {analysis ? 'Refresh' : 'Run Analysis'}</>
            )}
          </button>
          
          {/* Tooltip for Locked State */}
          {!isAuthenticated && (
            <div className="absolute top-full right-0 mt-2 w-48 p-2 bg-navy-800 border border-navy-700 rounded-md shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              <p className="text-xs text-gray-300 text-center">Login to access this operational feature.</p>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 p-5 overflow-y-auto scrollbar-thin scrollbar-thumb-navy-700">
        {!selectedDistrictId && (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <Brain size={32} className="text-cyan-glow/30 mb-3" />
            <p className="text-sm text-gray-500">Select a district on the map to run Gemma 4 reasoning</p>
          </div>
        )}

        {analysisError && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-risk-critical/10 border border-risk-critical/20 mb-4">
            <AlertTriangle size={16} className="text-risk-critical flex-shrink-0 mt-0.5" />
            <p className="text-sm text-risk-critical">{analysisError}</p>
          </div>
        )}

        {isRunningAnalysis && (
          <div className="h-full flex flex-col justify-center max-w-sm mx-auto">
            <div className="flex items-center gap-3 mb-4">
              <Loader size={16} className="text-cyan-glow animate-spin" />
              <span className="text-sm text-cyan-glow font-medium animate-pulse">Powered by Gemma 4: Analyzing data...</span>
            </div>
            <div className="space-y-3">
              {['Processing multispectral satellite imagery...', 'Correlating river gauge telemetry...', 'Evaluating socioeconomic vulnerability...', 'Synthesizing actionable recommendations...'].map((step, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-glow/40 animate-pulse" style={{ animationDelay: `${i * 0.4}s` }} />
                  <span className="text-xs text-gray-400 font-mono" style={{ animationDelay: `${i * 0.4}s`, animationFillMode: 'both', animationName: 'fadeIn', animationDuration: '0.5s' }}>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {analysis && !isRunningAnalysis && (
          <div className="space-y-5">
            {/* Header info */}
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-lg font-bold text-white">{district?.district_name}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <span className="px-2 py-0.5 rounded text-xs font-bold" style={{ backgroundColor: alertColors?.bg, color: alertColors?.text }}>
                    {analysis.risk_category} RISK
                  </span>
                  <span className="text-xs text-gray-400">Confidence: {Math.round((analysis.confidence_score || 0.88)*100)}%</span>
                </div>
              </div>
            </div>

            {/* Executive Summary */}
            <div className="p-4 rounded-lg bg-navy-950/50 border border-navy-800 text-sm leading-relaxed text-gray-300 relative">
              <div className="absolute top-0 left-0 w-1 h-full rounded-l-lg" style={{ backgroundColor: alertColors?.border || '#00D4FF' }}></div>
              <p className="relative">
                {/* Simulated typing effect could be added here */}
                {analysis.executive_summary}
              </p>
            </div>

            {/* Reasoning Chain */}
            {analysis.reasoning_chain?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Reasoning Chain</h4>
                <div className="space-y-2">
                  {analysis.reasoning_chain.map((step) => (
                    <div key={step.step} className="border border-navy-800 rounded-lg overflow-hidden bg-navy-900/30">
                      <button
                        onClick={() => setExpandedStep(expandedStep === step.step ? null : step.step)}
                        className="w-full flex items-center justify-between p-3 text-left hover:bg-navy-800/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-5 h-5 rounded flex items-center justify-center bg-cyan-glow/10 text-cyan-glow text-[10px] font-bold">
                            {step.step}
                          </div>
                          <span className="text-sm font-medium text-gray-300">{step.title}</span>
                        </div>
                        {expandedStep === step.step ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
                      </button>
                      
                      {expandedStep === step.step && (
                        <div className="p-3 pt-0 pl-11 space-y-3 animate-slide-up bg-navy-800/10 border-t border-navy-800/50 mt-1">
                          <div>
                            <span className="text-[10px] text-cyan-glow uppercase tracking-wider block mb-1">Observation</span>
                            <span className="text-xs text-gray-400">{step.observation}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-cyan-glow uppercase tracking-wider block mb-1">Implication</span>
                            <span className="text-xs text-gray-300">{step.implication}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Recommendations */}
            {analysis.recommendations?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Action Plan</h4>
                <div className="space-y-2">
                  {analysis.recommendations.map((rec, i) => (
                    <div key={i} className="flex gap-3 p-3 rounded-lg bg-navy-950/30 border border-navy-800">
                      <div className={`mt-0.5 flex-shrink-0 w-2 h-2 rounded-full ${rec.priority === 1 ? 'bg-risk-critical animate-pulse' : 'bg-risk-moderate'}`}></div>
                      <div>
                        <p className="text-sm text-gray-200">{rec.action}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {rec.timeframe} · {rec.responsible_agency}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
