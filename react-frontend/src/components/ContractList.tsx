import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { useContracts } from '../context/ContractsContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from './ui/sheet';
import { Checkbox } from './ui/checkbox';
import { 
  Search, 
  Filter, 
  LayoutGrid, 
  List, 
  Download, 
  Eye, 
  AlertTriangle,
  Calendar,
  FileText,
  Building,
  User,
  Trash2
} from 'lucide-react';

// Contracts will be loaded from ContractsContext

const getRiskColor = (risk) => {
  switch (risk) {
    case 'low': return 'bg-green-100 text-green-800 border-green-200';
    case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'critical': return 'bg-red-100 text-red-800 border-red-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const getStatusColor = (status) => {
  switch (status) {
    case 'Active': return 'bg-green-100 text-green-800 border-green-200';
    case 'Approved': return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'Under Review': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'Needs Attention': return 'bg-red-100 text-red-800 border-red-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

export default function ContractList() {
  const { contracts, deleteContract } = useContracts();
  const [viewMode, setViewMode] = useState('table');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [selectedRisk, setSelectedRisk] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedContracts, setSelectedContracts] = useState([]);

  // Transform contracts for display
  const displayContracts = contracts.map(contract => ({
    id: contract.id,
    name: contract.name || 'Untitled Contract',
    type: contract.type || contract.analysis_results?.[0]?.label || 'Unknown',
    risk: contract.risk?.toLowerCase() || 'low',
    uploadedOn: contract.uploadedOn || contract.uploadedAt,
    status: contract.status || 'Analyzed',
    parties: contract.parties || [],
    expiryDate: contract.expiryDate || '',
    value: contract.value || 'N/A',
    clauses: contract.analysis_results?.length || 0
  }));

  const filteredContracts = displayContracts.filter(contract => {
    const matchesSearch = contract.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         contract.parties.some(party => party.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = selectedType === 'all' || contract.type === selectedType;
    const matchesRisk = selectedRisk === 'all' || contract.risk === selectedRisk;
    const matchesStatus = selectedStatus === 'all' || contract.status === selectedStatus;
    
    return matchesSearch && matchesType && matchesRisk && matchesStatus;
  });

  const handleSelectContract = (contractId) => {
    setSelectedContracts(prev => 
      prev.includes(contractId) 
        ? prev.filter(id => id !== contractId)
        : [...prev, contractId]
    );
  };

  const handleSelectAll = () => {
    setSelectedContracts(
      selectedContracts.length === filteredContracts.length 
        ? [] 
        : filteredContracts.map(c => c.id)
    );
  };

  const ContractCard = ({ contract }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <CardTitle className="text-base">{contract.name}</CardTitle>
              <CardDescription className="flex items-center space-x-2">
                <FileText className="h-3 w-3" />
                <span>{contract.type}</span>
              </CardDescription>
            </div>
            <div className="flex space-x-2">
              <Badge className={getRiskColor(contract.risk)}>
                {contract.risk}
              </Badge>
              <Badge className={getStatusColor(contract.status)}>
                {contract.status}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="space-y-2 text-sm text-muted-foreground">
            <div className="flex items-center space-x-2">
              <Building className="h-3 w-3" />
              <span>{contract.parties.join(', ')}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Calendar className="h-3 w-3" />
                <span>Uploaded: {new Date(contract.uploadedOn).toLocaleDateString()}</span>
              </div>
              <span className="font-medium">{contract.value}</span>
            </div>
          </div>
          <div className="flex space-x-2 mt-4">
            <Button asChild size="sm" variant="outline">
              <Link to={`/contracts/${contract.id}`}>
                <Eye className="h-3 w-3 mr-1" />
                View
              </Link>
            </Button>
            <Button size="sm" variant="ghost">
              <Download className="h-3 w-3 mr-1" />
              Download
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1>Contracts</h1>
          <p className="text-muted-foreground">
            Manage and review all your contracts in one place
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export All
          </Button>
          <Button asChild>
            <Link to="/upload">Upload Contract</Link>
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search contracts, parties, or content..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Filters */}
            <div className="flex gap-2">
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="Employment">Employment</SelectItem>
                  <SelectItem value="Vendor">Vendor</SelectItem>
                  <SelectItem value="NDA">NDA</SelectItem>
                  <SelectItem value="Service">Service</SelectItem>
                  <SelectItem value="Partnership">Partnership</SelectItem>
                  <SelectItem value="Lease">Lease</SelectItem>
                </SelectContent>
              </Select>

              <Select value={selectedRisk} onValueChange={setSelectedRisk}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Risk" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Risk</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>

              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Active">Active</SelectItem>
                  <SelectItem value="Approved">Approved</SelectItem>
                  <SelectItem value="Under Review">Under Review</SelectItem>
                  <SelectItem value="Needs Attention">Needs Attention</SelectItem>
                </SelectContent>
              </Select>

              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    More Filters
                  </Button>
                </SheetTrigger>
                <SheetContent>
                  <SheetHeader>
                    <SheetTitle>Advanced Filters</SheetTitle>
                    <SheetDescription>
                      Apply additional filters to refine your contract search
                    </SheetDescription>
                  </SheetHeader>
                  <div className="mt-6 space-y-4">
                    <div>
                      <label className="text-sm font-medium">Date Range</label>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <Input type="date" placeholder="From" />
                        <Input type="date" placeholder="To" />
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Contract Value</label>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <Input placeholder="Min amount" />
                        <Input placeholder="Max amount" />
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Parties</label>
                      <Input placeholder="Filter by organization" className="mt-2" />
                    </div>
                  </div>
                </SheetContent>
              </Sheet>
            </div>

            {/* View Toggle */}
            <div className="flex items-center border rounded-lg p-1">
              <Button
                variant={viewMode === 'table' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('table')}
                className="px-3"
              >
                <List className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'grid' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('grid')}
                className="px-3"
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Summary */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>Showing {filteredContracts.length} of {contracts.length} contracts</span>
        {selectedContracts.length > 0 && (
          <span>{selectedContracts.length} contracts selected</span>
        )}
      </div>

      {/* Content */}
      {viewMode === 'table' ? (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedContracts.length === filteredContracts.length}
                    onCheckedChange={handleSelectAll}
                  />
                </TableHead>
                <TableHead>Contract Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Risk Level</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Uploaded On</TableHead>
                <TableHead>Clauses</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredContracts.map((contract) => (
                <TableRow key={contract.id} className="hover:bg-muted/50">
                  <TableCell>
                    <Checkbox
                      checked={selectedContracts.includes(contract.id)}
                      onCheckedChange={() => handleSelectContract(contract.id)}
                    />
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{contract.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {contract.parties.join(', ')}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{contract.type}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={getRiskColor(contract.risk)}>
                      {contract.risk}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(contract.status)}>
                      {contract.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {contract.uploadedOn 
                      ? new Date(contract.uploadedOn).toLocaleDateString() 
                      : 'N/A'}
                  </TableCell>
                  <TableCell>{contract.clauses || 0}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      <Button asChild size="sm" variant="outline">
                        <Link to={`/contracts/${contract.id}`}>
                          <Eye className="h-3 w-3" />
                        </Link>
                      </Button>
                      <Button 
                        size="sm" 
                        variant="ghost"
                        onClick={() => {
                          if (confirm('Delete this contract?')) {
                            deleteContract(contract.id);
                          }
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredContracts.map((contract) => (
            <ContractCard key={contract.id} contract={contract} />
          ))}
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-center space-x-2">
        <Button variant="outline" size="sm" disabled>
          Previous
        </Button>
        <div className="flex space-x-1">
          <Button variant="default" size="sm">1</Button>
          <Button variant="outline" size="sm">2</Button>
          <Button variant="outline" size="sm">3</Button>
        </div>
        <Button variant="outline" size="sm">
          Next
        </Button>
      </div>
    </div>
  );
}

