private CourseContent.FileType determineFileType(String contentType, String filename) {
    if (contentType == null) {
        return CourseContent.FileType.DOC;
    }

    if (contentType.contains("pdf")) {
        return CourseContent.FileType.PDF;
    } else if (contentType.contains("presentation") || contentType.contains("powerpoint") ||
               hasPptExtension(filename)) {
        return CourseContent.FileType.PPT;
    } else if (contentType.contains("word") || contentType.contains("document") ||
               hasDocExtension(filename)) {
        return CourseContent.FileType.DOC;
    } else if (contentType.contains("video")) {
        return CourseContent.FileType.VIDEO;
    }

    return CourseContent.FileType.DOC;
}

private boolean hasPptExtension(String filename) {
    return filename != null && filename.toLowerCase().endsWith(".ppt");
}

private boolean hasDocExtension(String filename) {
    return filename != null && (filename.toLowerCase().endsWith(".doc") || filename.toLowerCase().endsWith(".docx"));
}