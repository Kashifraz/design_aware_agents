    private CourseContent.FileType determineFileType(String contentType, String filename) {
        if (contentType == null) {
            return CourseContent.FileType.DOC;
        }

        if (contentType.contains("pdf")) {
            return CourseContent.FileType.PDF;
        } else if (contentType.contains("presentation") || contentType.contains("powerpoint") || 
                   (filename != null && filename.toLowerCase().endsWith(".ppt"))) {
            return CourseContent.FileType.PPT;
        } else if (contentType.contains("word") || contentType.contains("document") ||
                   (filename != null && (filename.toLowerCase().endsWith(".doc") || filename.toLowerCase().endsWith(".docx")))) {
            return CourseContent.FileType.DOC;
        } else if (contentType.contains("video")) {
            return CourseContent.FileType.VIDEO;
        }

        return CourseContent.FileType.DOC;
    }