    public ProfileResponse uploadProfilePhoto(Long userId, MultipartFile file) {
        // Validate file
        if (file.isEmpty()) {
            throw new RuntimeException("File is empty");
        }

        // Validate file type
        String contentType = file.getContentType();
        if (contentType == null || (!contentType.startsWith("image/jpeg") && !contentType.startsWith("image/png"))) {
            throw new RuntimeException("Only JPEG and PNG images are allowed");
        }

        // Validate file size (10MB max)
        if (file.getSize() > 10 * 1024 * 1024) {
            throw new RuntimeException("File size must not exceed 10MB");
        }

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        Profile profile = profileRepository.findByUser(user)
                .orElseThrow(() -> new RuntimeException("Profile not found"));

        try {
            // Create upload directory if it doesn't exist
            Path uploadPath = Paths.get(UPLOAD_DIR);
            if (!Files.exists(uploadPath)) {
                Files.createDirectories(uploadPath);
            }

            // Delete old profile photo if exists
            if (profile.getProfilePhotoUrl() != null && !profile.getProfilePhotoUrl().isEmpty()) {
                try {
                    // Extract just the filename (in case old records have full path)
                    String oldFilename = profile.getProfilePhotoUrl();
                    if (oldFilename.contains("/")) {
                        oldFilename = oldFilename.substring(oldFilename.lastIndexOf("/") + 1);
                    }
                    Path oldPhotoPath = uploadPath.resolve(oldFilename);
                    if (Files.exists(oldPhotoPath)) {
                        Files.delete(oldPhotoPath);
                    }
                } catch (Exception e) {
                    // Log error but continue with new upload
                    System.err.println("Error deleting old profile photo: " + e.getMessage());
                }
            }

            // Generate unique filename
            String originalFilename = file.getOriginalFilename();
            String extension = "";
            if (originalFilename != null && originalFilename.contains(".")) {
                extension = originalFilename.substring(originalFilename.lastIndexOf("."));
            }
            String filename = UUID.randomUUID().toString() + extension;
            Path filePath = uploadPath.resolve(filename);

            // Save file
            Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);

            // Update profile with new photo URL - store only filename, not full path
            profile.setProfilePhotoUrl(filename);
            Profile updatedProfile = profileRepository.save(profile);

            return mapToResponse(updatedProfile);
        } catch (IOException e) {
            throw new RuntimeException("Failed to upload profile photo: " + e.getMessage());
        }
    }