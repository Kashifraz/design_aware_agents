const apiRequest = async (requestFn, successMessage, transformData) => {
  try {
    const response = await requestFn()

    if (response.data.success) {
      return transformData ? transformData(response.data.data) : response.data.data
    }

    throw new Error(response.data.message || successMessage)
  } catch (error) {
    throw error
  }
}

export const postService = {
  /**
   * Get all posts with optional filters
   * @param {Object} params - Query parameters (status, page, limit, tag, search)
   * @returns {Promise<Object>} Posts data with pagination
   */
  async getPosts(params = {}) {
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
    const url = `/posts${queryString ? `?${queryString}` : ''}`

    return apiRequest(
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
    return apiRequest(
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
    return apiRequest(
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
    return apiRequest(
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
    await apiRequest(
      () => apiClient.delete(`/posts/${postId}`),
      'Failed to delete post'
    )
    return undefined
  },

  /**
   * Publish a post
   * @param {string} postId - Post ID
   * @returns {Promise<Object>} Updated post data
   */
  async publishPost(postId) {
    return apiRequest(
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
    return apiRequest(
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
    return apiRequest(
      () => apiClient.get(`/posts/${postId}/preview`),
      'Failed to fetch post preview',
      (data) => data.post
    )
  }
}