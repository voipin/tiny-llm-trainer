import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Database, Plus, Play, Download } from 'lucide-react'

export default function Datasets() {
  const [showTrainingDialog, setShowTrainingDialog] = useState(false)
  const [selectedDataset, setSelectedDataset] = useState<any>(null)
  const [trainingForm, setTrainingForm] = useState({
    name: '',
    config: {}
  })
  const queryClient = useQueryClient()

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => apiClient.getDatasets(),
  })

  const downloadMutation = useMutation({
    mutationFn: (datasetId: number) => apiClient.downloadDataset(datasetId),
    onSuccess: () => {
      // Download success is handled by the API method
    },
    onError: (error) => {
      console.error('Download failed:', error)
      alert('Download failed. Please try again.')
    }
  })

  const createTrainingMutation = useMutation({
    mutationFn: ({ datasetId, data }: { datasetId: number; data: { name: string; config?: any } }) =>
      apiClient.createTrainingRunFromDataset(datasetId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training-runs'] })
      setShowTrainingDialog(false)
      setTrainingForm({ name: '', config: {} })
      alert('Training run created! Check the Training page to start it.')
    },
    onError: (error) => {
      console.error('Training creation failed:', error)
      alert('Failed to create training run. Please try again.')
    }
  })

  const handleDownload = async (dataset: any) => {
    try {
      await downloadMutation.mutateAsync(dataset.id)
    } catch (error) {
      // Error handling is done in the mutation
    }
  }

  const handleStartTraining = (dataset: any) => {
    setSelectedDataset(dataset)
    setTrainingForm({
      name: `${dataset.name} Training`,
      config: {}
    })
    setShowTrainingDialog(true)
  }

  const handleTrainingSubmit = async () => {
    if (!selectedDataset || !trainingForm.name.trim()) {
      alert('Please provide a training run name')
      return
    }

    try {
      await createTrainingMutation.mutateAsync({
        datasetId: selectedDataset.id,
        data: trainingForm
      })
    } catch (error) {
      // Error handling is done in the mutation
    }
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'default'
      case 'generating': return 'secondary'
      case 'failed': return 'destructive'
      default: return 'outline'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Synthetic Datasets</h2>
          <p className="text-muted-foreground">
            Generate and manage training datasets from API specifications
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Generate Dataset
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {datasets?.map((dataset) => (
          <Card key={dataset.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <Database className="h-5 w-5 text-green-600" />
                  <CardTitle className="text-lg">{dataset.name}</CardTitle>
                </div>
                <Badge variant={getStatusColor(dataset.status)}>
                  {dataset.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Samples:</span>
                  <span className="font-medium">{dataset.num_samples.toLocaleString()}</span>
                </div>
                
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Created:</span>
                  <span>{new Date(dataset.created_at).toLocaleDateString()}</span>
                </div>

                <div className="flex space-x-2 pt-2">
                  {dataset.status === 'completed' && (
                    <>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1"
                        onClick={() => handleDownload(dataset)}
                        disabled={downloadMutation.isPending}
                      >
                        <Download className="h-4 w-4 mr-1" />
                        {downloadMutation.isPending ? 'Downloading...' : 'Download'}
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1"
                        onClick={() => handleStartTraining(dataset)}
                      >
                        <Play className="h-4 w-4 mr-1" />
                        Train
                      </Button>
                    </>
                  )}
                  {dataset.status === 'pending' && (
                    <Button size="sm" className="w-full">
                      <Play className="h-4 w-4 mr-1" />
                      Start Generation
                    </Button>
                  )}
                  {dataset.status === 'generating' && (
                    <Button variant="outline" size="sm" className="w-full" disabled>
                      Generating...
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {datasets?.length === 0 && (
          <div className="col-span-full">
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Database className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No datasets yet</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Generate your first synthetic dataset from an API specification.
                </p>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Generate Your First Dataset
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Training Creation Dialog */}
      {showTrainingDialog && selectedDataset && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Create Training Run</CardTitle>
              <p className="text-sm text-muted-foreground">
                Start training a model with "{selectedDataset.name}"
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Training Run Name</label>
                  <input
                    type="text"
                    value={trainingForm.name}
                    onChange={(e) => setTrainingForm(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-border rounded-md"
                    placeholder="Pet Compliment Model Training"
                  />
                </div>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    className="flex-1"
                    onClick={() => {
                      setShowTrainingDialog(false)
                      setSelectedDataset(null)
                      setTrainingForm({ name: '', config: {} })
                    }}
                  >
                    Cancel
                  </Button>
                  <Button 
                    className="flex-1" 
                    onClick={handleTrainingSubmit}
                    disabled={createTrainingMutation.isPending}
                  >
                    {createTrainingMutation.isPending ? 'Creating...' : 'Create Training Run'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}