public ProfessorDashboardDTO getProfessorDashboard(Long professorId) {
    ProfessorDashboardDTO dashboard = new ProfessorDashboardDTO();

    List<Course> assignedCourses = courseRepository.findByProfessorId(professorId);
    dashboard.setAssignedCourses(mapCoursesToDTOs(assignedCourses));
    dashboard.setTotalAssignedCourses((long) assignedCourses.size());

    List<Assessment> allAssessments = assessmentRepository.findByProfessorId(professorId);
    dashboard.setUpcomingDeadlines(getUpcomingDeadlines(allAssessments));

    List<Submission> allSubmissions = submissionRepository.findAll();
    List<Submission> professorSubmissions = filterSubmissionsByProfessor(allSubmissions, professorId);

    List<Submission> pendingGradingSubmissions = professorSubmissions.stream()
            .filter(s -> s.getStatus() == Submission.Status.SUBMITTED
                    && !gradeRepository.findBySubmissionId(s.getId()).isPresent())
            .collect(Collectors.toList());
    dashboard.setPendingGradingCount((long) pendingGradingSubmissions.size());
    dashboard.setPendingGradings(pendingGradingSubmissions.stream()
            .limit(10)
            .map(this::convertSubmissionToDTO)
            .collect(Collectors.toList()));

    dashboard.setTodaysClasses(getTodaysClasses(professorId));
    dashboard.setRecentSubmissions(getRecentSubmissions(professorSubmissions));

    dashboard.setTotalAssessments((long) allAssessments.size());
    dashboard.setTotalSubmissions((long) professorSubmissions.size());
    dashboard.setGradedSubmissions(getGradedSubmissionsCount(professorSubmissions));

    return dashboard;
}

private List<CourseDTO> mapCoursesToDTOs(List<Course> assignedCourses) {
    return assignedCourses.stream()
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
            .collect(Collectors.toList());
}

private List<AssessmentDTO> getUpcomingDeadlines(List<Assessment> allAssessments) {
    LocalDateTime now = LocalDateTime.now();
    LocalDateTime sevenDaysLater = now.plusDays(7);

    return allAssessments.stream()
            .filter(a -> a.getDeadline() != null
                    && a.getDeadline().isAfter(now)
                    && a.getDeadline().isBefore(sevenDaysLater)
                    && a.getStatus() == Assessment.Status.PUBLISHED)
            .sorted((a1, a2) -> a1.getDeadline().compareTo(a2.getDeadline()))
            .limit(10)
            .map(this::convertAssessmentToDTO)
            .collect(Collectors.toList());
}

private List<Submission> filterSubmissionsByProfessor(List<Submission> submissions, Long professorId) {
    return submissions.stream()
            .filter(s -> {
                Assessment assessment = s.getAssessment();
                return assessment != null
                        && assessment.getProfessor() != null
                        && assessment.getProfessor().getId().equals(professorId);
            })
            .collect(Collectors.toList());
}

private List<TimetableEntryDTO> getTodaysClasses(Long professorId) {
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

    return todaysEntries.stream()
            .map(this::convertTimetableEntryToDTO)
            .collect(Collectors.toList());
}

private List<SubmissionDTO> getRecentSubmissions(List<Submission> professorSubmissions) {
    return professorSubmissions.stream()
            .sorted((s1, s2) -> s2.getSubmissionDate().compareTo(s1.getSubmissionDate()))
            .limit(10)
            .map(this::convertSubmissionToDTO)
            .collect(Collectors.toList());
}

private long getGradedSubmissionsCount(List<Submission> professorSubmissions) {
    return professorSubmissions.stream()
            .filter(s -> gradeRepository.findBySubmissionId(s.getId()).isPresent())
            .count();
}