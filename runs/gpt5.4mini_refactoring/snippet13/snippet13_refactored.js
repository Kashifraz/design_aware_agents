const spamKeywords = [
  'buy now', 'click here', 'limited time', 'act now',
  'make money', 'get rich', 'free money', 'guaranteed',
  'no credit check', 'risk free', 'winner', 'congratulations'
];

const hasTooManyLinks = (content) => {
  const linkCount = (content.match(/https?:\/\//g) || []).length;
  return linkCount > 2;
};

const containsSpamKeywords = (content, authorName, authorEmail) => {
  const contentLower = content.toLowerCase();
  const nameLower = authorName.toLowerCase();
  const emailLower = authorEmail.toLowerCase();

  for (const keyword of spamKeywords) {
    if (
      contentLower.includes(keyword) ||
      nameLower.includes(keyword) ||
      emailLower.includes(keyword)
    ) {
      return true;
    }
  }

  return false;
};

const hasExcessiveCapitalization = (content) => {
  const upperCaseRatio = (content.match(/[A-Z]/g) || []).length / content.length;
  return upperCaseRatio > 0.5 && content.length > 20;
};

const checkSpamPatterns = (content, authorName, authorEmail) => {
  if (hasTooManyLinks(content)) {
    return { isSpam: true, reason: 'Too many links' };
  }

  if (containsSpamKeywords(content, authorName, authorEmail)) {
    return { isSpam: true, reason: 'Contains spam keywords' };
  }

  if (hasExcessiveCapitalization(content)) {
    return { isSpam: true, reason: 'Excessive capitalization' };
  }

  return { isSpam: false };
};