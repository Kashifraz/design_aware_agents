const isValidObjectId = (value) => /^[0-9a-fA-F]{24}$/.test(value);

const validateStatsParams = (postId, blockId) => {
  if (!postId || !isValidObjectId(postId)) {
    return 'Invalid post ID';
  }

  if (!blockId || typeof blockId !== 'string' || blockId.trim().length === 0) {
    return 'Invalid block ID';
  }

  return null;
};

const resolveBlock = (post, blockId) => {
  let block = null;

  if (/^\d+$/.test(blockId)) {
    const index = parseInt(blockId, 10);
    if (index >= 0 && index < post.content.length) {
      block = post.content[index];
    }
  } else {
    block = post.content.find(b => (b.type === 'quiz' || b.type === 'poll'));
  }

  return block;
};

const buildOptionStats = (options) => options.map((opt, index) => ({
  index,
  value: opt.value !== undefined ? opt.value : index,
  text: opt.text,
  count: 0,
  percentage: 0
}));

const incrementMatchingOptionCount = (optionStats, answer) => {
  const optionIndex = optionStats.findIndex(stat =>
    stat.value === answer ||
    stat.index === answer ||
    String(stat.value) === String(answer) ||
    String(stat.index) === String(answer)
  );

  if (optionIndex !== -1) {
    optionStats[optionIndex].count++;
  }
};

const countResponses = (responses, optionStats) => {
  responses.forEach(response => {
    const answers = Array.isArray(response.answers) ? response.answers : [response.answers];
    answers.forEach(answer => incrementMatchingOptionCount(optionStats, answer));
  });
};

const calculatePercentages = (optionStats, totalResponses) => {
  if (totalResponses > 0) {
    optionStats.forEach(stat => {
      stat.percentage = Math.round((stat.count / totalResponses) * 100 * 10) / 10;
    });
  }
};

router.get('/:postId/:blockId/stats', async (req, res) => {
  try {
    const { postId, blockId } = req.params;

    const validationError = validateStatsParams(postId, blockId);
    if (validationError) {
      return sendError(res, validationError, 400);
    }

    const post = await Post.findById(postId);
    if (!post) {
      return sendError(res, 'Post not found', 404);
    }

    const block = resolveBlock(post, blockId);
    if (!block || (block.type !== 'quiz' && block.type !== 'poll')) {
      return sendError(res, 'Quiz/Poll block not found in post', 404);
    }

    const responses = await QuizResponse.find({ postId, blockId });

    const totalResponses = responses.length;
    const blockData = block.data;
    const options = blockData.options || [];
    const optionStats = buildOptionStats(options);

    countResponses(responses, optionStats);
    calculatePercentages(optionStats, totalResponses);

    sendSuccess(res, {
      totalResponses,
      options: optionStats,
      blockType: block.type,
      question: blockData.question
    }, 'Statistics retrieved successfully');
  } catch (error) {
    console.error('Get quiz statistics error:', error);
    sendError(res, error.message || 'Failed to get statistics', 500);
  }
});