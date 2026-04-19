const validResult = () => ({ valid: true, error: null });
const invalidResult = (error) => ({ valid: false, error });

const isObject = (value) => value && typeof value === 'object' && !Array.isArray(value);

const isValidUrlOrPath = (value) => {
  try {
    return (
      value.startsWith('http://') ||
      value.startsWith('https://') ||
      value.startsWith('/uploads/') ||
      value.startsWith('/')
    );
  } catch {
    return false;
  }
};

const isValidCarouselLink = (value) => (
  value.startsWith('http://') ||
  value.startsWith('https://') ||
  value.startsWith('/') ||
  value.startsWith('#') ||
  value.startsWith('mailto:') ||
  value.startsWith('tel:')
);

const validateBaseBlock = (block) => {
  if (!block || typeof block !== 'object') {
    return invalidResult('Block must be an object');
  }

  if (!block.type || typeof block.type !== 'string') {
    return invalidResult('Block must have a type property');
  }

  if (!BLOCK_TYPES.includes(block.type)) {
    return invalidResult(`Invalid block type: ${block.type}. Must be one of: ${BLOCK_TYPES.join(', ')}`);
  }

  if (block.data === undefined || block.data === null) {
    return invalidResult('Block must have a data property');
  }

  if (!isObject(block.data)) {
    return invalidResult('Block data must be an object');
  }

  return null;
};

const validateParagraphBlock = (data) => {
  if (typeof data.text !== 'string') {
    return invalidResult('Paragraph block must have text in data.text');
  }
  return null;
};

const validateHeadingBlock = (data) => {
  if (typeof data.text !== 'string') {
    return invalidResult('Heading block must have text in data.text');
  }
  if (![1, 2, 3].includes(data.level)) {
    return invalidResult('Heading block must have level 1, 2, or 3 in data.level');
  }
  return null;
};

const validateImageBlock = (data) => {
  if (typeof data.url !== 'string' || !data.url.trim()) {
    return invalidResult('Image block must have a valid URL in data.url');
  }

  if (!isValidUrlOrPath(data.url)) {
    return invalidResult('Image URL must be a valid URL or path');
  }

  if (typeof data.alt !== 'string') {
    return invalidResult('Image block must have alt text in data.alt');
  }

  return null;
};

const validateCodeBlock = (data) => {
  if (typeof data.code !== 'string') {
    return invalidResult('Code block must have code in data.code');
  }
  if (data.code.trim().length === 0) {
    return invalidResult('Code block cannot be empty');
  }

  if (data.language !== undefined) {
    if (typeof data.language !== 'string') {
      return invalidResult('Code block language must be a string');
    }
    const languagePattern = /^[a-zA-Z0-9_-]+$/;
    if (data.language.trim().length > 0 && !languagePattern.test(data.language.trim())) {
      return invalidResult('Code block language must be a valid identifier');
    }
  }

  if (data.filename !== undefined && typeof data.filename !== 'string') {
    return invalidResult('Code block filename must be a string');
  }

  return null;
};

const validateAuthorBoxBlock = (data) => {
  if (data.authorId && typeof data.authorId === 'string' && data.authorId.trim()) {
    const authorId = data.authorId.trim();
    if (!/^[0-9a-fA-F]{24}$/.test(authorId)) {
      return invalidResult('Author box authorId must be a valid MongoDB ObjectId');
    }
  } else {
    if (typeof data.name !== 'string' || !data.name || !data.name.trim()) {
      return invalidResult('Author box must have name in data.name (or authorId)');
    }
    if (typeof data.bio !== 'string' || data.bio === undefined) {
      return invalidResult('Author box must have bio in data.bio');
    }
    if (data.avatar && typeof data.avatar === 'string' && data.avatar.trim()) {
      const avatarUrl = data.avatar.trim();
      if (!isValidUrlOrPath(avatarUrl)) {
        return invalidResult('Author box avatar must be a valid URL or path');
      }
    }
  }

  return null;
};

const validateTableOfContentsItems = (items) => {
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (typeof item !== 'object' || !item) {
      return invalidResult(`Table of contents item ${i} must be an object`);
    }
    if (typeof item.text !== 'string' || !item.text.trim()) {
      return invalidResult(`Table of contents item ${i} must have text`);
    }
    if (typeof item.id !== 'string' || !item.id.trim()) {
      return invalidResult(`Table of contents item ${i} must have id`);
    }
    if (item.level !== undefined && ![1, 2, 3, 4, 5, 6].includes(item.level)) {
      return invalidResult(`Table of contents item ${i} level must be between 1 and 6`);
    }
  }
  return null;
};

const validateTableOfContentsBlock = (data) => {
  if (data.autoGenerate !== undefined && typeof data.autoGenerate !== 'boolean') {
    return invalidResult('Table of contents autoGenerate must be a boolean');
  }

  if (data.items && Array.isArray(data.items)) {
    const itemsValidation = validateTableOfContentsItems(data.items);
    if (itemsValidation) {
      return itemsValidation;
    }
  } else if (data.items !== undefined && !Array.isArray(data.items)) {
    return invalidResult('Table of contents items must be an array');
  }

  if (data.title !== undefined && typeof data.title !== 'string') {
    return invalidResult('Table of contents title must be a string');
  }

  return null;
};

const validateQuizOrPollOptions = (options) => {
  for (let i = 0; i < options.length; i++) {
    const option = options[i];
    if (typeof option !== 'object' || option === null) {
      return invalidResult(`Quiz/Poll option ${i + 1} must be an object`);
    }
    if (typeof option.text !== 'string' || option.text.trim().length === 0) {
      return invalidResult(`Quiz/Poll option ${i + 1} must have a non-empty text`);
    }
    if (option.text.length > 200) {
      return invalidResult(`Quiz/Poll option ${i + 1} text cannot exceed 200 characters`);
    }
    if (option.value !== undefined && typeof option.value !== 'string' && typeof option.value !== 'number') {
      return invalidResult(`Quiz/Poll option ${i + 1} value must be a string or number`);
    }
  }
  return null;
};

const validateQuizOrPollBlock = (block) => {
  const { data } = block;

  if (typeof data.question !== 'string' || data.question.trim().length === 0) {
    return invalidResult('Quiz/Poll block must have a non-empty question');
  }
  if (data.question.length > 500) {
    return invalidResult('Quiz/Poll question cannot exceed 500 characters');
  }
  if (!Array.isArray(data.options) || data.options.length < 2) {
    return invalidResult('Quiz/Poll block must have at least 2 options');
  }
  if (data.options.length > 20) {
    return invalidResult('Quiz/Poll block cannot have more than 20 options');
  }

  const optionsValidation = validateQuizOrPollOptions(data.options);
  if (optionsValidation) {
    return optionsValidation;
  }

  if (data.allowMultipleAnswers !== undefined && typeof data.allowMultipleAnswers !== 'boolean') {
    return invalidResult('Quiz/Poll allowMultipleAnswers must be a boolean');
  }

  const isPoll = block.type === 'poll' || data.blockType === 'poll';
  if (!isPoll) {
    if (data.correctAnswer !== undefined && data.correctAnswer !== null) {
      if (typeof data.correctAnswer !== 'string' && typeof data.correctAnswer !== 'number') {
        return invalidResult('Quiz correctAnswer must be a string or number');
      }
    }
    if (data.correctAnswers !== undefined && data.correctAnswers !== null) {
      if (!Array.isArray(data.correctAnswers)) {
        return invalidResult('Quiz correctAnswers must be an array');
      }
    }
  }

  return null;
};

const validateCarouselItems = (items) => {
  for (let i = 0; i < items.length; i++) {
    const item = items[i];

    if (typeof item !== 'object' || item === null) {
      return invalidResult(`Carousel item ${i + 1} must be an object`);
    }

    if (typeof item.imageUrl !== 'string' || !item.imageUrl.trim()) {
      return invalidResult(`Carousel item ${i + 1} must have a valid imageUrl`);
    }

    if (!isValidUrlOrPath(item.imageUrl)) {
      return invalidResult(`Carousel item ${i + 1} imageUrl must be a valid URL or path`);
    }

    if (typeof item.alt !== 'string' || !item.alt.trim()) {
      return invalidResult(`Carousel item ${i + 1} must have alt text`);
    }
    if (item.alt.length > 200) {
      return invalidResult(`Carousel item ${i + 1} alt text cannot exceed 200 characters`);
    }

    if (item.link !== undefined && item.link !== null) {
      if (typeof item.link !== 'string') {
        return invalidResult(`Carousel item ${i + 1} link must be a valid URL string`);
      }

      const trimmedLink = item.link.trim();
      if (trimmedLink.length > 0 && !isValidCarouselLink(trimmedLink)) {
        return invalidResult(`Carousel item ${i + 1} link must be a valid URL (http:// or https://), path (starting with /), or anchor (starting with #)`);
      }
    }

    if (item.title !== undefined && typeof item.title !== 'string') {
      return invalidResult(`Carousel item ${i + 1} title must be a string`);
    }
    if (item.title && item.title.length > 200) {
      return invalidResult(`Carousel item ${i + 1} title cannot exceed 200 characters`);
    }

    if (item.description !== undefined && typeof item.description !== 'string') {
      return invalidResult(`Carousel item ${i + 1} description must be a string`);
    }
    if (item.description && item.description.length > 500) {
      return invalidResult(`Carousel item ${i + 1} description cannot exceed 500 characters`);
    }
  }

  return null;
};

const validateCarouselBlock = (data) => {
  if (!Array.isArray(data.items) || data.items.length === 0) {
    return invalidResult('Carousel block must have at least one item');
  }
  if (data.items.length > 50) {
    return invalidResult('Carousel block cannot have more than 50 items');
  }

  return validateCarouselItems(data.items);
};

const blockValidators = {
  paragraph: (block) => validateParagraphBlock(block.data),
  heading: (block) => validateHeadingBlock(block.data),
  image: (block) => validateImageBlock(block.data),
  code: (block) => validateCodeBlock(block.data),
  authorBox: (block) => validateAuthorBoxBlock(block.data),
  tableOfContents: (block) => validateTableOfContentsBlock(block.data),
  quiz: validateQuizOrPollBlock,
  poll: validateQuizOrPollBlock,
  carousel: (block) => validateCarouselBlock(block.data),
};

export const validateBlock = (block) => {
  const baseValidation = validateBaseBlock(block);
  if (baseValidation) {
    return baseValidation;
  }

  const validator = blockValidators[block.type];
  if (!validator) {
    return invalidResult(`Unknown block type: ${block.type}`);
  }

  const typeValidation = validator(block);
  if (typeValidation) {
    return typeValidation;
  }

  return validResult();
};