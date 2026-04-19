const isNonEmptyString = (value) => typeof value === 'string' && value.trim().length > 0;

const isValidUrlOrPath = (value) => {
  try {
    return (
      typeof value === 'string' &&
      (value.startsWith('http://') ||
        value.startsWith('https://') ||
        value.startsWith('/uploads/') ||
        value.startsWith('/'))
    );
  } catch {
    return false;
  }
};

const isValidCarouselLink = (value) => {
  try {
    return (
      typeof value === 'string' &&
      (value.startsWith('http://') ||
        value.startsWith('https://') ||
        value.startsWith('/') ||
        value.startsWith('#') ||
        value.startsWith('mailto:') ||
        value.startsWith('tel:'))
    );
  } catch {
    return false;
  }
};

const validateTableOfContentsItem = (item, index) => {
  if (typeof item !== 'object' || !item) {
    return { valid: false, error: `Table of contents item ${index} must be an object` };
  }
  if (typeof item.text !== 'string' || !item.text.trim()) {
    return { valid: false, error: `Table of contents item ${index} must have text` };
  }
  if (typeof item.id !== 'string' || !item.id.trim()) {
    return { valid: false, error: `Table of contents item ${index} must have id` };
  }
  if (item.level !== undefined && ![1, 2, 3, 4, 5, 6].includes(item.level)) {
    return { valid: false, error: `Table of contents item ${index} level must be between 1 and 6` };
  }
  return { valid: true, error: null };
};

const validateQuizOrPollOption = (option, index) => {
  if (typeof option !== 'object' || option === null) {
    return { valid: false, error: `Quiz/Poll option ${index + 1} must be an object` };
  }
  if (typeof option.text !== 'string' || option.text.trim().length === 0) {
    return { valid: false, error: `Quiz/Poll option ${index + 1} must have a non-empty text` };
  }
  if (option.text.length > 200) {
    return { valid: false, error: `Quiz/Poll option ${index + 1} text cannot exceed 200 characters` };
  }
  if (option.value !== undefined && typeof option.value !== 'string' && typeof option.value !== 'number') {
    return { valid: false, error: `Quiz/Poll option ${index + 1} value must be a string or number` };
  }
  return { valid: true, error: null };
};

const validateImageBlock = (data) => {
  if (typeof data.url !== 'string' || !data.url.trim()) {
    return { valid: false, error: 'Image block must have a valid URL in data.url' };
  }
  if (!isValidUrlOrPath(data.url)) {
    return { valid: false, error: 'Image URL must be a valid URL or path' };
  }
  if (typeof data.alt !== 'string') {
    return { valid: false, error: 'Image block must have alt text in data.alt' };
  }
  return { valid: true, error: null };
};

const validateAuthorBoxBlock = (data) => {
  if (data.authorId && typeof data.authorId === 'string' && data.authorId.trim()) {
    const authorId = data.authorId.trim();
    if (!/^[0-9a-fA-F]{24}$/.test(authorId)) {
      return { valid: false, error: 'Author box authorId must be a valid MongoDB ObjectId' };
    }
    return { valid: true, error: null };
  }

  if (typeof data.name !== 'string' || !data.name || !data.name.trim()) {
    return { valid: false, error: 'Author box must have name in data.name (or authorId)' };
  }
  if (typeof data.bio !== 'string' || data.bio === undefined) {
    return { valid: false, error: 'Author box must have bio in data.bio' };
  }
  if (data.avatar && typeof data.avatar === 'string' && data.avatar.trim()) {
    const avatarUrl = data.avatar.trim();
    if (!isValidUrlOrPath(avatarUrl)) {
      return { valid: false, error: 'Author box avatar must be a valid URL or path' };
    }
  }

  return { valid: true, error: null };
};

const validateQuizOrPollBlock = (block) => {
  if (typeof block.data.question !== 'string' || block.data.question.trim().length === 0) {
    return { valid: false, error: 'Quiz/Poll block must have a non-empty question' };
  }
  if (block.data.question.length > 500) {
    return { valid: false, error: 'Quiz/Poll question cannot exceed 500 characters' };
  }
  if (!Array.isArray(block.data.options) || block.data.options.length < 2) {
    return { valid: false, error: 'Quiz/Poll block must have at least 2 options' };
  }
  if (block.data.options.length > 20) {
    return { valid: false, error: 'Quiz/Poll block cannot have more than 20 options' };
  }

  for (let i = 0; i < block.data.options.length; i++) {
    const result = validateQuizOrPollOption(block.data.options[i], i);
    if (!result.valid) return result;
  }

  if (block.data.allowMultipleAnswers !== undefined && typeof block.data.allowMultipleAnswers !== 'boolean') {
    return { valid: false, error: 'Quiz/Poll allowMultipleAnswers must be a boolean' };
  }

  const isPoll = block.type === 'poll' || block.data.blockType === 'poll';
  if (!isPoll) {
    if (block.data.correctAnswer !== undefined && block.data.correctAnswer !== null) {
      if (typeof block.data.correctAnswer !== 'string' && typeof block.data.correctAnswer !== 'number') {
        return { valid: false, error: 'Quiz correctAnswer must be a string or number' };
      }
    }
    if (block.data.correctAnswers !== undefined && block.data.correctAnswers !== null) {
      if (!Array.isArray(block.data.correctAnswers)) {
        return { valid: false, error: 'Quiz correctAnswers must be an array' };
      }
    }
  }

  return { valid: true, error: null };
};

const validateCarouselItem = (item, index) => {
  if (typeof item !== 'object' || item === null) {
    return { valid: false, error: `Carousel item ${index + 1} must be an object` };
  }

  if (typeof item.imageUrl !== 'string' || !item.imageUrl.trim()) {
    return { valid: false, error: `Carousel item ${index + 1} must have a valid imageUrl` };
  }
  if (!isValidUrlOrPath(item.imageUrl)) {
    return { valid: false, error: `Carousel item ${index + 1} imageUrl must be a valid URL or path` };
  }

  if (typeof item.alt !== 'string' || !item.alt.trim()) {
    return { valid: false, error: `Carousel item ${index + 1} must have alt text` };
  }
  if (item.alt.length > 200) {
    return { valid: false, error: `Carousel item ${index + 1} alt text cannot exceed 200 characters` };
  }

  if (item.link !== undefined && item.link !== null) {
    if (typeof item.link !== 'string') {
      return { valid: false, error: `Carousel item ${index + 1} link must be a valid URL string` };
    }

    const trimmedLink = item.link.trim();
    if (trimmedLink.length > 0 && !isValidCarouselLink(trimmedLink)) {
      return {
        valid: false,
        error: `Carousel item ${index + 1} link must be a valid URL (http:// or https://), path (starting with /), or anchor (starting with #)`
      };
    }
  }

  if (item.title !== undefined && typeof item.title !== 'string') {
    return { valid: false, error: `Carousel item ${index + 1} title must be a string` };
  }
  if (item.title && item.title.length > 200) {
    return { valid: false, error: `Carousel item ${index + 1} title cannot exceed 200 characters` };
  }

  if (item.description !== undefined && typeof item.description !== 'string') {
    return { valid: false, error: `Carousel item ${index + 1} description must be a string` };
  }
  if (item.description && item.description.length > 500) {
    return { valid: false, error: `Carousel item ${index + 1} description cannot exceed 500 characters` };
  }

  return { valid: true, error: null };
};

const validateCarouselBlock = (data) => {
  if (!Array.isArray(data.items) || data.items.length === 0) {
    return { valid: false, error: 'Carousel block must have at least one item' };
  }
  if (data.items.length > 50) {
    return { valid: false, error: 'Carousel block cannot have more than 50 items' };
  }

  for (let i = 0; i < data.items.length; i++) {
    const result = validateCarouselItem(data.items[i], i);
    if (!result.valid) return result;
  }

  return { valid: true, error: null };
};

export const validateBlock = (block) => {
  if (!block || typeof block !== 'object') {
    return { valid: false, error: 'Block must be an object' };
  }

  if (!block.type || typeof block.type !== 'string') {
    return { valid: false, error: 'Block must have a type property' };
  }

  if (!BLOCK_TYPES.includes(block.type)) {
    return { valid: false, error: `Invalid block type: ${block.type}. Must be one of: ${BLOCK_TYPES.join(', ')}` };
  }

  if (block.data === undefined || block.data === null) {
    return { valid: false, error: 'Block must have a data property' };
  }

  if (typeof block.data !== 'object' || Array.isArray(block.data)) {
    return { valid: false, error: 'Block data must be an object' };
  }

  switch (block.type) {
    case 'paragraph':
      if (typeof block.data.text !== 'string') {
        return { valid: false, error: 'Paragraph block must have text in data.text' };
      }
      break;

    case 'heading':
      if (typeof block.data.text !== 'string') {
        return { valid: false, error: 'Heading block must have text in data.text' };
      }
      if (![1, 2, 3].includes(block.data.level)) {
        return { valid: false, error: 'Heading block must have level 1, 2, or 3 in data.level' };
      }
      break;

    case 'image': {
      const result = validateImageBlock(block.data);
      if (!result.valid) return result;
      break;
    }

    case 'code':
      if (typeof block.data.code !== 'string') {
        return { valid: false, error: 'Code block must have code in data.code' };
      }
      if (block.data.code.trim().length === 0) {
        return { valid: false, error: 'Code block cannot be empty' };
      }
      if (block.data.language !== undefined) {
        if (typeof block.data.language !== 'string') {
          return { valid: false, error: 'Code block language must be a string' };
        }
        const languagePattern = /^[a-zA-Z0-9_-]+$/;
        if (block.data.language.trim().length > 0 && !languagePattern.test(block.data.language.trim())) {
          return { valid: false, error: 'Code block language must be a valid identifier' };
        }
      }
      if (block.data.filename !== undefined && typeof block.data.filename !== 'string') {
        return { valid: false, error: 'Code block filename must be a string' };
      }
      break;

    case 'authorBox': {
      const result = validateAuthorBoxBlock(block.data);
      if (!result.valid) return result;
      break;
    }

    case 'tableOfContents':
      if (block.data.autoGenerate !== undefined && typeof block.data.autoGenerate !== 'boolean') {
        return { valid: false, error: 'Table of contents autoGenerate must be a boolean' };
      }

      if (block.data.items && Array.isArray(block.data.items)) {
        for (let i = 0; i < block.data.items.length; i++) {
          const result = validateTableOfContentsItem(block.data.items[i], i);
          if (!result.valid) return result;
        }
      } else if (block.data.items !== undefined && !Array.isArray(block.data.items)) {
        return { valid: false, error: 'Table of contents items must be an array' };
      }

      if (block.data.title !== undefined && typeof block.data.title !== 'string') {
        return { valid: false, error: 'Table of contents title must be a string' };
      }
      break;

    case 'quiz':
    case 'poll': {
      const result = validateQuizOrPollBlock(block);
      if (!result.valid) return result;
      break;
    }

    case 'carousel': {
      const result = validateCarouselBlock(block.data);
      if (!result.valid) return result;
      break;
    }

    default:
      return { valid: false, error: `Unknown block type: ${block.type}` };
  }

  return { valid: true, error: null };
};