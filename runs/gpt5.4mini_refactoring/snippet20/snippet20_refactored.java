public ResultsheetDTO generateResultsheet(Long courseId, Long studentId) {
    Course course = courseRepository.findById(courseId)
            .orElseThrow(() -> new RuntimeException("Course not found with id: " + courseId));

    User student = userRepository.findById(studentId)
            .orElseThrow(() -> new RuntimeException("Student not found with id: " + studentId));

    validateEnrollment(courseId, studentId);

    List<Assessment> assessments = assessmentRepository.findByCourseId(courseId);
    List<Grade> grades = gradeRepository.findByCourseIdAndStudentId(courseId, studentId);

    AssessmentGradeBuildResult assessmentGradeResult = buildAssessmentGrades(assessments, grades);
    CourseGrade courseGrade = resolveCourseGrade(courseId, studentId, grades);

    ResultsheetDTO resultsheet = new ResultsheetDTO();
    resultsheet.setStudentId(student.getId());
    resultsheet.setStudentName(student.getFirstName() + " " + student.getLastName());
    resultsheet.setStudentEmail(student.getEmail());
    resultsheet.setCourseId(course.getId());
    resultsheet.setCourseCode(course.getCode());
    resultsheet.setCourseName(course.getName());
    resultsheet.setMajorName(course.getMajor().getName());
    resultsheet.setCreditHours(course.getCreditHours());
    resultsheet.setAssessmentGrades(assessmentGradeResult.getAssessmentGrades());
    resultsheet.setOverallGrade(courseGrade.getOverallGrade());
    resultsheet.setGradeLetter(courseGrade.getGradeLetter());
    resultsheet.setLastCalculatedAt(courseGrade.getLastCalculatedAt());
    resultsheet.setTotalWeight(assessmentGradeResult.getTotalWeight());
    resultsheet.setTotalAssessments(assessments.size());
    resultsheet.setGradedAssessments(assessmentGradeResult.getGradedCount());

    return resultsheet;
}

private void validateEnrollment(Long courseId, Long studentId) {
    Optional<CourseEnrollment> enrollment = enrollmentRepository.findByCourseIdAndStudentId(courseId, studentId);
    if (enrollment.isEmpty() || enrollment.get().getStatus() != CourseEnrollment.Status.ACTIVE) {
        throw new RuntimeException("Student is not enrolled in this course");
    }
}

private AssessmentGradeBuildResult buildAssessmentGrades(List<Assessment> assessments, List<Grade> grades) {
    List<ResultsheetDTO.AssessmentGradeDTO> assessmentGrades = new ArrayList<>();
    BigDecimal totalWeight = BigDecimal.ZERO;
    int gradedCount = 0;

    for (Assessment assessment : assessments) {
        ResultsheetDTO.AssessmentGradeDTO assessmentGrade = new ResultsheetDTO.AssessmentGradeDTO();
        assessmentGrade.setAssessmentId(assessment.getId());
        assessmentGrade.setAssessmentTitle(assessment.getTitle());
        assessmentGrade.setAssessmentType(assessment.getAssessmentType().name());
        assessmentGrade.setMaximumMarks(assessment.getMaximumMarks());
        assessmentGrade.setWeightPercentage(assessment.getWeightPercentage());
        totalWeight = totalWeight.add(assessment.getWeightPercentage());

        Optional<Grade> grade = grades.stream()
                .filter(g -> g.getAssessment().getId().equals(assessment.getId()))
                .findFirst();

        if (grade.isPresent()) {
            applyGradeDetails(assessmentGrade, assessment, grade.get());
            gradedCount++;
        } else {
            applyEmptyGradeDetails(assessmentGrade);
        }

        assessmentGrades.add(assessmentGrade);
    }

    return new AssessmentGradeBuildResult(assessmentGrades, totalWeight, gradedCount);
}

private void applyGradeDetails(ResultsheetDTO.AssessmentGradeDTO assessmentGrade, Assessment assessment, Grade grade) {
    assessmentGrade.setMarksObtained(grade.getMarksObtained());
    assessmentGrade.setFeedback(grade.getFeedback());
    assessmentGrade.setGradedAt(grade.getGradedAt());

    BigDecimal percentage = grade.getMarksObtained()
            .divide(assessment.getMaximumMarks(), 4, RoundingMode.HALF_UP)
            .multiply(BigDecimal.valueOf(100));
    assessmentGrade.setPercentageScore(percentage);

    BigDecimal weight = assessment.getWeightPercentage()
            .divide(BigDecimal.valueOf(100), 4, RoundingMode.HALF_UP);
    BigDecimal weightedScore = percentage.multiply(weight);
    assessmentGrade.setWeightedScore(weightedScore);
}

private void applyEmptyGradeDetails(ResultsheetDTO.AssessmentGradeDTO assessmentGrade) {
    assessmentGrade.setMarksObtained(BigDecimal.ZERO);
    assessmentGrade.setPercentageScore(BigDecimal.ZERO);
    assessmentGrade.setWeightedScore(BigDecimal.ZERO);
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

private static class AssessmentGradeBuildResult {
    private final List<ResultsheetDTO.AssessmentGradeDTO> assessmentGrades;
    private final BigDecimal totalWeight;
    private final int gradedCount;

    private AssessmentGradeBuildResult(List<ResultsheetDTO.AssessmentGradeDTO> assessmentGrades,
                                       BigDecimal totalWeight,
                                       int gradedCount) {
        this.assessmentGrades = assessmentGrades;
        this.totalWeight = totalWeight;
        this.gradedCount = gradedCount;
    }

    private List<ResultsheetDTO.AssessmentGradeDTO> getAssessmentGrades() {
        return assessmentGrades;
    }

    private BigDecimal getTotalWeight() {
        return totalWeight;
    }

    private int getGradedCount() {
        return gradedCount;
    }
}