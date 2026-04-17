const getJobs = async (req, res) => {
    try {
      const {
        search,
        category,
        location,
        employmentType,
        experienceLevel,
        isRemote,
        minSalary,
        maxSalary,
        currency = 'USD',
        sortBy = 'postedAt',
        sortOrder = 'desc',
        page = 1,
        limit = 10
      } = req.query;
  
      // Build filter object
      const filter = { status: 'active' };
  
      // Text search
      if (search) {
        filter.$text = { $search: search };
      }
  
      // Category filter
      if (category) {
        filter.category = category;
      }
  
      // Location filter
      if (location) {
        filter.location = { $regex: location, $options: 'i' };
      }
  
      // Employment type filter
      if (employmentType) {
        filter.employmentType = employmentType;
      }
  
      // Experience level filter
      if (experienceLevel) {
        filter.experienceLevel = experienceLevel;
      }
  
      // Remote work filter
      if (isRemote !== undefined) {
        filter.isRemote = isRemote === 'true';
      }
  
      // Salary range filter
      if (minSalary || maxSalary) {
        filter['salaryRange.currency'] = currency;
        if (minSalary && maxSalary) {
          filter.$or = [
            { 'salaryRange.min': { $gte: parseInt(minSalary) } },
            { 'salaryRange.max': { $lte: parseInt(maxSalary) } }
          ];
        } else if (minSalary) {
          filter['salaryRange.min'] = { $gte: parseInt(minSalary) };
        } else if (maxSalary) {
          filter['salaryRange.max'] = { $lte: parseInt(maxSalary) };
        }
      }
  
      // Build sort object
      const sort = {};
      if (sortBy === 'salary') {
        sort['salaryRange.min'] = sortOrder === 'asc' ? 1 : -1;
      } else {
        sort[sortBy] = sortOrder === 'asc' ? 1 : -1;
      }
  
      // Calculate pagination
      const skip = (parseInt(page) - 1) * parseInt(limit);
  
      // Execute query
      const jobs = await JobPosting.find(filter)
        .populate('category', 'name description')
        .populate('employer', 'email profile.firstName profile.lastName profile.organization verificationBadge')
        .sort(sort)
        .skip(skip)
        .limit(parseInt(limit))
        .lean();
  
      // Get total count for pagination
      const totalJobs = await JobPosting.countDocuments(filter);
      const totalPages = Math.ceil(totalJobs / parseInt(limit));
  
      res.json({
        success: true,
        data: {
          jobs,
          pagination: {
            currentPage: parseInt(page),
            totalPages,
            totalJobs,
            hasNextPage: parseInt(page) < totalPages,
            hasPrevPage: parseInt(page) > 1
          }
        }
      });
    } catch (error) {
      console.error('Get jobs error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch jobs',
        error: error.message
      });
    }
  };