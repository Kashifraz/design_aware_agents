 public ProfessorDashboardDTO getProfessorDashboard(Long professorId) {
        ProfessorDashboardDTO dashboard = new ProfessorDashboardDTO();

        // Assigned courses
        List<Course> assignedCourses = courseRepository.findByProfessorId(professorId);
        dashboard.setAssignedCourses(assignedCourses.stream()
                .map(course -> {
                    CourseDTO dto = new CourseDTO();
                    dto.setId(course.getId());
                    dto.setCode(course.getCode());
                    dto.setName(course.getName());
                    dto.setDescription(course.getDescription());
                    dto.setMajorId(course.getMajor().getId());
                    dto.setMajorName(course.getMajor().getName());
                    dto.setProfessorId(course.getProfessor() != null ? course.getProfessor().getId() : null);
                    dto.setProfessorName(course.getProfessor() != null ? 
                            course.getProfessor().getFirstName() + " " + course.getProfessor().getLastName() : null);
                    dto.setStartDate(course.getStartDate());
                    dto.setEndDate(course.getEndDate());
                    dto.setCreditHours(course.getCreditHours());
                    dto.setStatus(course.getStatus());
                    dto.setCreatedAt(course.getCreatedAt());
                    dto.setUpdatedAt(course.getUpdatedAt());
                    return dto;
                })
                .collect(Collectors.toList()));
        dashboard.setTotalAssignedCourses((long) assignedCourses.size());

        // Upcoming deadlines (next 7 days)
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime sevenDaysLater = now.plusDays(7);
        List<Assessment> allAssessments = assessmentRepository.findByProfessorId(professorId);
        List<AssessmentDTO> upcomingDeadlines = allAssessments.stream()
                .filter(a -> a.getDeadline() != null 
                        && a.getDeadline().isAfter(now) 
                        && a.getDeadline().isBefore(sevenDaysLater)
                        && a.getStatus() == Assessment.Status.PUBLISHED)
                .sorted((a1, a2) -> a1.getDeadline().compareTo(a2.getDeadline()))
                .limit(10)
                .map(this::convertAssessmentToDTO)
                .collect(Collectors.toList());
        dashboard.setUpcomingDeadlines(upcomingDeadlines);

        // Pending grading tasks
        List<Submission> allSubmissions = submissionRepository.findAll().stream()
                .filter(s -> {
                    Assessment assessment = s.getAssessment();
                    return assessment != null 
                            && assessment.getProfessor() != null
                            && assessment.getProfessor().getId().equals(professorId)
                            && s.getStatus() == Submission.Status.SUBMITTED
                            && !gradeRepository.findBySubmissionId(s.getId()).isPresent();
                })
                .collect(Collectors.toList());
        dashboard.setPendingGradingCount((long) allSubmissions.size());
        dashboard.setPendingGradings(allSubmissions.stream()
                .limit(10)
                .map(this::convertSubmissionToDTO)
                .collect(Collectors.toList()));

        // Today's classes
        LocalDate today = LocalDate.now();
        String dayOfWeek = today.getDayOfWeek().name();
        List<TimetableEntry> todaysEntries = timetableRepository.findAll().stream()
                .filter(entry -> {
                    Course course = entry.getCourse();
                    return course != null 
                            && course.getProfessor() != null
                            && course.getProfessor().getId().equals(professorId)
                            && entry.getDayOfWeek().name().equals(dayOfWeek);
                })
                .sorted((e1, e2) -> e1.getStartTime().compareTo(e2.getStartTime()))
                .collect(Collectors.toList());
        dashboard.setTodaysClasses(todaysEntries.stream()
                .map(this::convertTimetableEntryToDTO)
                .collect(Collectors.toList()));

        // Recent submissions (last 10)
        List<Submission> recentSubmissions = submissionRepository.findAll().stream()
                .filter(s -> {
                    Assessment assessment = s.getAssessment();
                    return assessment != null 
                            && assessment.getProfessor() != null
                            && assessment.getProfessor().getId().equals(professorId);
                })
                .sorted((s1, s2) -> s2.getSubmissionDate().compareTo(s1.getSubmissionDate()))
                .limit(10)
                .collect(Collectors.toList());
        dashboard.setRecentSubmissions(recentSubmissions.stream()
                .map(this::convertSubmissionToDTO)
                .collect(Collectors.toList()));

        // Statistics
        dashboard.setTotalAssessments((long) allAssessments.size());
        long totalSubmissions = submissionRepository.findAll().stream()
                .filter(s -> {
                    Assessment assessment = s.getAssessment();
                    return assessment != null 
                            && assessment.getProfessor() != null
                            && assessment.getProfessor().getId().equals(professorId);
                })
                .count();
        dashboard.setTotalSubmissions(totalSubmissions);
        long gradedSubmissions = submissionRepository.findAll().stream()
                .filter(s -> {
                    Assessment assessment = s.getAssessment();
                    return assessment != null 
                            && assessment.getProfessor() != null
                            && assessment.getProfessor().getId().equals(professorId)
                            && gradeRepository.findBySubmissionId(s.getId()).isPresent();
                })
                .count();
        dashboard.setGradedSubmissions(gradedSubmissions);

        return dashboard;
    }