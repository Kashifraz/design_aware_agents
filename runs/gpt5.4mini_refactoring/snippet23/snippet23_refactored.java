public ProfileResponse uploadProfilePhoto(Long userId, MultipartFile file) {
    validateProfilePhoto(file);

    User user = userRepository.findById(userId)
            .orElseThrow(() -> new RuntimeException("User not found"));

    Profile profile = profileRepository.findByUser(user)
            .orElseThrow(() -> new RuntimeException("Profile not found"));

    try {
        Path uploadPath = getOrCreateUploadPath();
        deleteOldProfilePhotoIfPresent(profile, uploadPath);

        String filename = generateFilename(file.getOriginalFilename());
        Path filePath = uploadPath.resolve(filename);

        Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);

        profile.setProfilePhotoUrl(filename);
        Profile updatedProfile = profileRepository.save(profile);

        return mapToResponse(updatedProfile);
    } catch (IOException e) {
        throw new RuntimeException("Failed to upload profile photo: " + e.getMessage());
    }
}

private void validateProfilePhoto(MultipartFile file) {
    if (file.isEmpty()) {
        throw new RuntimeException("File is empty");
    }

    String contentType = file.getContentType();
    if (contentType == null || (!contentType.startsWith("image/jpeg") && !contentType.startsWith("image/png"))) {
        throw new RuntimeException("Only JPEG and PNG images are allowed");
    }

    if (file.getSize() > 10 * 1024 * 1024) {
        throw new RuntimeException("File size must not exceed 10MB");
    }
}

private Path getOrCreateUploadPath() throws IOException {
    Path uploadPath = Paths.get(UPLOAD_DIR);
    if (!Files.exists(uploadPath)) {
        Files.createDirectories(uploadPath);
    }
    return uploadPath;
}

private void deleteOldProfilePhotoIfPresent(Profile profile, Path uploadPath) {
    String profilePhotoUrl = profile.getProfilePhotoUrl();
    if (profilePhotoUrl == null || profilePhotoUrl.isEmpty()) {
        return;
    }

    try {
        String oldFilename = extractFilename(profilePhotoUrl);
        Path oldPhotoPath = uploadPath.resolve(oldFilename);
        if (Files.exists(oldPhotoPath)) {
            Files.delete(oldPhotoPath);
        }
    } catch (Exception e) {
        System.err.println("Error deleting old profile photo: " + e.getMessage());
    }
}

private String extractFilename(String pathOrFilename) {
    String filename = pathOrFilename;
    if (filename.contains("/")) {
        filename = filename.substring(filename.lastIndexOf("/") + 1);
    }
    return filename;
}

private String generateFilename(String originalFilename) {
    String extension = "";
    if (originalFilename != null && originalFilename.contains(".")) {
        extension = originalFilename.substring(originalFilename.lastIndexOf("."));
    }
    return UUID.randomUUID().toString() + extension;
}