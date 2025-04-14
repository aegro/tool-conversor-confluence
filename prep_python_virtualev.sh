#!/bin/bash
# This script automates the process of managing a Python virtual environment:
# 1. Checks if a virtual environment exists.
# 2. If --delete-env is passed, removes and recreates the environment using Python 3.12.
# 3. Checks if the environment is active; if not, activates it.
# 4. Removes any aliases for 'pip3' and 'python3' within the active environment.
# 5. Installs dependencies from 'requirements.txt'.

# --- Configuration ---
# The name of the virtual environment. You can change this if needed.
VENV_NAME="venv"
# The requirements file.
REQUIREMENTS_FILE="requirements.txt"
# The specific Python executable to use for the virtual environment
PYTHON_EXECUTABLE="/opt/homebrew/bin/python3.11" # Using Python 3.11 for better package compatibility

# --- Script Variables ---
DELETE_ENV=false # Flag to indicate if --delete-env was passed

# --- Functions ---

# Function to display a message to the user.
# First argument is the message, second (optional) is the message type:
# "" (empty) for normal, "error" for error, "warning" for warning.
message() {
  local msg="$1"
  local type="$2"

  case "$type" in
    "error")
      echo "Error: $msg" >&2 # Redirect to stderr
      ;;
    "warning")
      echo "Warning: $msg" >&2 # Redirect to stderr
      ;;
    *)
      echo "$msg"
      ;;
  esac
}

# Function to check if a command is available.
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to remove the virtual environment.
remove_venv() {
  if [ -d "$VENV_NAME" ]; then
    message "Removing existing virtual environment: $VENV_NAME"
    rm -rf "$VENV_NAME" || {
      message "Failed to remove virtual environment." "error"
      exit 1
    }
  else
    message "No existing virtual environment found to remove." "warning"
  fi
}

# Function to create the virtual environment using the specified Python executable.
create_venv() {
  # Check if the specified Python executable exists
  if ! command_exists "$PYTHON_EXECUTABLE"; then
    message "Python executable '$PYTHON_EXECUTABLE' not found. Please ensure it is installed and in your PATH." "error"
    exit 1
  fi

  # Check if the venv directory already exists before creating
  if [ -d "$VENV_NAME" ]; then
      message "Virtual environment '$VENV_NAME' already exists." "warning"
      return 0 # Indicate success as it already exists
  fi

  message "Creating virtual environment: $VENV_NAME (using $PYTHON_EXECUTABLE)"
  # Use the specified Python executable to create the venv
  "$PYTHON_EXECUTABLE" -m venv "$VENV_NAME" || {
    message "Failed to create virtual environment using $PYTHON_EXECUTABLE." "error"
    exit 1
  }
}

# Function to check if the virtual environment is active.
is_venv_active() {
  # Check if VIRTUAL_ENV is set and points to our venv directory
  if [[ -n "$VIRTUAL_ENV" && "$VIRTUAL_ENV" == "$(pwd)/$VENV_NAME" ]]; then
    return 0 # Active
  else
    return 1 # Not active
  fi
}

# Function to activate the virtual environment.
# This function needs to be sourced in the main script logic,
# as 'source' affects the current shell, not a subshell created by a function call.
# We'll call 'source' directly in the main part.

# Function to unalias pip3 and python3.
unalias_pip_python() {
  # Check if the commands are aliased, and if so, unalias them.
  # This should run *after* the venv is activated to affect the venv's context if needed.
  # Note: Inside the venv, 'pip3' and 'python3' usually point to 'pip' and 'python' respectively.
  # We check for aliases specifically for 'pip3' and 'python3' as requested.
  if command -v alias >/dev/null && [[ -n $(alias pip3 2>/dev/null) ]]; then
    message "Removing alias for pip3."
    unalias pip3
  else
    message "'pip3' is not aliased or 'alias' command not found."
  fi

  if command -v alias >/dev/null && [[ -n $(alias python3 2>/dev/null) ]]; then
    message "Removing alias for python3."
    unalias python3
  else
    message "'python3' is not aliased or 'alias' command not found."
  fi
}

# Function to install dependencies from requirements.txt.
install_dependencies() {
  if ! is_venv_active; then
      message "Virtual environment is not active. Cannot install dependencies." "error"
      # Attempt to activate it here just in case, although the main logic should handle it
      if [ -f "$VENV_NAME/bin/activate" ]; then
          source "$VENV_NAME/bin/activate"
          if ! is_venv_active; then
              message "Failed to activate virtual environment before installing dependencies." "error"
              exit 1
          fi
          message "Activated environment to install dependencies."
      else
          exit 1 # Exit if activation fails
      fi
  fi

  # Upgrade pip and install setuptools first to ensure compatibility
  message "Upgrading pip and installing setuptools"
  # Use 'python -m pip' which is the recommended way inside a venv
  python -m pip install --upgrade pip setuptools wheel || {
    message "Failed to upgrade pip or install setuptools." "error"
    # Don't exit here, maybe requirements can still install
  }

  if [ -f "$REQUIREMENTS_FILE" ]; then
    message "Installing dependencies from $REQUIREMENTS_FILE"
    # Use 'python -m pip' from the activated venv
    python -m pip install -r "$REQUIREMENTS_FILE" || {
      message "Failed to install dependencies from $REQUIREMENTS_FILE." "error"
      exit 1
    }
    message "Dependencies installed successfully."
  else
    message "No requirements file found at '$REQUIREMENTS_FILE'. Skipping dependency installation." "warning"
  fi
}

# --- Argument Parsing ---
# Simple loop to check for --delete-env
for arg in "$@"; do
  if [[ "$arg" == "--delete-env" ]]; then
    DELETE_ENV=true
    break # Found the flag, no need to check further
  fi
done

# --- Main Script Logic ---

# 1. Handle deletion if requested
if [ "$DELETE_ENV" = true ]; then
  message "--delete-env flag detected. Removing and recreating environment with $PYTHON_EXECUTABLE."
  remove_venv
  create_venv # Create it fresh using the specified python
else
  message "Checking for existing virtual environment '$VENV_NAME'."
  # If not deleting, ensure it exists, create if not
  if [ ! -d "$VENV_NAME" ]; then
      message "Virtual environment '$VENV_NAME' not found. Creating it with $PYTHON_EXECUTABLE."
      create_venv
  else
      # Optional: Check if existing venv was created with the desired python version?
      # This is complex, usually recreating with --delete-env is easier if version mismatch is suspected.
      message "Virtual environment '$VENV_NAME' already exists."
  fi
fi

# 2. Check activation and activate if necessary
if is_venv_active; then
  message "Virtual environment '$VENV_NAME' is already active."
else
  message "Virtual environment '$VENV_NAME' is not active. Activating..."
  if [ -f "$VENV_NAME/bin/activate" ]; then
    source "$VENV_NAME/bin/activate" || {
      message "Failed to activate virtual environment." "error"
      exit 1
    }
    message "Virtual environment activated."
  else
    # If activation script doesn't exist, but venv dir does, maybe creation failed partially?
    if [ -d "$VENV_NAME" ]; then
        message "Virtual environment directory '$VENV_NAME' exists, but activation script is missing." "error"
        message "Consider running with --delete-env to recreate it." "error"
    else
        message "Virtual environment does not exist and could not be activated." "error"
    fi
    exit 1
  fi
fi

# 3. Unalias pip3 and python3 (now that venv is active)
unalias_pip_python

# 4. Install dependencies
install_dependencies

# 5. Display completion message
message "Virtual environment setup complete using $PYTHON_EXECUTABLE."

# Note: The activation done via 'source' only persists for the duration of this script's execution
# and any processes it launches. It won't make the venv active in the parent shell that called the script.
# To make it active in the parent shell, the *user* must run: source ./your_script_name.sh
# Or, alternatively: source venv/bin/activate after the script runs.
