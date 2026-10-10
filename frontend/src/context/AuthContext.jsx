// src/context/AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from "react";
import { jwtDecode } from "jwt-decode";


const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  useEffect(() => {
  const token = localStorage.getItem("token");
  if (token) {
    try {
      const decoded = jwtDecode(token);
      setUser(decoded);
    } catch (error) {
      console.warn("Invalid token, clearing...");
      localStorage.removeItem("token");
    }
  }
  }, []);
  
  const login = (role) => {
    // Mock JWT for now
    const mockToken = btoa(JSON.stringify({ role }));
    localStorage.setItem("token", mockToken);
    setUser({ role });
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
