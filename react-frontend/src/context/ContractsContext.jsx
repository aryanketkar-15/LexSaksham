import React, { createContext, useContext, useState, useEffect } from 'react';

const ContractsContext = createContext();

export const useContracts = () => {
  const context = useContext(ContractsContext);
  if (!context) {
    throw new Error('useContracts must be used within ContractsProvider');
  }
  return context;
};

export const ContractsProvider = ({ children }) => {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load contracts from localStorage on mount
  useEffect(() => {
    const savedContracts = localStorage.getItem('lexsaksham_contracts');
    if (savedContracts) {
      try {
        setContracts(JSON.parse(savedContracts));
      } catch (error) {
        console.error('Failed to load contracts from localStorage:', error);
      }
    }
  }, []);

  // Save contracts to localStorage whenever they change
  useEffect(() => {
    if (contracts.length > 0) {
      localStorage.setItem('lexsaksham_contracts', JSON.stringify(contracts));
    }
  }, [contracts]);

  const addContract = (contractData) => {
    const newContract = {
      id: Date.now().toString(),
      ...contractData,
      uploadedOn: new Date().toISOString(),
      status: 'Analyzed'
    };
    setContracts(prev => [newContract, ...prev]);
    return newContract.id;
  };

  const updateContract = (id, updates) => {
    setContracts(prev => 
      prev.map(contract => 
        contract.id === id ? { ...contract, ...updates } : contract
      )
    );
  };

  const deleteContract = (id) => {
    setContracts(prev => prev.filter(contract => contract.id !== id));
  };

  const getContract = (id) => {
    return contracts.find(contract => contract.id === id);
  };

  // Calculate dashboard stats
  const getStats = () => {
    const totalContracts = contracts.length;
    // Count contracts by risk level (case-insensitive)
    const highRiskContracts = contracts.filter(c => {
      const risk = (c.risk || '').toLowerCase();
      return risk === 'high' || risk === 'critical';
    }).length;
    
    const mediumRiskContracts = contracts.filter(c => {
      const risk = (c.risk || '').toLowerCase();
      return risk === 'medium';
    }).length;
    
    const lowRiskContracts = contracts.filter(c => {
      const risk = (c.risk || '').toLowerCase();
      return risk === 'low';
    }).length;
    
    const clausesFlagged = contracts.reduce((sum, contract) => {
      return sum + (contract.analysis_results?.length || 0);
    }, 0);

    const riskDistribution = contracts.reduce((acc, contract) => {
      const risk = (contract.risk || 'low').toLowerCase();
      acc[risk] = (acc[risk] || 0) + 1;
      return acc;
    }, { low: 0, medium: 0, high: 0, critical: 0 });

    const contractTypes = contracts.reduce((acc, contract) => {
      const type = contract.type || 'Other';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});

    // Calculate compliance score: 
    // - Low risk contracts = 100% compliant
    // - Medium risk contracts = 50% compliant
    // - High/Critical risk contracts = 0% compliant
    let complianceScore = 0;
    if (totalContracts > 0) {
      const lowScore = lowRiskContracts * 100;
      const mediumScore = mediumRiskContracts * 50;
      const highScore = highRiskContracts * 0;
      complianceScore = Math.round((lowScore + mediumScore + highScore) / totalContracts);
    }

    return {
      totalContracts,
      highRiskContracts,
      mediumRiskContracts,
      lowRiskContracts,
      clausesFlagged,
      riskDistribution,
      contractTypes,
      complianceScore
    };
  };

  const value = {
    contracts,
    loading,
    setLoading,
    addContract,
    updateContract,
    deleteContract,
    getContract,
    getStats
  };

  return (
    <ContractsContext.Provider value={value}>
      {children}
    </ContractsContext.Provider>
  );
};

