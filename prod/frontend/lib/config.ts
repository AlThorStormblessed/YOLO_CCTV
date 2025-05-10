// Configuration for the application
// These values can be overridden by environment variables

// Helper function to detect if running in production
const isProduction = () => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    return hostname === 'yolo.viewer.in' || hostname === 'model.viewer.in';
  }
  return false;
};

// Use production or development settings based on environment
const getConfig = () => {
  // Production configuration
  if (isProduction()) {
    return {
      SOCKET_PROTOCOL: "https:",
      SOCKET_HOST: "model.viewer.in",
      SOCKET_PORT: "",  // Empty for default HTTPS port
      API_PROTOCOL: "https:",
      API_HOST: "model.viewer.in",
      API_PORT: ""  // Empty for default HTTPS port
    };
  } 
  // Development configuration (localhost)
  else {
    return {
      SOCKET_PROTOCOL: process.env.NEXT_PUBLIC_SOCKET_PROTOCOL || "http:",
      SOCKET_HOST: process.env.NEXT_PUBLIC_SOCKET_HOST || "localhost",
      SOCKET_PORT: process.env.NEXT_PUBLIC_SOCKET_PORT || "5003",
      API_PROTOCOL: process.env.NEXT_PUBLIC_API_PROTOCOL || "http:",
      API_HOST: process.env.NEXT_PUBLIC_API_HOST || "localhost",
      API_PORT: process.env.NEXT_PUBLIC_API_PORT || "5003"
    };
  }
};

export const config = getConfig();
