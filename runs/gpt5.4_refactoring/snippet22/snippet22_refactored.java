private CourseContent.FileType determineFileType(String contentType, String filename) {
    if (contentType == null) {
        return CourseContent.FileType.DOC;
    }

    if (isPdf(contentType)) {
        return CourseContent.FileType.PDF;
    } else if (isPresentation(contentType, filename)) {
        return CourseContent.FileType.PPT;
    } else if (isDocument(contentType, filename)) {
        return CourseContent.FileType.DOC;
    } else if (isVideo(contentType)) {
        return CourseContent.FileType.VIDEO;
    }

    return CourseContent.FileType.DOC;
}

private boolean isPdf(String contentType) {
    return contentType.contains("pdf");
}

private boolean isPresentation(String contentType, String filename) {
    return contentType.contains("presentation")
            || contentType.contains("powerpoint")
            || hasPptExtension(filename);
}

private boolean isDocument(String contentType, String filename) {
    return contentType.contains("word")
            || contentType.contains("document")
            || hasDocExtension(filename);
}

private boolean isVideo(String contentType) {
    return contentType.contains("video");
}

private boolean hasPptExtension(String filename) {
    return filename != null && filename.toLowerCase().endsWith(".ppt");
}

private boolean hasDocExtension(String filename) {
    return filename != null
            && (filename.toLowerCase().endsWith(".doc")
            || filename.toLowerCase().endsWith(".docx"));
}