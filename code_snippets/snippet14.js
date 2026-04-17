router.get('/:postId/:blockId/stats', async (req, res) => {
    try {
      const { postId, blockId } = req.params;
  
      // Validate postId
      if (!postId || !postId.match(/^[0-9a-fA-F]{24}$/)) {
        return sendError(res, 'Invalid post ID', 400);
      }
  
      // Validate blockId
      if (!blockId || typeof blockId !== 'string' || blockId.trim().length === 0) {
        return sendError(res, 'Invalid block ID', 400);
      }
  
      // Check if post exists
      const post = await Post.findById(postId);
      if (!post) {
        return sendError(res, 'Post not found', 404);
      }
  
      // Find the quiz/poll block in the post content
      // Block ID can be the index (as string) or a unique identifier
      let block = null;
      if (/^\d+$/.test(blockId)) {
        // If blockId is a number (as string), use it as array index
        const index = parseInt(blockId);
        if (index >= 0 && index < post.content.length) {
          block = post.content[index];
        }
      } else {
        // Otherwise, search for block by type
        block = post.content.find(b => (b.type === 'quiz' || b.type === 'poll'));
      }
  
      if (!block || (block.type !== 'quiz' && block.type !== 'poll')) {
        return sendError(res, 'Quiz/Poll block not found in post', 404);
      }
  
      // Get all responses for this block
      const responses = await QuizResponse.find({ postId, blockId });
  
      // Calculate statistics
      const totalResponses = responses.length;
      const blockData = block.data;
      const options = blockData.options || [];
  
      // Initialize option counts
      const optionStats = options.map((opt, index) => ({
        index,
        value: opt.value !== undefined ? opt.value : index,
        text: opt.text,
        count: 0,
        percentage: 0
      }));
  
      // Count responses
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
  
      // Calculate percentages
      if (totalResponses > 0) {
        optionStats.forEach(stat => {
          stat.percentage = Math.round((stat.count / totalResponses) * 100 * 10) / 10; // Round to 1 decimal
        });
      }
  
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