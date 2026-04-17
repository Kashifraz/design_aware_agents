const checkSpamPatterns = (content, authorName, authorEmail) => {
    const spamKeywords = [
      'buy now', 'click here', 'limited time', 'act now',
      'make money', 'get rich', 'free money', 'guaranteed',
      'no credit check', 'risk free', 'winner', 'congratulations'
    ];
    
    const contentLower = content.toLowerCase();
    const nameLower = authorName.toLowerCase();
    const emailLower = authorEmail.toLowerCase();
    
    // Check for excessive links
    const linkCount = (content.match(/https?:\/\//g) || []).length;
    if (linkCount > 2) {
      return { isSpam: true, reason: 'Too many links' };
    }
    
    // Check for spam keywords
    for (const keyword of spamKeywords) {
      if (contentLower.includes(keyword) || nameLower.includes(keyword) || emailLower.includes(keyword)) {
        return { isSpam: true, reason: 'Contains spam keywords' };
      }
    }
    
    // Check for excessive capitalization
    const upperCaseRatio = (content.match(/[A-Z]/g) || []).length / content.length;
    if (upperCaseRatio > 0.5 && content.length > 20) {
      return { isSpam: true, reason: 'Excessive capitalization' };
    }
    
    return { isSpam: false };
  };