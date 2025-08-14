import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Play, Send, Copy, CheckCircle, XCircle, Clock } from 'lucide-react'

export default function Playground() {
  const [inputText, setInputText] = useState('')
  const [selectedModel, setSelectedModel] = useState<number | null>(null)
  const [selectedSpec, setSelectedSpec] = useState<number | null>(null)
  const [history, setHistory] = useState<any[]>([])

  const generateMutation = useMutation({
    mutationFn: (data: { model_id: number; spec_id: number; input_text: string }) =>
      apiClient.generateResponse(data),
    onSuccess: (result) => {
      setHistory(prev => [result, ...prev])
      setInputText('')
    },
  })

  const handleGenerate = () => {
    if (!inputText.trim() || !selectedModel || !selectedSpec) return
    
    generateMutation.mutate({
      model_id: selectedModel,
      spec_id: selectedSpec,
      input_text: inputText,
    })
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Playground</h2>
        <p className="text-muted-foreground">
          Test your trained models with natural language requests
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Play className="h-5 w-5 mr-2" />
                Test Your Model
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Model</label>
                  <select 
                    className="w-full px-3 py-2 border border-border rounded-md"
                    value={selectedModel || ''}
                    onChange={(e) => setSelectedModel(Number(e.target.value))}
                  >
                    <option value="">Select a model...</option>
                    <option value="1">SmolLM2-API-v1</option>
                    <option value="2">SmolLM2-API-v2</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">API Spec</label>
                  <select 
                    className="w-full px-3 py-2 border border-border rounded-md"
                    value={selectedSpec || ''}
                    onChange={(e) => setSelectedSpec(Number(e.target.value))}
                  >
                    <option value="">Select a spec...</option>
                    <option value="1">Petstore API</option>
                    <option value="2">User Management API</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Natural Language Request</label>
                <textarea
                  className="w-full px-3 py-2 border border-border rounded-md"
                  rows={4}
                  placeholder="e.g., Get all users with status active and limit 10"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                />
              </div>

              <Button 
                onClick={handleGenerate}
                disabled={!inputText.trim() || !selectedModel || !selectedSpec || generateMutation.isPending}
                className="w-full"
              >
                {generateMutation.isPending ? (
                  <>
                    <Clock className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Generate API Call
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* History */}
          <Card>
            <CardHeader>
              <CardTitle>Generation History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {history.length > 0 ? (
                  history.map((item, index) => (
                    <div key={index} className="border border-border rounded-lg p-4 space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium mb-1">Input:</p>
                          <p className="text-sm text-muted-foreground bg-muted p-2 rounded">
                            {item.input_text}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                          {item.is_valid_api !== undefined && (
                            <Badge variant={item.is_valid_api ? 'default' : 'destructive'}>
                              {item.is_valid_api ? (
                                <CheckCircle className="h-3 w-3 mr-1" />
                              ) : (
                                <XCircle className="h-3 w-3 mr-1" />
                              )}
                              {item.is_valid_api ? 'Valid' : 'Invalid'}
                            </Badge>
                          )}
                          {item.generation_time_ms && (
                            <span className="text-xs text-muted-foreground">
                              {item.generation_time_ms}ms
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-sm font-medium">Generated API Call:</p>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(item.generated_output)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                        <pre className="text-xs bg-muted p-3 rounded overflow-x-auto">
                          {item.generated_output}
                        </pre>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    No generations yet. Try entering a request above!
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Info Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Tips</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <h4 className="font-medium mb-1">Good Examples:</h4>
                <ul className="text-muted-foreground space-y-1">
                  <li>• "Get user with ID 123"</li>
                  <li>• "Create a new pet with name Fluffy"</li>
                  <li>• "List all orders with status pending"</li>
                  <li>• "Update user 456 with email john@example.com"</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium mb-1">Be Specific:</h4>
                <ul className="text-muted-foreground space-y-1">
                  <li>• Include parameter values</li>
                  <li>• Specify filters and limits</li>
                  <li>• Mention required fields</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Model Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {selectedModel ? (
                <>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Base Model:</span>
                    <span>SmolLM2-1.7B</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Fine-tuned:</span>
                    <span>LoRA</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Training Samples:</span>
                    <span>10,000</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Accuracy:</span>
                    <span>94.2%</span>
                  </div>
                </>
              ) : (
                <p className="text-muted-foreground">Select a model to see details</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}