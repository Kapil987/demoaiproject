#!/bin/bash

echo "Starting environment setup..."
# sudo apt update && sudo apt upgrade -y
# Array of packages to check and install
# Each element is a comma-separated string: "command_to_check,package_name_to_install,check_method"
# check_method: "dpkg" for checking via dpkg -s, empty for checking command availability
PACKAGES_TO_INSTALL=(
    "curl,curl,"
    "wget,wget,"
    "python3-venv,python3-venv,dpkg"
    "pip3,python3-pip,"
    "nginx,nginx"
)

# Function to check and install a package
# Arguments:
#   $1: The command to check for (e.g., "curl", "pip3")
#   $2: The package name to install (e.g., "curl", "python3-venv")
#   $3: (Optional) "dpkg" if it's a Debian package name to check with dpkg -s
install_package() {
    local cmd_to_check="$1"
    local pkg_to_install="$2"
    local check_method="$3"

    echo "Checking for $pkg_to_install..."

    if [ "$check_method" == "dpkg" ]; then
        if ! dpkg -s "$pkg_to_install" &> /dev/null; then
            echo "$pkg_to_install not found. Installing $pkg_to_install..."
            sudo apt install -y "$pkg_to_install"
            if [ $? -ne 0 ]; then
                echo "Error installing $pkg_to_install. Exiting."
                exit 1
            fi
        else
            echo "$pkg_to_install is already installed."
        fi
    else # Default to checking command availability
        if ! command -v "$cmd_to_check" &> /dev/null; then
            echo "$cmd_to_check (from $pkg_to_install) not found. Installing $pkg_to_install..."
            sudo apt install -y "$pkg_to_install"
            if [ $? -ne 0 ]; then
                echo "Error installing $pkg_to_install. Exiting."
                exit 1
            fi
        else
            echo "$cmd_to_check (from $pkg_to_install) is already installed."
        fi
    fi
    echo "$pkg_to_install check complete."
}


if [ $? -ne 0 ]; then
    echo "Error during apt update/upgrade. Please check your internet connection or permissions."
    exit 1
fi
echo "Apt update and upgrade complete."

# 2. Install specified packages from the array
echo "Installing required packages..."
for package_info in "${PACKAGES_TO_INSTALL[@]}"; do
    IFS=',' read -r cmd_to_check pkg_to_install check_method <<< "$package_info"
    install_package "$cmd_to_check" "$pkg_to_install" "$check_method"
done

echo "Environment setup complete. You can now create Python virtual environments."