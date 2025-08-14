import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Brain, Plus, Play, Pause, BarChart3 } from 'lucide-react'

export default function Training() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const { data: trainingRuns, isLoading } = useQuery({
    queryKey: ['training-runs'],
    queryFn: () => apiClient.getTrainingRuns(),
  })

  const startTrainingMutation = useMutation({
    mutationFn: (id: number) => apiClient.startTraining(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training-runs'] })
    },
    onError: (error) => {
      console.error('Training start failed:', error)
      alert('Failed to start training. Please try again.')
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
      case 'cancelled': return 'outline'
      default: return 'outline'
    }
  }

  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime) return 'Not started'
    if (!endTime) return 'Running...'
    
    const start = new Date(startTime)
    const end = new Date(endTime)
    const diff = end.getTime() - start.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    
    return `${hours}h ${minutes}m`
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Training Runs</h2>
          <p className="text-muted-foreground">
            Train SmolLM2 models on synthetic datasets with LoRA/QLoRA
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Start Training
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {trainingRuns?.map((run) => (
          <Card key={run.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <Brain className="h-5 w-5 text-purple-600" />
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
                    <p className="font-medium truncate">{run.model_name}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Duration:</span>
                    <p className="font-medium">
                      {formatDuration(run.started_at, run.completed_at)}
                    </p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Created:</span>
                    <p>{new Date(run.created_at).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Dataset:</span>
                    <p className="font-medium">Dataset #{run.dataset}</p>
                  </div>
                </div>

                {run.metrics && Object.keys(run.metrics).length > 0 && (
                  <div className="border-t pt-3">
                    <h4 className="text-sm font-medium mb-2">Training Metrics</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {Object.entries(run.metrics).slice(0, 4).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-muted-foreground">{key}:</span>
                          <span className="font-mono">
                            {typeof value === 'number' ? value.toFixed(4) : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex space-x-2 pt-2">
                  {run.status === 'pending' && (
                    <Button 
                      size="sm" 
                      className="flex-1"
                      onClick={() => startTrainingMutation.mutate(run.id)}
                      disabled={startTrainingMutation.isPending}
                    >
                      <Play className="h-4 w-4 mr-1" />
                      {startTrainingMutation.isPending ? 'Starting...' : 'Start'}
                    </Button>
                  )}
                  {run.status === 'running' && (
                    <Button variant="outline" size="sm" className="flex-1">
                      <Pause className="h-4 w-4 mr-1" />
                      Stop
                    </Button>
                  )}
                  {run.status === 'completed' && (
                    <>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1"
                        onClick={() => navigate('/evaluation')}
                      >
                        <BarChart3 className="h-4 w-4 mr-1" />
                        Metrics
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1"
                        onClick={() => navigate('/evaluation')}
                      >
                        Evaluate
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {trainingRuns?.length === 0 && (
          <div className="col-span-full">
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Brain className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No training runs yet</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Start your first SmolLM2 training run on a synthetic dataset.
                </p>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Start Your First Training
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}