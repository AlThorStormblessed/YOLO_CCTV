// Configuration for the application
// These values can be overridden by environment variables

// Helper function to safely access window object (for SSR compatibility)
const getWindowHostname = () => {
  if (typeof window !== 'undefined') {
    return window.location.hostname;
  }
  return null;
};

// Replace "backend" with actual hostname when in browser
const adjustHostForBrowser = (host: string) => {
  if (typeof window !== 'undefined' && host === 'backend') {
    return window.location.hostname;
  }
  return host;
};

export const config = {
  // Socket.IO server configuration
  SOCKET_PROTOCOL: process.env.NEXT_PUBLIC_SOCKET_PROTOCOL || "http:",
  SOCKET_HOST: adjustHostForBrowser(process.env.NEXT_PUBLIC_SOCKET_HOST || getWindowHostname() || "localhost"),
  SOCKET_PORT: process.env.NEXT_PUBLIC_SOCKET_PORT || "5003",

  // API server configuration
  API_PROTOCOL: process.env.NEXT_PUBLIC_API_PROTOCOL || "http:",
  API_HOST: adjustHostForBrowser(process.env.NEXT_PUBLIC_API_HOST || getWindowHostname() || "localhost"),
  API_PORT: process.env.NEXT_PUBLIC_API_PORT || "5003",
}
