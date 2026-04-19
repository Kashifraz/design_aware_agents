const buildJobFilter = (query) => {
  const {
    search,
    category,
    location,
    employmentType,
    experienceLevel,
    isRemote,
    minSalary,
    maxSalary,
    currency = 'USD'
  } = query;

  const filter = { status: 'active' };

  if (search) {
    filter.$text = { $search: search };
  }

  if (category) {
    filter.category = category;
  }

  if (location) {
    filter.location = { $regex: location, $options: 'i' };
  }

  if (employmentType) {
    filter.employmentType = employmentType;
  }

  if (experienceLevel) {
    filter.experienceLevel = experienceLevel;
  }

  if (isRemote !== undefined) {
    filter.isRemote = isRemote === 'true';
  }

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

  return filter;
};

const buildJobSort = (query) => {
  const {
    sortBy = 'postedAt',
    sortOrder = 'desc'
  } = query;

  const sort = {};

  if (sortBy === 'salary') {
    sort['salaryRange.min'] = sortOrder === 'asc' ? 1 : -1;
  } else {
    sort[sortBy] = sortOrder === 'asc' ? 1 : -1;
  }

  return sort;
};

const buildPagination = (query) => {
  const page = parseInt(query.page || 1);
  const limit = parseInt(query.limit || 10);
  const skip = (page - 1) * limit;

  return { page, limit, skip };
};

const buildPaginationResponse = (page, limit, totalJobs) => {
  const totalPages = Math.ceil(totalJobs / limit);

  return {
    currentPage: page,
    totalPages,
    totalJobs,
    hasNextPage: page < totalPages,
    hasPrevPage: page > 1
  };
};

const getJobs = async (req, res) => {
  try {
    const filter = buildJobFilter(req.query);
    const sort = buildJobSort(req.query);
    const { page, limit, skip } = buildPagination(req.query);

    const jobs = await JobPosting.find(filter)
      .populate('category', 'name description')
      .populate('employer', 'email profile.firstName profile.lastName profile.organization verificationBadge')
      .sort(sort)
      .skip(skip)
      .limit(limit)
      .lean();

    const totalJobs = await JobPosting.countDocuments(filter);
    const pagination = buildPaginationResponse(page, limit, totalJobs);

    res.json({
      success: true,
      data: {
        jobs,
        pagination
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