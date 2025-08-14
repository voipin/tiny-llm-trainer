import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Target, Plus, BarChart3, CheckCircle, XCircle } from 'lucide-react'

export default function Evaluation() {
  const queryClient = useQueryClient()
  
  const { data: evaluationRuns, isLoading } = useQuery({
    queryKey: ['evaluation-runs'],
    queryFn: () => apiClient.getEvaluationRuns(),
  })

  const startEvaluationMutation = useMutation({
    mutationFn: (id: number) => apiClient.startEvaluation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluation-runs'] })
    },
    onError: (error) => {
      console.error('Evaluation start failed:', error)
      alert('Failed to start evaluation. Please try again.')
    }
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'default'
      case 'running': return 'secondary'
      case 'failed': return 'destructive'
      default: return 'outline'
    }
  }

  const formatMetric = (metric: string, value: number) => {
    // Some metrics should be displayed as raw numbers, not percentages
    const rawNumberMetrics = ['total_samples', 'correct_samples']
    
    if (rawNumberMetrics.includes(metric)) {
      return value.toString()
    }
    
    // Other metrics are percentages (values between 0-1)
    return (value * 100).toFixed(1) + '%'
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Model Evaluation</h2>
          <p className="text-muted-foreground">
            Evaluate trained models with domain-specific metrics
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Run Evaluation
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {evaluationRuns?.map((run) => (
          <Card key={run.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <Target className="h-5 w-5 text-orange-600" />
                  <CardTitle className="text-lg">{run.name}</CardTitle>
                </div>
                <Badge variant={getStatusColor(run.status)}>
                  {run.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Model:</span>
                    <p className="font-medium">Model #{run.model}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Test Dataset:</span>
                    <p className="font-medium">Dataset #{run.test_dataset}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Created:</span>
                    <p>{new Date(run.created_at).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Status:</span>
                    <div className="flex items-center space-x-1">
                      {run.status === 'completed' ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : run.status === 'failed' ? (
                        <XCircle className="h-4 w-4 text-red-600" />
                      ) : null}
                      <span className="capitalize">{run.status}</span>
                    </div>
                  </div>
                </div>

                {run.results && Object.keys(run.results).length > 0 && (
                  <div className="border-t pt-3">
                    <h4 className="text-sm font-medium mb-3">Evaluation Metrics</h4>
                    <div className="space-y-2">
                      {Object.entries(run.results).map(([metric, value]) => (
                        <div key={metric} className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground capitalize">
                            {metric.replace('_', ' ')}:
                          </span>
                          <div className="flex items-center space-x-2">
                            <div className="w-20 bg-muted rounded-full h-2">
                              <div 
                                className="bg-primary h-2 rounded-full transition-all"
                                style={{ 
                                  width: ['total_samples', 'correct_samples'].includes(metric) 
                                    ? '100%' // Full bar for count metrics
                                    : `${(value as number) * 100}%` 
                                }}
                              />
                            </div>
                            <span className="text-sm font-mono w-12 text-right">
                              {formatMetric(metric, value as number)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex space-x-2 pt-2">
                  {run.status === 'pending' && (
                      <Button 
                        variant="success"
                        size="sm" 
                        className="w-full"
                        onClick={() => startEvaluationMutation.mutate(run.id)}
                        disabled={startEvaluationMutation.isPending}
                      >
                        {startEvaluationMutation.isPending ? 'Starting...' : 'Start Evaluation'}
                      </Button>
                  )}
                  {run.status === 'running' && (
                    <Button variant="outline" size="sm" className="w-full" disabled>
                      Running...
                    </Button>
                  )}
                  {run.status === 'completed' && (
                    <>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1"
                        onClick={() => {
                          const details = Object.entries(run.results || {})
                            .map(([key, value]) => `${key}: ${typeof value === 'number' ? (value * 100).toFixed(1) + '%' : value}`)
                            .join('\n');
                          alert(`Evaluation Details:\n\n${details}\n\nStatus: ${run.status}\nStarted: ${run.started_at ? new Date(run.started_at).toLocaleString() : 'N/A'}\nCompleted: ${run.completed_at ? new Date(run.completed_at).toLocaleString() : 'N/A'}`);
                        }}
                      >
                        <BarChart3 className="h-4 w-4 mr-1" />
                        Details
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1"
                        onClick={() => {
                          const exportData = {
                            name: run.name,
                            status: run.status,
                            model: run.model,
                            test_dataset: run.test_dataset,
                            created_at: run.created_at,
                            started_at: run.started_at,
                            completed_at: run.completed_at,
                            results: run.results,
                            evaluation_config: run.evaluation_config
                          };
                          const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `${run.name.toLowerCase().replace(/\s+/g, '_')}_evaluation_results.json`;
                          document.body.appendChild(a);
                          a.click();
                          window.URL.revokeObjectURL(url);
                          document.body.removeChild(a);
                        }}
                      >
                        Export
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {evaluationRuns?.length === 0 && (
          <div className="col-span-full">
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Target className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No evaluations yet</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Run your first model evaluation to measure performance.
                </p>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Run Your First Evaluation
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}