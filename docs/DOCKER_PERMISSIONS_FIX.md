# Docker Permissions Fix for GitHub Container Registry

## Problem Description

The GitHub Actions workflow was failing with multiple issues:

1. **Permissions Error**: When attempting to push Docker images to the GitHub Container Registry (ghcr.io):
```
failed to push ghcr.io/ebrandler/mcportfolio:nightly: denied: permission_denied: write_package
```

2. **Annotation Index Error**: During Docker image build step:
```
index annotations not supported for single platform export
```

## Root Cause Analysis

The issues were caused by two main problems:

1. **Insufficient Permissions**: The GitHub Actions workflow lacked sufficient permissions for accessing the GitHub Container Registry (ghcr.io). While the workflow had `packages: write` permission, additional permissions were needed for OIDC token generation and provenance attestations.

2. **Incompatible Annotation Configuration**: The workflow was attempting to use index annotations (`annotation-index`) on single-platform builds, which is only supported for multi-platform builds.

## Solution Implemented

### 1. Enhanced Workflow Permissions

Updated `.github/workflows/docker.yml` to include additional required permissions:

```yaml
permissions:
  contents: read
  packages: write
  id-token: write      # Required for OIDC token generation
  attestations: write  # Required for provenance attestations
```

### 2. Improved Docker Login Configuration

Enhanced the Docker login step with:
- Better error handling
- Debug information logging
- Explicit logout configuration

### 3. Enhanced Metadata Extraction

Updated the Docker metadata action to:
- Properly handle nightly builds with `type=schedule,pattern=nightly`
- Add comprehensive image labels
- Improve tag generation logic

### 4. Fixed Annotation Index Issue

Resolved the single-platform annotation problem:
- Made index annotations conditional on multi-platform builds
- Used `annotation-index` only for non-PR contexts (multi-platform)
- Simplified outputs for PR contexts (single-platform)

### 5. Added Debugging and Verification

Added comprehensive debugging steps:
- Environment variable logging
- Build information display
- Post-push verification
- Image manifest inspection

## Repository Settings Requirements

To ensure this fix works properly, verify the following repository settings:

### 1. Actions Permissions

Go to **Settings > Actions > General > Workflow permissions** and ensure:
- ✅ "Read and write permissions" is selected
- ✅ "Allow GitHub Actions to create and approve pull requests" is checked (if needed)

### 2. Package Registry Access

Go to **Settings > Actions > General > Workflow permissions** and verify:
- ✅ The repository has access to write to ghcr.io
- ✅ The GITHUB_TOKEN has sufficient scope

### 3. Container Registry Settings

In your GitHub profile/organization settings:
- ✅ Ensure ghcr.io is enabled
- ✅ Verify package visibility settings
- ✅ Check that the repository has write access to the container registry

## Testing the Fix

### 1. Trigger the Workflow

The workflow can be triggered by:
- Pushing to the `main` branch
- Creating a tag (for versioned releases)
- Scheduled runs (nightly builds)

### 2. Monitor the Build

Check the Actions tab to verify:
- ✅ Debug information is displayed correctly
- ✅ Docker login succeeds
- ✅ Image build completes successfully
- ✅ Image push succeeds
- ✅ Post-push verification passes

### 3. Verify the Image

After successful push, verify the image is available:

```bash
# Pull the image
docker pull ghcr.io/ebrandler/mcportfolio:nightly

# Run the image
docker run -d -p 8001:8001 ghcr.io/ebrandler/mcportfolio:nightly

# Test the health endpoint
curl http://localhost:8001/health
```

## Troubleshooting

### If the issue persists:

1. **Check Repository Settings**: Verify all permissions are correctly configured
2. **Review Token Scope**: Ensure GITHUB_TOKEN has sufficient permissions
3. **Check Organization Policies**: Verify no organization-level restrictions
4. **Review Debug Output**: Check the workflow logs for detailed error information

### Common Issues:

- **Token Scope**: GITHUB_TOKEN might need additional scopes
- **Organization Policies**: Organization might restrict package registry access
- **Repository Visibility**: Private repositories might have different permission requirements
- **Rate Limiting**: GitHub Container Registry might have rate limits

## Additional Security Considerations

The enhanced workflow includes:
- ✅ Proper OIDC token handling
- ✅ Provenance attestations for supply chain security
- ✅ Comprehensive image labeling
- ✅ Multi-platform builds (AMD64 and ARM64)
- ✅ Build cache optimization

## Monitoring and Maintenance

- Monitor workflow runs for any permission-related failures
- Keep Docker actions updated to latest versions
- Review and update permissions as needed
- Monitor GitHub's documentation for any changes to container registry requirements
