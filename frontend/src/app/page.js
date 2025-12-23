'use client';

import { useState } from 'react';
import { Send, BarChart3, Database, Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import { generateSql, executeSql, generateInsights } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function Home() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('');
  const [error, setError] = useState('');

  const [sql, setSql] = useState('');
  const [resultData, setResultData] = useState(null);
  const [insights, setInsights] = useState('');

  const handleSearch = async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    setError('');
    setSql('');
    setResultData(null);
    setInsights('');
    
    try {
      setStep('Generating SQL...');
      const sqlRes = await generateSql(question);
      setSql(sqlRes.sql_query);

      setStep('Executing Query...');
      const dataRes = await executeSql(sqlRes.sql_query);
      
      if (!dataRes.data || dataRes.data.length === 0) {
        setError('No data found for this query.');
        setLoading(false);
        return;
      }
      
      // Store data safely
      setResultData(dataRes);

      setStep('Analyzing Data...');
      generateInsights(dataRes.data).then(res => {
        setInsights(res.insights);
      }).catch(err => console.error("Insight error:", err));

    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
      setStep('');
    }
  };

  const getChartConfig = () => {
    // Safety check: ensure resultData exists before accessing it
    if (!resultData || !resultData.data || !resultData.data.length) return null;
    
    const keys = Object.keys(resultData.data[0]);
    const xKey = keys.find(k => typeof resultData.data[0][k] === 'string') || keys[0];
    const yKey = keys.find(k => typeof resultData.data[0][k] === 'number');

    return { xKey, yKey };
  };

  const chartConfig = getChartConfig();

  return (
    <main className="min-h-screen bg-slate-50 p-8 font-sans text-slate-800">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <header className="text-center space-y-2 mb-10">
          <h1 className="text-4xl font-extrabold text-indigo-600 flex items-center justify-center gap-3">
            <BarChart3 className="w-10 h-10" /> InsightGen
          </h1>
          <p className="text-slate-500">Convert natural language into business insights instantly.</p>
        </header>

        <div className="bg-white p-2 rounded-2xl shadow-lg shadow-indigo-100 border border-indigo-50 max-w-3xl mx-auto">
          <div className="flex items-center gap-2 p-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question (e.g., 'Show total sales by category')"
              className="flex-1 p-4 bg-transparent outline-none text-lg text-slate-700 placeholder:text-slate-400"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-4 rounded-xl font-medium transition-all flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed shadow-md shadow-indigo-200"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              {loading ? step : 'Analyze'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-xl flex items-center gap-3 border border-red-100 max-w-3xl mx-auto">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        {/* CRITICAL FIX: Changed condition from (sql || resultData) 
            to ensure individual components only render when their specific data is ready.
        */}
        {(sql || resultData) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            
            {/* 1. Generated SQL - Shows as soon as SQL exists */}
            {sql && (
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-700">
                  <Database className="w-5 h-5 text-blue-500" /> Generated SQL
                </h2>
                <div className="bg-slate-900 text-slate-50 p-4 rounded-xl font-mono text-sm overflow-x-auto flex-1">
                  {sql}
                </div>
              </div>
            )}

            {/* 2. AI Insights - Shows placeholder until insights arrive */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-700">
                <Sparkles className="w-5 h-5 text-amber-500" /> AI Insights
              </h2>
              <div className="prose prose-sm text-slate-600 flex-1">
                {insights ? (
                   <div className="whitespace-pre-line leading-relaxed">{insights}</div>
                ) : (
                  <div className="flex items-center gap-2 text-slate-400 italic">
                     {loading && resultData ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                     {resultData ? "Generating insights..." : "Insights will appear here..."}
                  </div>
                )}
              </div>
            </div>

            {/* 3. Data Visualization - Only renders if resultData AND chartConfig exist */}
            {resultData && chartConfig && chartConfig.yKey && (
              <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-100 min-h-[400px]">
                <h2 className="text-lg font-semibold mb-6 flex items-center gap-2 text-slate-700">
                  <BarChart3 className="w-5 h-5 text-indigo-500" /> Visualization
                </h2>
                <div className="h-[350px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={resultData.data}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                      <XAxis 
                        dataKey={chartConfig.xKey} 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{fill: '#64748B', fontSize: 12}} 
                        dy={10}
                      />
                      <YAxis 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{fill: '#64748B', fontSize: 12}} 
                      />
                      <Tooltip 
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        cursor={{ fill: '#F1F5F9' }}
                      />
                      <Bar 
                        dataKey={chartConfig.yKey} 
                        fill="#6366f1" 
                        radius={[6, 6, 0, 0]} 
                        barSize={60}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* 4. Data Table - CRITICAL FIX: Only renders if resultData exists */}
            {resultData && (
              <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                 <h2 className="text-lg font-semibold mb-4 text-slate-700">Raw Data</h2>
                 <div className="overflow-x-auto">
                   <table className="w-full text-left border-collapse">
                     <thead>
                       <tr className="border-b border-slate-100 bg-slate-50/50">
                         {resultData.columns.map((col) => (
                           <th key={col} className="p-4 font-semibold text-slate-600 text-sm tracking-wide">{col}</th>
                         ))}
                       </tr>
                     </thead>
                     <tbody>
                       {resultData.data.map((row, i) => (
                         <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                           {resultData.columns.map((col) => (
                             <td key={col} className="p-4 text-sm text-slate-600">{row[col]}</td>
                           ))}
                         </tr>
                       ))}
                     </tbody>
                   </table>
                 </div>
              </div>
            )}

          </div>
        )}
      </div>
    </main>
  );
}