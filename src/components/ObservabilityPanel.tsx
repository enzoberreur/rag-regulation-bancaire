import { Activity, AlertCircle, DollarSign, Zap } from 'lucide-react';
import { Badge } from './ui/badge';

interface ObservabilityMetrics {
  latency: number;
  errors: number;
  cost: number;
  tokensUsed: number;
}

interface ObservabilityPanelProps {
  metrics: ObservabilityMetrics;
}

export function ObservabilityPanel({ metrics }: ObservabilityPanelProps) {
  const getLatencyColor = (latency: number) => {
    if (latency < 200) return 'text-green-600';
    if (latency < 500) return 'text-amber-600';
    return 'text-red-600';
  };

  const getLatencyBgColor = (latency: number) => {
    if (latency < 200) return 'bg-green-50';
    if (latency < 500) return 'bg-amber-50';
    return 'bg-red-50';
  };

  return (
    <div className="border-t border-neutral-200 bg-white px-8 py-4 relative">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#0066FF]/20 to-transparent"></div>
      
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className={`flex items-center gap-2.5 px-3 py-2 rounded-lg ${getLatencyBgColor(metrics.latency)} transition-smooth`}>
            <Zap className={`w-4 h-4 ${getLatencyColor(metrics.latency)}`} />
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
                ${metrics.cost.toFixed(4)}
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
        </div>

        <Badge 
          variant="outline" 
          className="bg-green-50 text-green-700 border-green-200 px-3 py-1.5 hover:bg-green-100 transition-smooth text-xs"
        >
          <div className="w-1.5 h-1.5 bg-green-600 rounded-full mr-2 animate-glow" />
          System Operational
        </Badge>
      </div>
    </div>
  );
}
