import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Plus, FileText, Calendar, Hash } from 'lucide-react'

export default function Specs() {
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [showDatasetDialog, setShowDatasetDialog] = useState(false)
  const [showDetailsDialog, setShowDetailsDialog] = useState(false)
  const [selectedSpec, setSelectedSpec] = useState<any>(null)
  const [datasetForm, setDatasetForm] = useState({
    name: '',
    num_samples: 1000
  })
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    spec_content: ''
  })
  const queryClient = useQueryClient()

  const { data: specs, isLoading } = useQuery({
    queryKey: ['specs'],
    queryFn: () => apiClient.getSpecs(),
  })

  const uploadMutation = useMutation({
    mutationFn: (data: { name: string; description: string; spec_content: any }) =>
      apiClient.createSpec(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['specs'] })
      setShowUploadDialog(false)
      setFormData({ name: '', description: '', spec_content: '' })
    },
  })

  const generateDatasetMutation = useMutation({
    mutationFn: ({ specId, data }: { specId: number; data: { name: string; num_samples: number } }) =>
      apiClient.generateDatasetFromSpec(specId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      setShowDatasetDialog(false)
      setDatasetForm({ name: '', num_samples: 1000 })
      alert('Dataset generation started! Check the Datasets page for progress.')
    },
  })

  const handleUpload = async () => {
    if (!formData.name.trim() || !formData.spec_content.trim()) {
      alert('Please provide a name and spec content')
      return
    }

    try {
      // Try to parse the spec content as JSON or YAML
      let parsedSpec
      try {
        parsedSpec = JSON.parse(formData.spec_content)
      } catch {
        // If JSON parsing fails, assume it's YAML and send as string
        // The backend should handle YAML parsing
        parsedSpec = formData.spec_content
      }

      await uploadMutation.mutateAsync({
        name: formData.name,
        description: formData.description,
        spec_content: parsedSpec
      })
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed. Please check your specification format.')
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string
        setFormData(prev => ({
          ...prev,
          spec_content: content,
          name: prev.name || file.name.replace(/\.(yaml|yml|json)$/, '')
        }))
      }
      reader.readAsText(file)
    }
  }

  const handleViewDetails = (spec: any) => {
    setSelectedSpec(spec)
    setShowDetailsDialog(true)
  }

  const handleGenerateDataset = (spec: any) => {
    console.log('handleGenerateDataset called with spec:', spec)
    setSelectedSpec(spec)
    setDatasetForm({
      name: `${spec.name} Dataset`,
      num_samples: 1000
    })
    setShowDatasetDialog(true)
    console.log('Dialog should be showing now, showDatasetDialog:', true)
  }

  const handleDatasetSubmit = async () => {
    if (!selectedSpec || !datasetForm.name.trim()) {
      alert('Please provide a dataset name')
      return
    }

    try {
      await generateDatasetMutation.mutateAsync({
        specId: selectedSpec.id,
        data: datasetForm
      })
    } catch (error) {
      console.error('Dataset generation failed:', error)
      alert('Dataset generation failed. Please try again.')
    }
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">API Specifications</h2>
          <p className="text-muted-foreground">
            Manage OpenAPI specifications for training data generation
          </p>
        </div>
        <Button onClick={() => setShowUploadDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Upload Spec
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {console.log('Rendering specs:', specs)}
        {specs?.map((spec) => (
          <Card key={spec.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  <CardTitle className="text-lg">{spec.name}</CardTitle>
                </div>
                <Badge variant={spec.is_active ? 'default' : 'secondary'}>
                  {spec.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {spec.description || 'No description provided'}
                </p>
                
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-1">
                    <Hash className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">
                      {spec.endpoint_count} endpoints
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">
                      {new Date(spec.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="flex space-x-2 pt-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => handleViewDetails(spec)}
                  >
                    View Details
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => {
                      console.log('Generate Data button clicked! Spec:', spec)
                      handleGenerateDataset(spec)
                    }}
                  >
                    Generate Data
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {specs?.length === 0 && (
          <div className="col-span-full">
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No API specs yet</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Upload your first OpenAPI specification to get started with training data generation.
                </p>
                <Button onClick={() => {
                  console.log('Upload Your First Spec button clicked')
                  setShowUploadDialog(true)
                }}>
                  <Plus className="h-4 w-4 mr-2" />
                  Upload Your First Spec
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Upload Dialog would go here */}
      {showUploadDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Upload API Specification</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-border rounded-md"
                    placeholder="Pet Compliment API"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-border rounded-md"
                    rows={3}
                    placeholder="A silly API for giving compliments to pets"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Upload File</label>
                  <input
                    type="file"
                    accept=".json,.yaml,.yml"
                    onChange={handleFileUpload}
                    className="w-full px-3 py-2 border border-border rounded-md"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Upload a JSON or YAML file, or paste content below
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">OpenAPI JSON/YAML</label>
                  <textarea
                    value={formData.spec_content}
                    onChange={(e) => setFormData(prev => ({ ...prev, spec_content: e.target.value }))}
                    className="w-full px-3 py-2 border border-border rounded-md font-mono text-sm"
                    rows={8}
                    placeholder="Paste your OpenAPI specification here..."
                  />
                </div>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    className="flex-1"
                    onClick={() => {
                      setShowUploadDialog(false)
                      setFormData({ name: '', description: '', spec_content: '' })
                    }}
                  >
                    Cancel
                  </Button>
                  <Button 
                    className="flex-1" 
                    onClick={handleUpload}
                    disabled={uploadMutation.isPending}
                  >
                    {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Dataset Generation Dialog */}
      {showDatasetDialog && selectedSpec && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Generate Dataset</CardTitle>
              <p className="text-sm text-muted-foreground">
                Create synthetic training data from "{selectedSpec.name}"
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Dataset Name</label>
                  <input
                    type="text"
                    value={datasetForm.name}
                    onChange={(e) => setDatasetForm(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-border rounded-md"
                    placeholder="Pet Compliment Dataset"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Number of Samples</label>
                  <input
                    type="number"
                    value={datasetForm.num_samples}
                    onChange={(e) => setDatasetForm(prev => ({ ...prev, num_samples: parseInt(e.target.value) || 1000 }))}
                    className="w-full px-3 py-2 border border-border rounded-md"
                    min="10"
                    max="10000"
                    step="10"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Recommended: 1000-5000 samples for good training results
                  </p>
                </div>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    className="flex-1"
                    onClick={() => {
                      setShowDatasetDialog(false)
                      setSelectedSpec(null)
                      setDatasetForm({ name: '', num_samples: 1000 })
                    }}
                  >
                    Cancel
                  </Button>
                  <Button 
                    className="flex-1" 
                    onClick={handleDatasetSubmit}
                    disabled={generateDatasetMutation.isPending}
                  >
                    {generateDatasetMutation.isPending ? 'Generating...' : 'Generate'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Details Dialog */}
      {showDetailsDialog && selectedSpec && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-xl">{selectedSpec.name}</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedSpec.description || 'No description provided'}
                  </p>
                </div>
                <Badge variant={selectedSpec.is_active ? 'default' : 'secondary'}>
                  {selectedSpec.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="overflow-auto">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Endpoints:</span> {selectedSpec.endpoint_count}
                  </div>
                  <div>
                    <span className="font-medium">Version:</span> {selectedSpec.version || 'N/A'}
                  </div>
                  <div>
                    <span className="font-medium">Created:</span> {new Date(selectedSpec.created_at).toLocaleString()}
                  </div>
                  <div>
                    <span className="font-medium">ID:</span> {selectedSpec.id}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">OpenAPI Specification</h4>
                  <div className="bg-muted p-4 rounded-md overflow-auto max-h-96">
                    <pre className="text-xs whitespace-pre-wrap font-mono">
                      {typeof selectedSpec.spec_content === 'string' 
                        ? selectedSpec.spec_content 
                        : JSON.stringify(selectedSpec.spec_content, null, 2)}
                    </pre>
                  </div>
                </div>
                
                <div className="flex space-x-2 pt-4">
                  <Button 
                    variant="outline" 
                    className="flex-1"
                    onClick={() => {
                      setShowDetailsDialog(false)
                      setSelectedSpec(null)
                    }}
                  >
                    Close
                  </Button>
                  <Button 
                    className="flex-1"
                    onClick={() => {
                      setShowDetailsDialog(false)
                      handleGenerateDataset(selectedSpec)
                    }}
                  >
                    Generate Dataset
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