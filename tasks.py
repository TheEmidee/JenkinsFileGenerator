import re
import sys
from pathlib import Path
from typing import Optional

from invoke import Context, Result, task


def run_command(c: Context, cmd: str, check: bool = True, hide: bool = False) -> Result:
    """Run a shell command and return the result."""
    result: Result = c.run(cmd, warn=True, hide=hide)
    if check and result.exited != 0:
        print(f"Error running command: {cmd}")
        if result.stderr:
            print(result.stderr)
        sys.exit(1)
    return result


def check_git_status(c: Context) -> None:
    """Check if we're on develop branch with clean working tree."""
    # Check current branch
    result = run_command(c, "git branch --show-current", hide=True)
    branch = result.stdout.strip() if result.stdout else ""

    if branch != "develop":
        print(f"Error: You must be on the 'develop' branch (currently on '{branch}')")
        sys.exit(1)

    # Check for uncommitted changes
    result = run_command(c, "git status --porcelain", hide=True)
    status = result.stdout.strip() if result.stdout else ""

    if status:
        print("Error: You have uncommitted changes:")
        print(status)
        sys.exit(1)

    print("✓ On develop branch with clean working tree")


def parse_version(version_str: str) -> tuple[int, int, int]:
    """
    Parse a version string into a tuple of integers.

    Args:
        version_str: Version string (e.g., 'v1.2.3' or '1.2.3')

    Returns:
        Tuple of (major, minor, patch)
    """
    # Remove 'v' prefix if present
    clean_version = version_str.lstrip("v")

    pattern = r"^(\d+)\.(\d+)\.(\d+)$"
    match = re.match(pattern, clean_version)

    if not match:
        raise ValueError(f"Invalid version format: {version_str}")

    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def get_last_version_from_changelog(changelog_path: Path = Path("CHANGELOG.md")) -> Optional[tuple[int, int, int]]:
    """
    Extract the last version from CHANGELOG.md.

    Args:
        changelog_path: Path to the CHANGELOG file

    Returns:
        Tuple of (major, minor, patch) or None if no version found
    """
    if not changelog_path.exists():
        print(f"Warning: {changelog_path} not found")
        return None

    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for version patterns like ## v1.2.3, ## 1.2.3, # v1.2.3, etc.
    # This regex looks for markdown headers followed by version numbers
    pattern = r"^##?\s*\[v?(\d+\.\d+\.\d+)\]"

    matches = re.findall(pattern, content, re.MULTILINE)

    if not matches:
        print("Warning: No version found in CHANGELOG")
        return None

    # Return the first (most recent) version found
    try:
        return parse_version(matches[0])
    except ValueError:
        return None


def is_version_increment(new_version: tuple[int, int, int], old_version: tuple[int, int, int]) -> bool:
    """
    Check if new_version is a valid increment of old_version.

    A valid increment means:
    - Major version increased by 1 (and minor/patch reset to 0), OR
    - Major same, minor increased by 1 (and patch reset to 0), OR
    - Major and minor same, patch increased by 1

    Args:
        new_version: New version tuple (major, minor, patch)
        old_version: Old version tuple (major, minor, patch)

    Returns:
        True if new_version is a valid increment
    """
    new_major, new_minor, new_patch = new_version
    old_major, old_minor, old_patch = old_version

    # Major version bump
    if new_major == old_major + 1 and new_minor == 0 and new_patch == 0:
        return True

    # Minor version bump
    if new_major == old_major and new_minor == old_minor + 1 and new_patch == 0:
        return True

    # Patch version bump
    if new_major == old_major and new_minor == old_minor and new_patch == old_patch + 1:
        return True

    return False


def validate_version(version: str, changelog_path: Path = Path("CHANGELOG.md")) -> str:
    """
    Validate version number format and check it's an increment from CHANGELOG.

    Args:
        version: Version string (must start with 'v', e.g., 'v1.2.3')
        changelog_path: Path to the CHANGELOG file

    Returns:
        The validated version string with 'v' prefix
    """
    # Check if version starts with 'v'
    if not version.startswith("v"):
        print(f"Error: Version must start with 'v' (got '{version}')")
        sys.exit(1)

    # Parse and validate format
    try:
        new_version = parse_version(version)
    except ValueError as e:
        print(f"Error: {e}. Expected format: vX.Y.Z")
        sys.exit(1)

    # Get last version from CHANGELOG
    last_version = get_last_version_from_changelog(changelog_path)

    if last_version is None:
        print(f"Warning: Could not find last version in {changelog_path}")
        confirm = input(f"Continue with version {version} anyway? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("Version validation cancelled.")
            sys.exit(1)
        return version

    # Check if it's a valid increment
    if not is_version_increment(new_version, last_version):
        last_version_str = f"v{last_version[0]}.{last_version[1]}.{last_version[2]}"
        print(f"Error: Version {version} is not a valid increment from {last_version_str}")
        print("\nValid next versions would be:")
        print(f"  - v{last_version[0] + 1}.0.0 (major bump)")
        print(f"  - v{last_version[0]}.{last_version[1] + 1}.0 (minor bump)")
        print(f"  - v{last_version[0]}.{last_version[1]}.{last_version[2] + 1} (patch bump)")
        sys.exit(1)

    last_version_str = f"v{last_version[0]}.{last_version[1]}.{last_version[2]}"
    print(f"✓ Version {version} is a valid increment from {last_version_str}")

    return version


@task
def create_release(c: Context, version: Optional[str] = None) -> None:
    """
    Create a new release.

    This will:
    1. Check you're on develop branch with no uncommitted changes
    2. Ask for a version number (must start with 'v')
    3. Validate version is an increment from last CHANGELOG version
    4. Run towncrier to build changelog
    5. Commit all changes
    6. Create a git tag
    7. Push everything to the repository

    Args:
        c: Invoke context
        version: Version number (e.g., v1.2.3). If not provided, will prompt.
    """
    print("=== Release Creation Tool ===\n")

    # Check git status
    check_git_status(c)

    # Get version number
    if version is None:
        last_version = get_last_version_from_changelog()
        if last_version:
            last_version_str = f"v{last_version[0]}.{last_version[1]}.{last_version[2]}"
            print(f"Last version in CHANGELOG: {last_version_str}")
            print("Suggested next versions:")
            print(f"  - v{last_version[0] + 1}.0.0 (major bump)")
            print(f"  - v{last_version[0]}.{last_version[1] + 1}.0 (minor bump)")
            print(f"  - v{last_version[0]}.{last_version[1]}.{last_version[2] + 1} (patch bump)")
        version = input("\nEnter version number (e.g., v1.2.3): ").strip()

    # Validate version
    version = validate_version(version)

    # Confirm
    confirm = input(f"\nCreate release {version}? (yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("Release cancelled.")
        return

    print(f"\n=== Creating release {version} ===\n")

    # Run towncrier (without 'v' prefix for towncrier)
    version_for_towncrier = version.lstrip("v")
    print("Running towncrier...")
    run_command(c, f"towncrier build --yes --version {version_for_towncrier}")

    # Commit changes
    print("\nCommitting changes...")
    run_command(c, "git add .")
    run_command(c, f'git commit -m "Release {version}"')

    confirm = input(f"\nCreate tag {version} and push? (yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("Release cancelled.")
        return

    # Create tag
    print(f"\nCreating tag {version}...")
    run_command(c, f'git tag -a {version} -m "Release {version}"')

    # Push everything
    print("\nPushing to repository...")
    run_command(c, "git push origin develop")
    run_command(c, f"git push origin {version}")

    print(f"\n✓ Release {version} created successfully!")


@task
def check_release(c: Context) -> None:
    """
    Check if the repository is ready for a release (dry run).

    Args:
        c: Invoke context
    """
    print("=== Release Readiness Check ===\n")
    check_git_status(c)

    last_version = get_last_version_from_changelog()
    if last_version:
        last_version_str = f"v{last_version[0]}.{last_version[1]}.{last_version[2]}"
        print(f"\nLast version in CHANGELOG: {last_version_str}")
        print("Suggested next versions:")
        print(f"  - v{last_version[0] + 1}.0.0 (major bump)")
        print(f"  - v{last_version[0]}.{last_version[1] + 1}.0 (minor bump)")
        print(f"  - v{last_version[0]}.{last_version[1]}.{last_version[2] + 1} (patch bump)")

    print("\n✓ Repository is ready for a release!")
