import React, { createContext, useContext, useState, useEffect } from 'react';
import { useContracts } from './ContractsContext';

const NotificationsContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationsContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationsProvider');
  }
  return context;
};

export const NotificationsProvider = ({ children }) => {
  const { contracts } = useContracts();
  const [notifications, setNotifications] = useState([]);

  // Load notifications from localStorage on mount
  useEffect(() => {
    const savedNotifications = localStorage.getItem('lexsaksham_notifications');
    if (savedNotifications) {
      try {
        setNotifications(JSON.parse(savedNotifications));
      } catch (error) {
        console.error('Failed to load notifications from localStorage:', error);
      }
    }
  }, []);

  // Save notifications to localStorage whenever they change
  useEffect(() => {
    if (notifications.length > 0) {
      localStorage.setItem('lexsaksham_notifications', JSON.stringify(notifications));
    }
  }, [notifications]);

  // Generate notifications from contract activities
  useEffect(() => {
    if (contracts.length === 0) return;

    setNotifications(prev => {
      const existingNotificationIds = new Set(prev.map(n => n.contractId));
      const newNotifications = [];

      contracts.forEach(contract => {
        // Skip if notification already exists for this contract
        if (existingNotificationIds.has(contract.id)) return;

      const uploadedDate = new Date(contract.uploadedOn || contract.uploadedAt);
      const timeAgo = getTimeAgo(uploadedDate);

      // Notification for contract upload/analysis
      if (contract.analysis_results && contract.analysis_results.length > 0) {
        const highRiskClauses = contract.analysis_results.filter(
          r => r.risk_level?.toLowerCase() === 'high' || r.risk_level?.toLowerCase() === 'critical'
        );

        if (highRiskClauses.length > 0) {
          // High risk contract notification
          newNotifications.push({
            id: `risk-${contract.id}`,
            contractId: contract.id,
            type: 'alert',
            title: 'High Risk Contract Detected',
            message: `${contract.name || 'Contract'} contains ${highRiskClauses.length} high-risk clause${highRiskClauses.length > 1 ? 's' : ''} requiring immediate attention.`,
            timestamp: timeAgo,
            read: false,
            priority: 'high',
            category: 'risk',
            actionRequired: true,
            actions: ['Review Contract', 'View Details'],
            contractName: contract.name
          });
        } else {
          // Analysis complete notification
          newNotifications.push({
            id: `analysis-${contract.id}`,
            contractId: contract.id,
            type: 'success',
            title: 'Contract Analysis Complete',
            message: `${contract.name || 'Contract'} has been successfully analyzed. ${contract.analysis_results.length} clause${contract.analysis_results.length > 1 ? 's' : ''} extracted.`,
            timestamp: timeAgo,
            read: false,
            priority: 'medium',
            category: 'analysis',
            actionRequired: false,
            actions: ['View Results', 'View Contract'],
            contractName: contract.name
          });
        }
      } else if (contract.name) {
        // Upload successful notification
        newNotifications.push({
          id: `upload-${contract.id}`,
          contractId: contract.id,
          type: 'success',
          title: 'Upload Successful',
          message: `${contract.name} has been uploaded successfully.`,
          timestamp: timeAgo,
          read: false,
          priority: 'low',
          category: 'upload',
          actionRequired: false,
          actions: ['View Contract'],
          contractName: contract.name
        });
      }
      });

      // Add new notifications if any
      if (newNotifications.length > 0) {
        // Filter out duplicates and add new ones
        const existingIds = new Set(prev.map(n => n.id));
        const uniqueNew = newNotifications.filter(n => !existingIds.has(n.id));
        return [...uniqueNew, ...prev];
      }
      
      return prev;
    });
  }, [contracts]);

  const markAsRead = (id) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, read: true }
          : notification
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, read: true }))
    );
  };

  const deleteNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const addNotification = (notification) => {
    const newNotification = {
      id: `custom-${Date.now()}`,
      ...notification,
      timestamp: notification.timestamp || 'Just now',
      read: false
    };
    setNotifications(prev => [newNotification, ...prev]);
  };

  const getUnreadCount = () => {
    return notifications.filter(n => !n.read).length;
  };

  const getHighPriorityCount = () => {
    return notifications.filter(n => n.priority === 'high' && !n.read).length;
  };

  const value = {
    notifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    addNotification,
    getUnreadCount,
    getHighPriorityCount
  };

  return (
    <NotificationsContext.Provider value={value}>
      {children}
    </NotificationsContext.Provider>
  );
};

// Helper function to get time ago string
function getTimeAgo(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  return date.toLocaleDateString();
}

