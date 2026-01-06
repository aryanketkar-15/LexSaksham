import React, { useState } from 'react';
import { motion } from 'motion/react';
import { useNavigate } from 'react-router-dom';
import { useNotifications } from '../context/NotificationsContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Separator } from './ui/separator';
import { ScrollArea } from './ui/scroll-area';
import { toast } from 'sonner';
import { 
  Bell, 
  BellOff, 
  CheckCircle, 
  AlertTriangle, 
  Info, 
  X,
  Settings,
  Filter,
  Archive,
  Trash2,
  Clock,
  User,
  FileText,
  Shield,
  TrendingUp,
  Calendar,
  Mail
} from 'lucide-react';

// Notifications are now loaded from NotificationsContext

const alertSettings = [
  {
    category: 'High Risk Contracts',
    description: 'Get notified when contracts with high or critical risk are detected',
    enabled: true,
    email: true,
    push: true
  },
  {
    category: 'Contract Expiry',
    description: 'Receive alerts 30, 14, and 7 days before contract expiration',
    enabled: true,
    email: true,
    push: false
  },
  {
    category: 'Analysis Complete',
    description: 'Notification when AI analysis is finished for uploaded contracts',
    enabled: false,
    email: false,
    push: true
  },
  {
    category: 'Compliance Issues',
    description: 'Alert for contracts that fail compliance checks',
    enabled: true,
    email: true,
    push: true
  },
  {
    category: 'Weekly Reports',
    description: 'Receive weekly analytics and summary reports',
    enabled: true,
    email: true,
    push: false
  }
];

const getNotificationIcon = (type) => {
  switch (type) {
    case 'alert': return <AlertTriangle className="h-4 w-4 text-red-500" />;
    case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    case 'success': return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'info': return <Info className="h-4 w-4 text-blue-500" />;
    default: return <Bell className="h-4 w-4" />;
  }
};

const getPriorityColor = (priority) => {
  switch (priority) {
    case 'high': return 'bg-red-100 text-red-800 border-red-200';
    case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low': return 'bg-gray-100 text-gray-800 border-gray-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const getCategoryIcon = (category) => {
  switch (category) {
    case 'risk': return <Shield className="h-3 w-3" />;
    case 'analysis': return <TrendingUp className="h-3 w-3" />;
    case 'expiry': return <Calendar className="h-3 w-3" />;
    case 'compliance': return <Shield className="h-3 w-3" />;
    case 'report': return <FileText className="h-3 w-3" />;
    case 'upload': return <FileText className="h-3 w-3" />;
    default: return <Bell className="h-3 w-3" />;
  }
};

export default function Notifications() {
  const navigate = useNavigate();
  const { 
    notifications: notificationList, 
    markAsRead, 
    markAllAsRead, 
    deleteNotification,
    getUnreadCount,
    getHighPriorityCount
  } = useNotifications();
  
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [settingsChanged, setSettingsChanged] = useState(false);

  const unreadCount = getUnreadCount();
  const highPriorityCount = getHighPriorityCount();

  const handleMarkAllAsRead = () => {
    markAllAsRead();
    toast.success('All notifications marked as read');
  };

  const handleDeleteNotification = (id) => {
    deleteNotification(id);
    toast.success('Notification deleted');
  };

  const executeAction = (action, notification) => {
    markAsRead(notification.id);
    
    if (action === 'View Contract' || action === 'View Details' || action === 'Review Contract') {
      if (notification.contractId) {
        navigate(`/contracts/${notification.contractId}`);
      }
    } else if (action === 'View Results') {
      if (notification.contractId) {
        navigate(`/contracts/${notification.contractId}`);
      }
    } else {
      toast.success(`Executing: ${action}`);
    }
  };

  const filteredNotifications = notificationList.filter(notification => {
    if (selectedFilter === 'all') return true;
    if (selectedFilter === 'unread') return !notification.read;
    if (selectedFilter === 'high') return notification.priority === 'high';
    return notification.category === selectedFilter;
  });

  const toggleSetting = (index, field) => {
    setSettingsChanged(true);
    // In a real app, this would update the settings
    toast.info('Settings will be saved automatically');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1>Notifications & Alerts</h1>
          <p className="text-muted-foreground">
            Stay updated with contract activities and important alerts
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="secondary">
            {unreadCount} unread
          </Badge>
          {highPriorityCount > 0 && (
            <Badge className="bg-red-100 text-red-800">
              {highPriorityCount} high priority
            </Badge>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Bell className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm text-muted-foreground">Total</p>
                <p className="text-2xl font-bold">{notificationList.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-sm text-muted-foreground">High Priority</p>
                <p className="text-2xl font-bold text-red-600">{highPriorityCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-yellow-500" />
              <div>
                <p className="text-sm text-muted-foreground">Unread</p>
                <p className="text-2xl font-bold text-yellow-600">{unreadCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">Action Items</p>
                <p className="text-2xl font-bold text-green-600">
                  {notificationList.filter(n => n.actionRequired).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="notifications" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="settings">Alert Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="notifications" className="space-y-6">
          {/* Filters and Actions */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Filter className="h-4 w-4 text-muted-foreground" />
                  <div className="flex space-x-2">
                    {['all', 'unread', 'high', 'risk', 'compliance', 'expiry'].map((filter) => (
                      <Button
                        key={filter}
                        variant={selectedFilter === filter ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setSelectedFilter(filter)}
                      >
                        {filter.charAt(0).toUpperCase() + filter.slice(1)}
                      </Button>
                    ))}
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  <Button variant="outline" size="sm" onClick={handleMarkAllAsRead}>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Mark All Read
                  </Button>
                  <Button variant="outline" size="sm">
                    <Archive className="h-4 w-4 mr-2" />
                    Archive All
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notifications List */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Notifications</CardTitle>
              <CardDescription>
                {filteredNotifications.length} notifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-4">
                  {filteredNotifications.map((notification, index) => (
                    <motion.div
                      key={notification.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`border rounded-lg p-4 ${
                        !notification.read ? 'bg-blue-50 border-blue-200' : 'hover:bg-muted/50'
                      } transition-colors`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3 flex-1">
                          <div className="p-1.5 rounded-full bg-background border">
                            {getNotificationIcon(notification.type)}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-1">
                              <h4 className="font-medium">{notification.title}</h4>
                              {!notification.read && (
                                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                              )}
                            </div>
                            
                            <p className="text-sm text-muted-foreground mb-2">
                              {notification.message}
                            </p>
                            
                            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              <span>{notification.timestamp}</span>
                              <Separator orientation="vertical" className="h-3" />
                              <div className="flex items-center space-x-1">
                                {getCategoryIcon(notification.category)}
                                <span>{notification.category}</span>
                              </div>
                              <Separator orientation="vertical" className="h-3" />
                              <Badge className={getPriorityColor(notification.priority)}>
                                {notification.priority}
                              </Badge>
                            </div>
                            
                            {notification.actions && notification.actions.length > 0 && (
                              <div className="flex flex-wrap gap-2 mt-3">
                                {notification.actions.map((action, idx) => (
                                  <Button
                                    key={idx}
                                    size="sm"
                                    variant="outline"
                                    onClick={() => executeAction(action, notification)}
                                  >
                                    {action}
                                  </Button>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-4">
                          {!notification.read && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => markAsRead(notification.id)}
                            >
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeleteNotification(notification.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Alert Preferences</CardTitle>
              <CardDescription>
                Configure when and how you receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {alertSettings.map((setting, index) => (
                <div key={index} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">{setting.category}</h4>
                      <p className="text-sm text-muted-foreground">
                        {setting.description}
                      </p>
                    </div>
                    <Switch 
                      checked={setting.enabled}
                      onCheckedChange={() => toggleSetting(index, 'enabled')}
                    />
                  </div>
                  
                  {setting.enabled && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="ml-4 flex items-center space-x-6"
                    >
                      <div className="flex items-center space-x-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor={`email-${index}`}>Email</Label>
                        <Switch 
                          id={`email-${index}`}
                          checked={setting.email}
                          onCheckedChange={() => toggleSetting(index, 'email')}
                        />
                      </div>
                      <div className="flex items-center space-x-2">
                        <Bell className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor={`push-${index}`}>Push</Label>
                        <Switch 
                          id={`push-${index}`}
                          checked={setting.push}
                          onCheckedChange={() => toggleSetting(index, 'push')}
                        />
                      </div>
                    </motion.div>
                  )}
                  
                  {index < alertSettings.length - 1 && <Separator />}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quiet Hours</CardTitle>
              <CardDescription>
                Set times when you don't want to receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Enable Quiet Hours</Label>
                <Switch defaultChecked={false} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Start Time</Label>
                  <input 
                    type="time" 
                    className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm" 
                    defaultValue="22:00"
                  />
                </div>
                <div>
                  <Label>End Time</Label>
                  <input 
                    type="time" 
                    className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm" 
                    defaultValue="08:00"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

