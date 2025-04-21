export const getFullAvatarUrl = (avatarUrl: string): string => {
    // If the URL is already absolute (starts with http:// or https://), return it as is
  if (avatarUrl.startsWith('http://') || avatarUrl.startsWith('https://')) {
    return avatarUrl;
  }
  
  // Otherwise, prepend the API base URL
  return `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}${avatarUrl}`;
}; 