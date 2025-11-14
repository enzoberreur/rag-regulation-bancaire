import { Activity, AlertCircle, DollarSign, Zap, FileText, Target } from 'lucide-react';

interface ObservabilityMetrics {
  latency: number;
  errors: number;
  cost: number;
  tokensUsed: number;
  citationsCount?: number;
  averageSimilarityScore?: number;
}

interface ObservabilityPanelProps {
  metrics: ObservabilityMetrics;
}

export function ObservabilityPanel({ metrics }: ObservabilityPanelProps) {
  const getLatencyColor = (latency: number) => {
    if (latency < 200) return 'text-green-600';
    if (latency < 500) return 'text-blue-600';
    if (latency < 1000) return 'text-amber-600';
    return 'text-neutral-700';
  };

  const getLatencyBgColor = (latency: number) => {
    if (latency < 200) return 'bg-neutral-50';
    if (latency < 500) return 'bg-neutral-50';
    if (latency < 1000) return 'bg-neutral-50';
    return 'bg-neutral-50';
  };

  return (
    <div className="border-t border-neutral-200 bg-white px-8 py-4 relative">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#0066FF]/20 to-transparent"></div>
      
      <div className="max-w-4xl mx-auto flex items-center justify-start">
        <div className="flex items-center gap-6">
          <div className={`flex items-center gap-2.5 px-3 py-2 rounded-lg ${getLatencyBgColor(metrics.latency)} transition-smooth`}>
            <Zap className="w-4 h-4 text-[#0066FF]" />
            <div className="text-xs">
              <span className="text-neutral-500 mr-1.5">Response:</span>
              <span className={`${getLatencyColor(metrics.latency)}`}>
                {metrics.latency}ms
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-neutral-50">
            <AlertCircle className={`w-4 h-4 ${metrics.errors > 0 ? 'text-red-600' : 'text-green-600'}`} />
            <div className="text-xs">
              <span className="text-neutral-500 mr-1.5">Errors:</span>
              <span className={metrics.errors > 0 ? 'text-red-600' : 'text-green-600'}>
                {metrics.errors}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-neutral-50">
            <DollarSign className="w-4 h-4 text-[#0066FF]" />
            <div className="text-xs">
              <span className="text-neutral-500 mr-1.5">Cost:</span>
              <span className="text-neutral-900">
                ${(metrics.cost ?? 0).toFixed(4)}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-neutral-50">
            <Activity className="w-4 h-4 text-[#0066FF]" />
            <div className="text-xs">
              <span className="text-neutral-500 mr-1.5">Tokens:</span>
              <span className="text-neutral-900">
                {metrics.tokensUsed.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-neutral-50">
            <FileText className="w-4 h-4 text-[#0066FF]" />
            <div className="text-xs">
              <span className="text-neutral-500 mr-1.5">Citations:</span>
              <span className="text-neutral-900">
                {metrics.citationsCount ?? 0}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-neutral-50">
            <Target className="w-4 h-4 text-[#0066FF]" />
            <div className="text-xs">
              <span className="text-neutral-500 mr-1.5">Similarity:</span>
              <span className="text-neutral-900">
                {metrics.averageSimilarityScore !== undefined 
                  ? `${(metrics.averageSimilarityScore * 100).toFixed(1)}%`
                  : '0.0%'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
