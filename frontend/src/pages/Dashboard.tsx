import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { 
  FileText, 
  Database, 
  Brain, 
  Target,
  TrendingUp,
  Clock
} from 'lucide-react'

export default function Dashboard() {
  const navigate = useNavigate()
  
  const { data: specs } = useQuery({
    queryKey: ['specs'],
    queryFn: () => apiClient.getSpecs(),
  })

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => apiClient.getDatasets(),
  })

  const { data: trainingRuns } = useQuery({
    queryKey: ['training-runs'],
    queryFn: () => apiClient.getTrainingRuns(),
  })

  const { data: evaluationRuns } = useQuery({
    queryKey: ['evaluation-runs'],
    queryFn: () => apiClient.getEvaluationRuns(),
  })

  const stats = [
    {
      title: 'API Specs',
      value: specs?.length || 0,
      icon: FileText,
      description: 'OpenAPI specifications',
      color: 'text-blue-600',
    },
    {
      title: 'Datasets',
      value: datasets?.length || 0,
      icon: Database,
      description: 'Synthetic datasets',
      color: 'text-green-600',
    },
    {
      title: 'Training Runs',
      value: trainingRuns?.length || 0,
      icon: Brain,
      description: 'Model training sessions',
      color: 'text-purple-600',
    },
    {
      title: 'Evaluations',
      value: evaluationRuns?.length || 0,
      icon: Target,
      description: 'Model evaluations',
      color: 'text-orange-600',
    },
  ]

  const recentActivity = [
    ...(trainingRuns?.slice(0, 3).map(run => ({
      type: 'training',
      title: run.name,
      status: run.status,
      time: run.created_at,
    })) || []),
    ...(evaluationRuns?.slice(0, 3).map(run => ({
      type: 'evaluation',
      title: run.name,
      status: run.status,
      time: run.created_at,
    })) || []),
  ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime()).slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="h-5 w-5 mr-2" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.length > 0 ? (
                recentActivity.map((activity, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {activity.type === 'training' ? (
                        <Brain className="h-4 w-4 text-purple-600" />
                      ) : (
                        <Target className="h-4 w-4 text-orange-600" />
                      )}
                      <div>
                        <p className="text-sm font-medium">{activity.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {activity.type === 'training' ? 'Training Run' : 'Evaluation'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge 
                        variant={
                          activity.status === 'completed' ? 'default' :
                          activity.status === 'running' ? 'secondary' :
                          activity.status === 'failed' ? 'destructive' : 'outline'
                        }
                      >
                        {activity.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {new Date(activity.time).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No recent activity</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <button 
                onClick={() => navigate('/specs')}
                className="w-full text-left p-3 rounded-lg border border-border hover:bg-accent transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="font-medium">Upload API Spec</p>
                    <p className="text-sm text-muted-foreground">Add a new OpenAPI specification</p>
                  </div>
                </div>
              </button>
              
              <button 
                onClick={() => navigate('/datasets')}
                className="w-full text-left p-3 rounded-lg border border-border hover:bg-accent transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <Database className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="font-medium">Generate Dataset</p>
                    <p className="text-sm text-muted-foreground">Create synthetic training data</p>
                  </div>
                </div>
              </button>
              
              <button 
                onClick={() => navigate('/training')}
                className="w-full text-left p-3 rounded-lg border border-border hover:bg-accent transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <Brain className="h-5 w-5 text-purple-600" />
                  <div>
                    <p className="font-medium">Start Training</p>
                    <p className="text-sm text-muted-foreground">Train a new SmolLM2 model</p>
                  </div>
                </div>
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}