public ProfessorDashboardDTO getProfessorDashboard(Long professorId) {
    ProfessorDashboardDTO dashboard = new ProfessorDashboardDTO();

    List<Course> assignedCourses = courseRepository.findByProfessorId(professorId);
    List<Assessment> allAssessments = assessmentRepository.findByProfessorId(professorId);
    List<Submission> professorSubmissions = getProfessorSubmissions(professorId);

    populateAssignedCourses(dashboard, assignedCourses);
    populateUpcomingDeadlines(dashboard, allAssessments);
    populatePendingGradings(dashboard, professorSubmissions);
    populateTodaysClasses(dashboard, professorId);
    populateRecentSubmissions(dashboard, professorSubmissions);
    populateStatistics(dashboard, allAssessments, professorSubmissions);

    return dashboard;
}

private void populateAssignedCourses(ProfessorDashboardDTO dashboard, List<Course> assignedCourses) {
    dashboard.setAssignedCourses(assignedCourses.stream()
            .map(this::convertCourseToDTO)
            .collect(Collectors.toList()));
    dashboard.setTotalAssignedCourses((long) assignedCourses.size());
}

private void populateUpcomingDeadlines(ProfessorDashboardDTO dashboard, List<Assessment> allAssessments) {
    LocalDateTime now = LocalDateTime.now();
    LocalDateTime sevenDaysLater = now.plusDays(7);

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
}

private void populatePendingGradings(ProfessorDashboardDTO dashboard, List<Submission> professorSubmissions) {
    List<Submission> pendingSubmissions = professorSubmissions.stream()
            .filter(s -> s.getStatus() == Submission.Status.SUBMITTED
                    && !gradeRepository.findBySubmissionId(s.getId()).isPresent())
            .collect(Collectors.toList());

    dashboard.setPendingGradingCount((long) pendingSubmissions.size());
    dashboard.setPendingGradings(pendingSubmissions.stream()
            .limit(10)
            .map(this::convertSubmissionToDTO)
            .collect(Collectors.toList()));
}

private void populateTodaysClasses(ProfessorDashboardDTO dashboard, Long professorId) {
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
}

private void populateRecentSubmissions(ProfessorDashboardDTO dashboard, List<Submission> professorSubmissions) {
    List<Submission> recentSubmissions = professorSubmissions.stream()
            .sorted((s1, s2) -> s2.getSubmissionDate().compareTo(s1.getSubmissionDate()))
            .limit(10)
            .collect(Collectors.toList());

    dashboard.setRecentSubmissions(recentSubmissions.stream()
            .map(this::convertSubmissionToDTO)
            .collect(Collectors.toList()));
}

private void populateStatistics(ProfessorDashboardDTO dashboard, List<Assessment> allAssessments, List<Submission> professorSubmissions) {
    dashboard.setTotalAssessments((long) allAssessments.size());
    dashboard.setTotalSubmissions((long) professorSubmissions.size());

    long gradedSubmissions = professorSubmissions.stream()
            .filter(s -> gradeRepository.findBySubmissionId(s.getId()).isPresent())
            .count();

    dashboard.setGradedSubmissions(gradedSubmissions);
}

private List<Submission> getProfessorSubmissions(Long professorId) {
    return submissionRepository.findAll().stream()
            .filter(s -> isProfessorSubmission(s, professorId))
            .collect(Collectors.toList());
}

private boolean isProfessorSubmission(Submission submission, Long professorId) {
    Assessment assessment = submission.getAssessment();
    return assessment != null
            && assessment.getProfessor() != null
            && assessment.getProfessor().getId().equals(professorId);
}

private CourseDTO convertCourseToDTO(Course course) {
    CourseDTO dto = new CourseDTO();
    dto.setId(course.getId());
    dto.setCode(course.getCode());
    dto.setName(course.getName());
    dto.setDescription(course.getDescription());
    dto.setMajorId(course.getMajor().getId());
    dto.setMajorName(course.getMajor().getName());
    dto.setProfessorId(course.getProfessor() != null ? course.getProfessor().getId() : null);
    dto.setProfessorName(course.getProfessor() != null
            ? course.getProfessor().getFirstName() + " " + course.getProfessor().getLastName() : null);
    dto.setStartDate(course.getStartDate());
    dto.setEndDate(course.getEndDate());
    dto.setCreditHours(course.getCreditHours());
    dto.setStatus(course.getStatus());
    dto.setCreatedAt(course.getCreatedAt());
    dto.setUpdatedAt(course.getUpdatedAt());
    return dto;
}