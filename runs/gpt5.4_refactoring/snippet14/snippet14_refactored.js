const isValidPostId = (postId) => {
  return !!postId && !!postId.match(/^[0-9a-fA-F]{24}$/);
};

const isValidBlockId = (blockId) => {
  return !!blockId && typeof blockId === 'string' && blockId.trim().length !== 0;
};

const findQuizOrPollBlock = (post, blockId) => {
  let block = null;

  if (/^\d+$/.test(blockId)) {
    const index = parseInt(blockId);
    if (index >= 0 && index < post.content.length) {
      block = post.content[index];
    }
  } else {
    block = post.content.find(b => (b.type === 'quiz' || b.type === 'poll'));
  }

  if (!block || (block.type !== 'quiz' && block.type !== 'poll')) {
    return null;
  }

  return block;
};

const createOptionStats = (options) => {
  return options.map((opt, index) => ({
    index,
    value: opt.value !== undefined ? opt.value : index,
    text: opt.text,
    count: 0,
    percentage: 0
  }));
};

const countResponses = (responses, optionStats) => {
  responses.forEach(response => {
    const answers = Array.isArray(response.answers) ? response.answers : [response.answers];

    answers.forEach(answer => {
      const optionIndex = optionStats.findIndex(stat =>
        stat.value === answer ||
        stat.index === answer ||
        String(stat.value) === String(answer) ||
        String(stat.index) === String(answer)
      );

      if (optionIndex !== -1) {
        optionStats[optionIndex].count++;
      }
    });
  });
};

const applyPercentages = (optionStats, totalResponses) => {
  if (totalResponses > 0) {
    optionStats.forEach(stat => {
      stat.percentage = Math.round((stat.count / totalResponses) * 100 * 10) / 10;
    });
  }
};

const buildStatistics = (responses, block) => {
  const totalResponses = responses.length;
  const blockData = block.data;
  const options = blockData.options || [];
  const optionStats = createOptionStats(options);

  countResponses(responses, optionStats);
  applyPercentages(optionStats, totalResponses);

  return {
    totalResponses,
    options: optionStats,
    blockType: block.type,
    question: blockData.question
  };
};

router.get('/:postId/:blockId/stats', async (req, res) => {
  try {
    const { postId, blockId } = req.params;

    if (!isValidPostId(postId)) {
      return sendError(res, 'Invalid post ID', 400);
    }

    if (!isValidBlockId(blockId)) {
      return sendError(res, 'Invalid block ID', 400);
    }

    const post = await Post.findById(postId);
    if (!post) {
      return sendError(res, 'Post not found', 404);
    }

    const block = findQuizOrPollBlock(post, blockId);
    if (!block) {
      return sendError(res, 'Quiz/Poll block not found in post', 404);
    }

    const responses = await QuizResponse.find({ postId, blockId });
    const statistics = buildStatistics(responses, block);

    sendSuccess(res, statistics, 'Statistics retrieved successfully');
  } catch (error) {
    console.error('Get quiz statistics error:', error);
    sendError(res, error.message || 'Failed to get statistics', 500);
  }
});