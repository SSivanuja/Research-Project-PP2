import React, { createContext, useContext, useState, useEffect } from 'react';

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  firm: string;
  avatar: string | null;
  createdAt: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const storedUser = localStorage.getItem('legalvision_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, _password: string): Promise<boolean> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Accept any email/password combination
    const dummyUser: User = {
      id: "usr_001",
      name: email.split('@')[0].split('.').map(n => 
        n.charAt(0).toUpperCase() + n.slice(1)
      ).join(' ') || "Arun Perera",
      email: email,
      role: "Legal Analyst",
      firm: "Perera & Associates",
      avatar: null,
      createdAt: new Date().toISOString()
    };
    
    localStorage.setItem('legalvision_user', JSON.stringify(dummyUser));
    setUser(dummyUser);
    return true;
  };

  const logout = () => {
    localStorage.removeItem('legalvision_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      isAuthenticated: !!user, 
      login, 
      logout,
      isLoading 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
