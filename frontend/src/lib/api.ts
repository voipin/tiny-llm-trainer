const API_BASE_URL = 'http://localhost:8000/api'

export interface OpenAPISpec {
  id: number
  name: string
  description: string
  version: string
  endpoint_count: number
  created_at: string
  is_active: boolean
}

export interface SyntheticDataset {
  id: number
  name: string
  spec: number
  num_samples: number
  status: 'pending' | 'generating' | 'completed' | 'failed'
  created_at: string
}

export interface TrainingRun {
  id: number
  name: string
  dataset: number
  model_name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  started_at?: string
  completed_at?: string
  metrics: Record<string, any>
}

export interface EvaluationRun {
  id: number
  name: string
  model: number
  test_dataset: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  results: Record<string, any>
}

export interface PlaygroundQuery {
  id: number
  input_text: string
  generated_output: string
  is_valid_api?: boolean
  generation_time_ms?: number
  created_at: string
}

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
}

export interface TrainedModel {
  id: number
  name: string
  training_run: number
  model_path: string
  base_model: string
  adapter_path: string
  model_size_mb: number
  created_at: string
  is_active: boolean
}

class ApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      credentials: 'include',
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`)
    }

    return response.json()
  }

  // OpenAPI Specs
  async getSpecs(): Promise<OpenAPISpec[]> {
    const response = await this.request<{results: OpenAPISpec[]}>('/specs/')
    return response.results
  }

  async createSpec(data: { name: string; description: string; spec_content: any }): Promise<OpenAPISpec> {
    return this.request('/specs/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getSpec(id: number): Promise<OpenAPISpec> {
    return this.request(`/specs/${id}/`)
  }

  async generateDatasetFromSpec(specId: number, data: { name: string; num_samples: number }): Promise<any> {
    return this.request(`/specs/${specId}/generate_dataset/`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Synthetic Datasets
  async getDatasets(): Promise<SyntheticDataset[]> {
    const response = await this.request<{results: SyntheticDataset[]}>('/datasets/')
    return response.results
  }

  async createDataset(data: { 
    name: string
    spec: number
    num_samples: number
    generation_config?: any 
  }): Promise<SyntheticDataset> {
    return this.request('/datasets/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async downloadDataset(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/datasets/${id}/download/`, {
      method: 'GET',
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Download failed')
    }

    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get('Content-Disposition')
    const filename = contentDisposition?.match(/filename="(.+)"/)?.[1] || `dataset-${id}.json`

    // Create blob and download
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  async createTrainingRunFromDataset(datasetId: number, data: { 
    name: string
    config?: any 
  }): Promise<TrainingRun> {
    return this.request(`/datasets/${datasetId}/create_training_run/`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async generateDataset(id: number): Promise<void> {
    return this.request(`/datasets/${id}/generate/`, {
      method: 'POST',
    })
  }

  // Training Runs
  async getTrainingRuns(): Promise<TrainingRun[]> {
    const response = await this.request<{results: TrainingRun[]}>('/training-runs/')
    return response.results
  }

  async createTrainingRun(data: {
    name: string
    dataset: number
    model_name?: string
    training_config?: any
  }): Promise<TrainingRun> {
    return this.request('/training-runs/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async startTraining(id: number): Promise<void> {
    return this.request(`/training-runs/${id}/start/`, {
      method: 'POST',
    })
  }

  async getTrainingRun(id: number): Promise<TrainingRun> {
    return this.request(`/training-runs/${id}/`)
  }

  // Trained Models
  async getTrainedModels(): Promise<TrainedModel[]> {
    const response = await this.request<{results: TrainedModel[]}>('/models/')
    return response.results
  }

  async getTrainedModel(id: number): Promise<TrainedModel> {
    return this.request(`/models/${id}/`)
  }

  // Evaluation Runs
  async getEvaluationRuns(): Promise<EvaluationRun[]> {
    const response = await this.request<{results: EvaluationRun[]}>('/evaluation-runs/')
    return response.results
  }

  async createEvaluationRun(data: {
    name: string
    model: number
    test_dataset: number
    evaluation_config?: any
  }): Promise<EvaluationRun> {
    return this.request('/evaluation-runs/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async startEvaluation(id: number): Promise<void> {
    return this.request(`/evaluation-runs/${id}/start/`, {
      method: 'POST',
    })
  }

  // Playground
  async generateResponse(data: {
    model_id: number
    spec_id: number
    input_text: string
  }): Promise<PlaygroundQuery> {
    return this.request('/playground/generate/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getPlaygroundHistory(sessionId: number): Promise<PlaygroundQuery[]> {
    return this.request(`/playground/sessions/${sessionId}/queries/`)
  }

  // Authentication
  async login(email: string, password: string): Promise<{ detail: string; user: User }> {
    return this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async logout(): Promise<{ detail: string }> {
    return this.request('/auth/logout/', {
      method: 'POST',
    })
  }

  async getCurrentUser(): Promise<User> {
    return this.request('/auth/user/')
  }
}

export const apiClient = new ApiClient()