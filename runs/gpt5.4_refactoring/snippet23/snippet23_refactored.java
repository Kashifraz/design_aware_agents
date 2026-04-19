public ProfileResponse uploadProfilePhoto(Long userId, MultipartFile file) {
    validateFile(file);

    User user = getUserOrThrow(userId);
    Profile profile = getProfileOrThrow(user);

    try {
        Path uploadPath = ensureUploadDirectory();
        deleteOldProfilePhotoIfExists(profile, uploadPath);

        String filename = generateUniqueFilename(file);
        Path filePath = uploadPath.resolve(filename);

        Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);

        profile.setProfilePhotoUrl(filename);
        Profile updatedProfile = profileRepository.save(profile);

        return mapToResponse(updatedProfile);
    } catch (IOException e) {
        throw new RuntimeException("Failed to upload profile photo: " + e.getMessage());
    }
}

private void validateFile(MultipartFile file) {
    validateFileIsNotEmpty(file);
    validateFileType(file);
    validateFileSize(file);
}

private void validateFileIsNotEmpty(MultipartFile file) {
    if (file.isEmpty()) {
        throw new RuntimeException("File is empty");
    }
}

private void validateFileType(MultipartFile file) {
    String contentType = file.getContentType();
    if (contentType == null || (!contentType.startsWith("image/jpeg") && !contentType.startsWith("image/png"))) {
        throw new RuntimeException("Only JPEG and PNG images are allowed");
    }
}

private void validateFileSize(MultipartFile file) {
    if (file.getSize() > 10 * 1024 * 1024) {
        throw new RuntimeException("File size must not exceed 10MB");
    }
}

private User getUserOrThrow(Long userId) {
    return userRepository.findById(userId)
            .orElseThrow(() -> new RuntimeException("User not found"));
}

private Profile getProfileOrThrow(User user) {
    return profileRepository.findByUser(user)
            .orElseThrow(() -> new RuntimeException("Profile not found"));
}

private Path ensureUploadDirectory() throws IOException {
    Path uploadPath = Paths.get(UPLOAD_DIR);
    if (!Files.exists(uploadPath)) {
        Files.createDirectories(uploadPath);
    }
    return uploadPath;
}

private void deleteOldProfilePhotoIfExists(Profile profile, Path uploadPath) {
    if (profile.getProfilePhotoUrl() != null && !profile.getProfilePhotoUrl().isEmpty()) {
        try {
            String oldFilename = profile.getProfilePhotoUrl();
            if (oldFilename.contains("/")) {
                oldFilename = oldFilename.substring(oldFilename.lastIndexOf("/") + 1);
            }
            Path oldPhotoPath = uploadPath.resolve(oldFilename);
            if (Files.exists(oldPhotoPath)) {
                Files.delete(oldPhotoPath);
            }
        } catch (Exception e) {
            System.err.println("Error deleting old profile photo: " + e.getMessage());
        }
    }
}

private String generateUniqueFilename(MultipartFile file) {
    String originalFilename = file.getOriginalFilename();
    String extension = "";
    if (originalFilename != null && originalFilename.contains(".")) {
        extension = originalFilename.substring(originalFilename.lastIndexOf("."));
    }
    return UUID.randomUUID().toString() + extension;
}