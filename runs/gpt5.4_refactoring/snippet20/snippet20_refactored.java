public ResultsheetDTO generateResultsheet(Long courseId, Long studentId) {
    Course course = getCourse(courseId);
    User student = getStudent(studentId);
    validateActiveEnrollment(courseId, studentId);

    List<Assessment> assessments = assessmentRepository.findByCourseId(courseId);
    List<Grade> grades = gradeRepository.findByCourseIdAndStudentId(courseId, studentId);

    AssessmentGradesSummary assessmentSummary = buildAssessmentGrades(assessments, grades);
    CourseGrade courseGrade = resolveCourseGrade(courseId, studentId, grades);

    return buildResultsheet(course, student, assessmentSummary, courseGrade, assessments.size());
}

private Course getCourse(Long courseId) {
    return courseRepository.findById(courseId)
            .orElseThrow(() -> new RuntimeException("Course not found with id: " + courseId));
}

private User getStudent(Long studentId) {
    return userRepository.findById(studentId)
            .orElseThrow(() -> new RuntimeException("Student not found with id: " + studentId));
}

private void validateActiveEnrollment(Long courseId, Long studentId) {
    Optional<CourseEnrollment> enrollment = enrollmentRepository.findByCourseIdAndStudentId(courseId, studentId);
    if (enrollment.isEmpty() || enrollment.get().getStatus() != CourseEnrollment.Status.ACTIVE) {
        throw new RuntimeException("Student is not enrolled in this course");
    }
}

private AssessmentGradesSummary buildAssessmentGrades(List<Assessment> assessments, List<Grade> grades) {
    List<ResultsheetDTO.AssessmentGradeDTO> assessmentGrades = new ArrayList<>();
    BigDecimal totalWeight = BigDecimal.ZERO;
    int gradedCount = 0;

    for (Assessment assessment : assessments) {
        ResultsheetDTO.AssessmentGradeDTO assessmentGrade = buildAssessmentGrade(assessment, grades);
        assessmentGrades.add(assessmentGrade);
        totalWeight = totalWeight.add(assessment.getWeightPercentage());

        if (hasGradeForAssessment(assessmentGrade)) {
            gradedCount++;
        }
    }

    return new AssessmentGradesSummary(assessmentGrades, totalWeight, gradedCount);
}

private ResultsheetDTO.AssessmentGradeDTO buildAssessmentGrade(Assessment assessment, List<Grade> grades) {
    ResultsheetDTO.AssessmentGradeDTO assessmentGrade = new ResultsheetDTO.AssessmentGradeDTO();
    assessmentGrade.setAssessmentId(assessment.getId());
    assessmentGrade.setAssessmentTitle(assessment.getTitle());
    assessmentGrade.setAssessmentType(assessment.getAssessmentType().name());
    assessmentGrade.setMaximumMarks(assessment.getMaximumMarks());
    assessmentGrade.setWeightPercentage(assessment.getWeightPercentage());

    Optional<Grade> grade = findGradeForAssessment(grades, assessment.getId());
    if (grade.isPresent()) {
        populateGradedAssessment(assessmentGrade, assessment, grade.get());
    } else {
        populateUngradedAssessment(assessmentGrade);
    }

    return assessmentGrade;
}

private Optional<Grade> findGradeForAssessment(List<Grade> grades, Long assessmentId) {
    return grades.stream()
            .filter(g -> g.getAssessment().getId().equals(assessmentId))
            .findFirst();
}

private void populateGradedAssessment(ResultsheetDTO.AssessmentGradeDTO assessmentGrade, Assessment assessment, Grade grade) {
    assessmentGrade.setMarksObtained(grade.getMarksObtained());
    assessmentGrade.setFeedback(grade.getFeedback());
    assessmentGrade.setGradedAt(grade.getGradedAt());

    BigDecimal percentage = calculatePercentageScore(grade.getMarksObtained(), assessment.getMaximumMarks());
    assessmentGrade.setPercentageScore(percentage);

    BigDecimal weightedScore = calculateWeightedScore(percentage, assessment.getWeightPercentage());
    assessmentGrade.setWeightedScore(weightedScore);
}

private void populateUngradedAssessment(ResultsheetDTO.AssessmentGradeDTO assessmentGrade) {
    assessmentGrade.setMarksObtained(BigDecimal.ZERO);
    assessmentGrade.setPercentageScore(BigDecimal.ZERO);
    assessmentGrade.setWeightedScore(BigDecimal.ZERO);
}

private BigDecimal calculatePercentageScore(BigDecimal marksObtained, BigDecimal maximumMarks) {
    return marksObtained
            .divide(maximumMarks, 4, RoundingMode.HALF_UP)
            .multiply(BigDecimal.valueOf(100));
}

private BigDecimal calculateWeightedScore(BigDecimal percentage, BigDecimal weightPercentage) {
    BigDecimal weight = weightPercentage.divide(BigDecimal.valueOf(100), 4, RoundingMode.HALF_UP);
    return percentage.multiply(weight);
}

private boolean hasGradeForAssessment(ResultsheetDTO.AssessmentGradeDTO assessmentGrade) {
    return assessmentGrade.getGradedAt() != null;
}

private CourseGrade resolveCourseGrade(Long courseId, Long studentId, List<Grade> grades) {
    Optional<CourseGrade> existingCourseGrade = courseGradeRepository.findByCourseIdAndStudentId(courseId, studentId);

    if (existingCourseGrade.isPresent()) {
        return existingCourseGrade.get();
    }

    if (!grades.isEmpty()) {
        gradeService.calculateCourseGrade(courseId, studentId);
        return courseGradeRepository.findByCourseIdAndStudentId(courseId, studentId)
                .orElseThrow(() -> new RuntimeException("Failed to calculate course grade"));
    }

    throw new RuntimeException("No grades found for this course and student");
}

private ResultsheetDTO buildResultsheet(
        Course course,
        User student,
        AssessmentGradesSummary assessmentSummary,
        CourseGrade courseGrade,
        int totalAssessments
) {
    ResultsheetDTO resultsheet = new ResultsheetDTO();
    resultsheet.setStudentId(student.getId());
    resultsheet.setStudentName(student.getFirstName() + " " + student.getLastName());
    resultsheet.setStudentEmail(student.getEmail());
    resultsheet.setCourseId(course.getId());
    resultsheet.setCourseCode(course.getCode());
    resultsheet.setCourseName(course.getName());
    resultsheet.setMajorName(course.getMajor().getName());
    resultsheet.setCreditHours(course.getCreditHours());
    resultsheet.setAssessmentGrades(assessmentSummary.getAssessmentGrades());
    resultsheet.setOverallGrade(courseGrade.getOverallGrade());
    resultsheet.setGradeLetter(courseGrade.getGradeLetter());
    resultsheet.setLastCalculatedAt(courseGrade.getLastCalculatedAt());
    resultsheet.setTotalWeight(assessmentSummary.getTotalWeight());
    resultsheet.setTotalAssessments(totalAssessments);
    resultsheet.setGradedAssessments(assessmentSummary.getGradedCount());
    return resultsheet;
}

private static class AssessmentGradesSummary {
    private final List<ResultsheetDTO.AssessmentGradeDTO> assessmentGrades;
    private final BigDecimal totalWeight;
    private final int gradedCount;

    private AssessmentGradesSummary(
            List<ResultsheetDTO.AssessmentGradeDTO> assessmentGrades,
            BigDecimal totalWeight,
            int gradedCount
    ) {
        this.assessmentGrades = assessmentGrades;
        this.totalWeight = totalWeight;
        this.gradedCount = gradedCount;
    }

    public List<ResultsheetDTO.AssessmentGradeDTO> getAssessmentGrades() {
        return assessmentGrades;
    }

    public BigDecimal getTotalWeight() {
        return totalWeight;
    }

    public int getGradedCount() {
        return gradedCount;
    }
}