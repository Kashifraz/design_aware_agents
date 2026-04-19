const buildJobFilter = ({
  search,
  category,
  location,
  employmentType,
  experienceLevel,
  isRemote,
  minSalary,
  maxSalary,
  currency = 'USD'
}) => {
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

const buildJobSort = (sortBy = 'postedAt', sortOrder = 'desc') => {
  const sort = {};

  if (sortBy === 'salary') {
    sort['salaryRange.min'] = sortOrder === 'asc' ? 1 : -1;
  } else {
    sort[sortBy] = sortOrder === 'asc' ? 1 : -1;
  }

  return sort;
};

const getPaginationParams = (page = 1, limit = 10) => {
  const parsedPage = parseInt(page);
  const parsedLimit = parseInt(limit);

  return {
    parsedPage,
    parsedLimit,
    skip: (parsedPage - 1) * parsedLimit
  };
};

const getJobs = async (req, res) => {
  try {
    const {
      sortBy = 'postedAt',
      sortOrder = 'desc',
      page = 1,
      limit = 10
    } = req.query;

    const filter = buildJobFilter(req.query);
    const sort = buildJobSort(sortBy, sortOrder);
    const { parsedPage, parsedLimit, skip } = getPaginationParams(page, limit);

    const jobs = await JobPosting.find(filter)
      .populate('category', 'name description')
      .populate('employer', 'email profile.firstName profile.lastName profile.organization verificationBadge')
      .sort(sort)
      .skip(skip)
      .limit(parsedLimit)
      .lean();

    const totalJobs = await JobPosting.countDocuments(filter);
    const totalPages = Math.ceil(totalJobs / parsedLimit);

    res.json({
      success: true,
      data: {
        jobs,
        pagination: {
          currentPage: parsedPage,
          totalPages,
          totalJobs,
          hasNextPage: parsedPage < totalPages,
          hasPrevPage: parsedPage > 1
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