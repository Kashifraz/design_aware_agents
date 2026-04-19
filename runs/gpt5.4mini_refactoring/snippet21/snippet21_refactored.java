public ResultsheetDTO generateResultsheet(Long courseId, Long studentId) {
    Course course = getCourse(courseId);
    User student = getStudent(studentId);
    ensureActiveEnrollment(courseId, studentId);

    List<Assessment> assessments = assessmentRepository.findByCourseId(courseId);
    List<Grade> grades = gradeRepository.findByCourseIdAndStudentId(courseId, studentId);

    ResultsheetData resultsheetData = buildAssessmentGrades(assessments, grades);

    CourseGrade courseGrade = resolveCourseGrade(courseId, studentId, grades);

    return buildResultsheet(course, student, resultsheetData, courseGrade);
}

private Course getCourse(Long courseId) {
    return courseRepository.findById(courseId)
            .orElseThrow(() -> new RuntimeException("Course not found with id: " + courseId));
}

private User getStudent(Long studentId) {
    return userRepository.findById(studentId)
            .orElseThrow(() -> new RuntimeException("Student not found with id: " + studentId));
}

private void ensureActiveEnrollment(Long courseId, Long studentId) {
    Optional<CourseEnrollment> enrollment = enrollmentRepository.findByCourseIdAndStudentId(courseId, studentId);
    if (enrollment.isEmpty() || enrollment.get().getStatus() != CourseEnrollment.Status.ACTIVE) {
        throw new RuntimeException("Student is not enrolled in this course");
    }
}

private ResultsheetData buildAssessmentGrades(List<Assessment> assessments, List<Grade> grades) {
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

        Optional<Grade> grade = findGradeForAssessment(grades, assessment.getId());
        if (grade.isPresent()) {
            applyGrade(assessmentGrade, assessment, grade.get());
            gradedCount++;
        } else {
            applyMissingGradeDefaults(assessmentGrade);
        }

        assessmentGrades.add(assessmentGrade);
    }

    return new ResultsheetData(assessmentGrades, totalWeight, gradedCount);
}

private Optional<Grade> findGradeForAssessment(List<Grade> grades, Long assessmentId) {
    return grades.stream()
            .filter(g -> g.getAssessment().getId().equals(assessmentId))
            .findFirst();
}

private void applyGrade(ResultsheetDTO.AssessmentGradeDTO assessmentGrade, Assessment assessment, Grade grade) {
    assessmentGrade.setMarksObtained(grade.getMarksObtained());
    assessmentGrade.setFeedback(grade.getFeedback());
    assessmentGrade.setGradedAt(grade.getGradedAt());

    BigDecimal percentage = grade.getMarksObtained()
            .divide(assessment.getMaximumMarks(), 4, RoundingMode.HALF_UP)
            .multiply(BigDecimal.valueOf(100));
    assessmentGrade.setPercentageScore(percentage);

    BigDecimal weight = assessment.getWeightPercentage()
            .divide(BigDecimal.valueOf(100), 4, RoundingMode.HALF_UP);
    assessmentGrade.setWeightedScore(percentage.multiply(weight));
}

private void applyMissingGradeDefaults(ResultsheetDTO.AssessmentGradeDTO assessmentGrade) {
    assessmentGrade.setMarksObtained(BigDecimal.ZERO);
    assessmentGrade.setPercentageScore(BigDecimal.ZERO);
    assessmentGrade.setWeightedScore(BigDecimal.ZERO);
}

private CourseGrade resolveCourseGrade(Long courseId, Long studentId, List<Grade> grades) {
    Optional<CourseGrade> existingCourseGrade = courseGradeRepository.findByCourseIdAndStudentId(courseId, studentId);

    if (existingCourseGrade.isPresent()) {
        return existingCourseGrade.get();
    }

    if (grades.isEmpty()) {
        throw new RuntimeException("No grades found for this course and student");
    }

    gradeService.calculateCourseGrade(courseId, studentId);

    return courseGradeRepository.findByCourseIdAndStudentId(courseId, studentId)
            .orElseThrow(() -> new RuntimeException("Failed to calculate course grade"));
}

private ResultsheetDTO buildResultsheet(Course course, User student, ResultsheetData resultsheetData, CourseGrade courseGrade) {
    ResultsheetDTO resultsheet = new ResultsheetDTO();
    resultsheet.setStudentId(student.getId());
    resultsheet.setStudentName(student.getFirstName() + " " + student.getLastName());
    resultsheet.setStudentEmail(student.getEmail());
    resultsheet.setCourseId(course.getId());
    resultsheet.setCourseCode(course.getCode());
    resultsheet.setCourseName(course.getName());
    resultsheet.setMajorName(course.getMajor().getName());
    resultsheet.setCreditHours(course.getCreditHours());
    resultsheet.setAssessmentGrades(resultsheetData.assessmentGrades);
    resultsheet.setOverallGrade(courseGrade.getOverallGrade());
    resultsheet.setGradeLetter(courseGrade.getGradeLetter());
    resultsheet.setLastCalculatedAt(courseGrade.getLastCalculatedAt());
    resultsheet.setTotalWeight(resultsheetData.totalWeight);
    resultsheet.setTotalAssessments(resultsheetData.assessmentGrades.size());
    resultsheet.setGradedAssessments(resultsheetData.gradedCount);
    return resultsheet;
}

private static class ResultsheetData {
    private final List<ResultsheetDTO.AssessmentGradeDTO> assessmentGrades;
    private final BigDecimal totalWeight;
    private final int gradedCount;

    private ResultsheetData(List<ResultsheetDTO.AssessmentGradeDTO> assessmentGrades, BigDecimal totalWeight, int gradedCount) {
        this.assessmentGrades = assessmentGrades;
        this.totalWeight = totalWeight;
        this.gradedCount = gradedCount;
    }
}