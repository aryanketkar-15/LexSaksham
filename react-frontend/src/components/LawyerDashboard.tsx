import React from 'react';
import { motion } from 'motion/react';
import { useContracts } from '../context/ContractsContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line
} from 'recharts';
import { 
  FileText, 
  AlertTriangle, 
  TrendingUp, 
  Clock, 
  Shield, 
  Users,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Upload,
  MessageSquare,
  Scale,
  BookOpen
} from 'lucide-react';

const getRiskColor = (risk) => {
  switch (risk) {
    case 'low': return 'bg-green-500';
    case 'medium': return 'bg-yellow-500';
    case 'high': return 'bg-orange-500';
    case 'critical': return 'bg-red-500';
    default: return 'bg-gray-500';
  }
};

export default function LawyerDashboard() {
  const { contracts, getStats } = useContracts();
  const navigate = useNavigate();
  const stats = getStats();

  const contractsByType = Object.entries(stats.contractTypes).map(([name, value], index) => {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    return { name, value, color: colors[index % colors.length] };
  });

  const riskTrends = [
    { month: 'Current', 
      high: stats.riskDistribution.high || 0, 
      medium: stats.riskDistribution.medium || 0, 
      low: stats.riskDistribution.low || 0 
    }
  ];

  const recentActivity = contracts.slice(0, 4).map((contract, index) => ({
    id: contract.id,
    action: 'Contract analyzed',
    contract: contract.name || 'Untitled',
    time: contract.uploadedOn 
      ? new Date(contract.uploadedOn).toLocaleDateString() 
      : 'Recently',
    risk: contract.risk?.toLowerCase() || 'low'
  }));

  const activityData = [
    { time: '9:00', uploads: contracts.length > 0 ? Math.min(contracts.length, 5) : 0, reviews: contracts.length > 0 ? Math.min(contracts.length, 8) : 0 },
    { time: '12:00', uploads: contracts.length > 1 ? Math.min(contracts.length, 12) : 0, reviews: contracts.length > 1 ? Math.min(contracts.length, 15) : 0 },
    { time: '15:00', uploads: contracts.length > 2 ? Math.min(contracts.length, 8) : 0, reviews: contracts.length > 2 ? Math.min(contracts.length, 12) : 0 },
    { time: '18:00', uploads: contracts.length > 3 ? Math.min(contracts.length, 6) : 0, reviews: contracts.length > 3 ? Math.min(contracts.length, 9) : 0 }
  ];

  const totalContracts = stats.totalContracts;
  const highRiskContracts = stats.highRiskContracts;
  const clausesFlagged = stats.clausesFlagged;
  // Use compliance score from stats (calculated in ContractsContext)
  const complianceScore = stats.complianceScore ?? (totalContracts > 0 ? 0 : 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1>Lawyer Dashboard</h1>
          <p className="text-muted-foreground">
            Professional legal research and contract analysis with Supreme Court judgment assistance
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button onClick={() => navigate('/legal-research')} variant="outline">
            <Scale className="h-4 w-4 mr-2" />
            Legal Research
          </Button>
          <Button onClick={() => navigate('/upload')}>
            <Upload className="h-4 w-4 mr-2" />
            Upload Contract
          </Button>
          <Button variant="outline" onClick={() => navigate('/chat')}>
            <MessageSquare className="h-4 w-4 mr-2" />
            Legal AI Assistant
          </Button>
        </div>
      </div>

      {/* Quick Access Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="cursor-pointer hover:bg-muted/50 transition-colors" onClick={() => navigate('/legal-research')}>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Scale className="h-5 w-5 text-primary" />
              <span>Supreme Court Judgments</span>
            </CardTitle>
            <CardDescription>
              Search and analyze relevant case law
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <p className="text-2xl font-bold">Available</p>
              <ArrowUpRight className="h-5 w-5 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-muted/50 transition-colors" onClick={() => navigate('/chat')}>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BookOpen className="h-5 w-5 text-primary" />
              <span>Legal AI Assistant</span>
            </CardTitle>
            <CardDescription>
              Get legal research help and case law insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <p className="text-2xl font-bold">Ready</p>
              <ArrowUpRight className="h-5 w-5 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-muted/50 transition-colors" onClick={() => navigate('/contracts')}>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-primary" />
              <span>Contract Analysis</span>
            </CardTitle>
            <CardDescription>
              Review contracts with judgment references
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <p className="text-2xl font-bold">{totalContracts}</p>
              <ArrowUpRight className="h-5 w-5 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Contracts</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalContracts}</div>
            <p className="text-xs text-muted-foreground">
              {totalContracts === 0 ? 'No contracts yet' : `${totalContracts} document${totalContracts > 1 ? 's' : ''} analyzed`}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Risk Contracts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{highRiskContracts}</div>
            <p className="text-xs text-muted-foreground">
              Requires immediate attention
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Clauses Flagged</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{clausesFlagged}</div>
            <p className="text-xs text-muted-foreground">
              Clauses requiring review
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{complianceScore}%</div>
            <Progress value={complianceScore} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Contract Activity</CardTitle>
            <CardDescription>Uploads and reviews over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="uploads" stroke="#3b82f6" name="Uploads" />
                <Line type="monotone" dataKey="reviews" stroke="#10b981" name="Reviews" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
            <CardDescription>Current risk levels</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Low', value: stats.riskDistribution.low || 0 },
                    { name: 'Medium', value: stats.riskDistribution.medium || 0 },
                    { name: 'High', value: stats.riskDistribution.high || 0 },
                    { name: 'Critical', value: stats.riskDistribution.critical || 0 }
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {['#10b981', '#f59e0b', '#ef4444', '#dc2626'].map((color, index) => (
                    <Cell key={`cell-${index}`} fill={color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest contract analyses with judgment references</CardDescription>
        </CardHeader>
        <CardContent>
          {recentActivity.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No contracts uploaded yet</p>
              <Button onClick={() => navigate('/upload')} className="mt-4">
                Upload Your First Contract
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <motion.div
                  key={activity.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 cursor-pointer"
                  onClick={() => navigate(`/contracts/${activity.id}`)}
                >
                  <div className="flex items-center space-x-4">
                    <div className={`p-2 rounded ${getRiskColor(activity.risk)}/10`}>
                      <FileText className={`h-5 w-5 ${getRiskColor(activity.risk)}`} />
                    </div>
                    <div>
                      <p className="font-medium">{activity.contract}</p>
                      <p className="text-sm text-muted-foreground">{activity.action}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Badge className={getRiskColor(activity.risk)}>
                      {activity.risk} risk
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      <Scale className="h-3 w-3 mr-1" />
                      Judgments Available
                    </Badge>
                    <span className="text-sm text-muted-foreground flex items-center">
                      <Clock className="h-4 w-4 mr-1" />
                      {activity.time}
                    </span>
                    <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

