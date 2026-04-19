const handleResponse = (response, defaultMessage, dataSelector = (data) => data) => {
  if (response.data.success) {
    return dataSelector(response.data.data)
  }

  throw new Error(response.data.message || defaultMessage)
}

const executeRequest = async (requestFn, defaultMessage, dataSelector) => {
  const response = await requestFn()
  return handleResponse(response, defaultMessage, dataSelector)
}

const buildPostsQuery = (params = {}) => {
  const queryParams = new URLSearchParams()

  if (params.status) {
    queryParams.append('status', params.status)
  }
  if (params.page) {
    queryParams.append('page', params.page)
  }
  if (params.limit) {
    queryParams.append('limit', params.limit)
  }
  if (params.tag) {
    queryParams.append('tag', params.tag)
  }
  if (params.search) {
    queryParams.append('search', params.search)
  }

  const queryString = queryParams.toString()
  return `/posts${queryString ? `?${queryString}` : ''}`
}

export const postService = {
  /**
   * Get all posts with optional filters
   * @param {Object} params - Query parameters (status, page, limit, tag, search)
   * @returns {Promise<Object>} Posts data with pagination
   */
  async getPosts(params = {}) {
    const url = buildPostsQuery(params)
    return executeRequest(
      () => apiClient.get(url),
      'Failed to fetch posts'
    )
  },

  /**
   * Get single post by ID
   * @param {string} postId - Post ID
   * @returns {Promise<Object>} Post data
   */
  async getPost(postId) {
    return executeRequest(
      () => apiClient.get(`/posts/${postId}`),
      'Failed to fetch post',
      (data) => data.post
    )
  },

  /**
   * Create new post
   * @param {Object} postData - Post data (title, content, excerpt, status, tags, categoryId, featuredImage)
   * @returns {Promise<Object>} Created post data
   */
  async createPost(postData) {
    return executeRequest(
      () => apiClient.post('/posts', postData),
      'Failed to create post',
      (data) => data.post
    )
  },

  /**
   * Update post
   * @param {string} postId - Post ID
   * @param {Object} postData - Updated post data
   * @returns {Promise<Object>} Updated post data
   */
  async updatePost(postId, postData) {
    return executeRequest(
      () => apiClient.put(`/posts/${postId}`, postData),
      'Failed to update post',
      (data) => data.post
    )
  },

  /**
   * Delete post
   * @param {string} postId - Post ID
   * @returns {Promise<void>}
   */
  async deletePost(postId) {
    return executeRequest(
      () => apiClient.delete(`/posts/${postId}`),
      'Failed to delete post',
      () => undefined
    )
  },

  /**
   * Publish a post
   * @param {string} postId - Post ID
   * @returns {Promise<Object>} Updated post data
   */
  async publishPost(postId) {
    return executeRequest(
      () => apiClient.patch(`/posts/${postId}/publish`),
      'Failed to publish post',
      (data) => data.post
    )
  },

  /**
   * Unpublish a post
   * @param {string} postId - Post ID
   * @returns {Promise<Object>} Updated post data
   */
  async unpublishPost(postId) {
    return executeRequest(
      () => apiClient.patch(`/posts/${postId}/unpublish`),
      'Failed to unpublish post',
      (data) => data.post
    )
  },

  /**
   * Preview a post (for authors, even if draft)
   * @param {string} postId - Post ID
   * @returns {Promise<Object>} Post data
   */
  async previewPost(postId) {
    return executeRequest(
      () => apiClient.get(`/posts/${postId}/preview`),
      'Failed to fetch post preview',
      (data) => data.post
    )
  }
}